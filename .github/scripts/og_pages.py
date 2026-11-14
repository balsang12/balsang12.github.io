#!/usr/bin/env python3
"""상품마다 카톡·문자 미리보기용 페이지(p/<상품번호>/)를 만듭니다.
미리보기 로봇은 자바스크립트를 실행하지 않으므로 상품 이름·사진을 정적 HTML에 넣고,
검색 엔진이 읽을 수 있게 상품 내용을 그대로 보여 주고, [주문하기]로 앱 상품 화면(/app/?p=번호)에 연결합니다.
상품 목록은 sitemap-products.xml 로도 만듭니다."""
import base64, html, json, os, re, shutil, sys, urllib.request

SB = "https://vxgydzjyzhjxvqaeludh.supabase.co/rest/v1/docs"
KEY = "sb_publishable_4MyQuV4WbsSnyIdE_s8XIQ_cfRlY6tz"
SITE = "https://nongmani.com"
OUT = sys.argv[1] if len(sys.argv) > 1 else "p"

def get(col, sel="id,data"):
    req = urllib.request.Request(f"{SB}?col=eq.{col}&select={sel}", headers={"apikey": KEY, "Authorization": "Bearer " + KEY})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def won(n):
    try: return f"{int(n):,}원"
    except Exception: return ""

products = {r["id"]: r["data"] for r in get("products") if (r.get("data") or {}).get("status") == "판매중"}
sellers = {r["id"]: r["data"] for r in get("sellers")}
os.makedirs(OUT, exist_ok=True)
for d in os.listdir(OUT):
    if d not in products and os.path.isdir(os.path.join(OUT, d)):
        shutil.rmtree(os.path.join(OUT, d))

def write(path, data, mode="w"):
    old = None
    if os.path.exists(path):
        with open(path, "rb" if "b" in mode else "r") as f: old = f.read()
    if old != data:
        with open(path, mode) as f: f.write(data)

urls = []
for pid, p in products.items():
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", pid): continue
    d = os.path.join(OUT, pid); os.makedirs(d, exist_ok=True)
    img = SITE + "/og.png"
    m = re.match(r"data:image/(jpeg|png);base64,(.+)", p.get("photo") or "", re.S)
    if m:
        ext = "jpg" if m.group(1) == "jpeg" else "png"
        try:
            write(os.path.join(d, "og." + ext), base64.b64decode(m.group(2)), "wb")
            img = f"{SITE}/p/{pid}/og.{ext}"
        except Exception: pass
    name = (p.get("name") or "농마니 상품")[:80]
    shop = (sellers.get(p.get("sellerId") or "") or {}).get("shopName", "")
    maker = p.get("maker") or shop
    grow = "심마니 채취" if str(p.get("grow", "")).startswith("자연산") else "농부 재배"
    price = won(p.get("price")); unit = p.get("unit", "")
    desc = " · ".join(x for x in [f"{price} / {unit}", p.get("region", ""), grow, maker] if x)
    body = p.get("desc") or ""
    e = html.escape
    url = f"{SITE}/p/{pid}/"; app = f"/app/?p={pid}"
    ld = {"@context": "https://schema.org", "@type": "Product", "name": name, "image": [img],
          "description": (body or desc)[:500], "brand": {"@type": "Brand", "name": "농마니"},
          "offers": {"@type": "Offer", "url": url, "priceCurrency": "KRW", "price": int(p.get("price") or 0),
                     "availability": "https://schema.org/InStock" if (p.get("stock") or 0) > 0 else "https://schema.org/OutOfStock"}}
    paras = "".join(f"<p>{e(x)}</p>" for x in body.split("\n") if x.strip())
    page = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(name)} · 농마니</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="product"><meta property="og:site_name" content="농마니">
<meta property="og:title" content="{e(name)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{e(img)}"><meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>:root{{--ink:#1D2B22;--muted:#5B6B60;--pine:#1F5A3C;--gold:#B8862B;--bg:#FBF6EA;--surface:#fff;--line:#E2D9C4}}
@media (prefers-color-scheme:dark){{:root{{--ink:#EDE6D6;--muted:#B3B8AE;--bg:#141A16;--surface:#1D2520;--line:#33403A;--pine:#5FB487}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:"Pretendard",system-ui,-apple-system,"Apple SD Gothic Neo","Noto Sans KR",sans-serif;line-height:1.7}}
main{{max-width:720px;margin:0 auto;padding:16px}}header a{{font-weight:900;font-size:22px;color:var(--pine);text-decoration:none}}header b{{color:var(--gold)}}
.ph{{width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:16px;background:var(--line);display:block}}
h1{{font-size:24px;line-height:1.35;margin:16px 0 6px}}.price{{font-size:26px;font-weight:800}}.price span{{font-size:16px;color:var(--muted);font-weight:400}}
.meta{{color:var(--muted);font-size:15px}}.go{{display:block;text-align:center;margin:18px 0;padding:16px;border-radius:14px;background:var(--pine);color:#fff;font-weight:800;font-size:18px;text-decoration:none}}
.box{{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:6px 18px}}footer{{color:var(--muted);font-size:13px;margin:24px 0 8px}}</style>
</head><body><main>
<header><a href="/app/">농<b>마니</b></a></header>
<img class="ph" src="{e(img)}" alt="{e(name)}">
<h1>{e(name)}</h1>
<div class="price">{e(price)} <span>/ {e(unit)}</span></div>
<div class="meta">{e(" · ".join(x for x in [p.get("region",""), grow, "생산자 " + maker if maker else ""] if x))}</div>
<a class="go" href="{app}">농마니에서 주문하기 →</a>
{f'<div class="box">{paras}</div>' if paras else ""}
<a class="go" href="{app}">사진 더 보기 · 주문하기 →</a>
<footer>농마니 · 농부와 심마니가 판매하는 산야초 · <a href="/">nongmani.com</a></footer>
</main></body></html>
"""
    write(os.path.join(d, "index.html"), page)
    urls.append((url, img))
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' + "".join(f"<url><loc>{u}</loc><image:image><image:loc>{html.escape(i)}</image:loc></image:image></url>\n" for u, i in urls) + "</urlset>\n"
write("sitemap-products.xml", sm)
# 이미 제출된 sitemap.xml 에도 상품 주소를 넣어 두면 따로 제출하지 않아도 됨
if os.path.exists("sitemap.xml"):
    main = open("sitemap.xml", encoding="utf-8").read()
    main = re.sub(r"<url><loc>https://nongmani\.com/p/[^\n]*</url>\n?", "", main)
    add = "".join(f"<url><loc>{u}</loc><image:image><image:loc>{html.escape(i)}</image:loc></image:image></url>\n" for u, i in urls)
    if "xmlns:image" not in main:
        main = main.replace('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"', 1)
    main = main.replace("</urlset>", add + "</urlset>", 1)
    write("sitemap.xml", main)
print(f"{len(products)} product pages")
