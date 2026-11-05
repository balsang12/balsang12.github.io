#!/usr/bin/env python3
"""상품마다 카톡·문자 미리보기용 페이지(p/<상품번호>/)를 만듭니다.
미리보기 로봇은 자바스크립트를 실행하지 않으므로 상품 이름·사진을 정적 HTML에 넣고,
사람은 바로 앱의 상품 화면(/app/?p=번호)으로 넘어갑니다."""
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
    name = (p.get("name") or "농마니 상품")[:60]
    shop = (sellers.get(p.get("sellerId") or "") or {}).get("shopName", "")
    grow = "심마니 채취" if str(p.get("grow", "")).startswith("자연산") else "농부 재배"
    desc = " · ".join(x for x in [f"{won(p.get('price'))} / {p.get('unit','')}", p.get("region", ""), grow, shop] if x)
    e = html.escape
    page = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(name)} · 농마니</title>
<meta name="description" content="{e(desc)}">
<meta property="og:type" content="product"><meta property="og:site_name" content="농마니">
<meta property="og:title" content="{e(name)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{e(img)}"><meta property="og:url" content="{SITE}/p/{pid}/">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{SITE}/app/?p={pid}">
<meta http-equiv="refresh" content="0;url=/app/?p={pid}">
<script>location.replace("/app/?p={pid}")</script>
</head><body><p><a href="/app/?p={pid}">{e(name)} 보러 가기</a></p></body></html>
"""
    write(os.path.join(d, "index.html"), page)
print(f"{len(products)} product pages")
