BIZ="상호 농마니 · 대표 권영철 · 사업자등록번호 854-67-00792 · 통신판매업 신고 진행 중<br>주소 경북 구미시 형곡동로8길 14, 대경파크빌 802호 · 전화 010-8167-8040 · 이메일 balsang12@naver.com"
def page(slug,title,desc,body):
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title} · 농마니</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://nongmani.com/{slug}/">
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.css">
<link rel="icon" href="/app/icon.svg"><link rel="apple-touch-icon" href="/app/icon-180.png">
<style>
:root{{--bg:#FFFFFF;--surface:#F7FAF6;--ink:#15201A;--muted:#4E5E51;--pine:#16824A;--line:#DDE5DA}}
@media (prefers-color-scheme:dark){{:root{{--bg:#111712;--surface:#19221B;--ink:#E5ECE4;--muted:#A9B8AC;--pine:#7BBA94;--line:#334036;color-scheme:dark}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.75 "Pretendard Variable",Pretendard,"Noto Sans KR","Apple SD Gothic Neo","Malgun Gothic",system-ui,sans-serif;-webkit-text-size-adjust:100%}}
main{{max-width:760px;margin:0 auto;padding:28px max(16px,env(safe-area-inset-left,0px)) 64px}}
nav.top{{font-size:14px;margin-bottom:18px}}nav.top a{{color:var(--pine)}}
h1{{font-size:28px;font-weight:800;letter-spacing:-.04em;line-height:1.3;margin:0 0 6px;color:var(--ink)}}.meta{{color:var(--muted);font-size:14px;margin:0 0 24px}}
h2{{font-size:19px;margin:30px 0 8px;padding-top:12px;border-top:1px solid var(--line)}}h3{{font-size:16px;margin:18px 0 4px}}
p,li{{margin:6px 0}}ol,ul{{padding-left:22px}}
table{{width:100%;border-collapse:collapse;font-size:14.5px;background:var(--surface);margin:8px 0}}th,td{{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}}th{{background:var(--bg);color:var(--muted)}}td:first-child,th{{word-break:keep-all;min-width:64px}}
.tw{{overflow-x:auto}}.box{{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin:10px 0}}
footer{{margin-top:44px;padding-top:16px;border-top:1px solid var(--line);font-size:13px;color:var(--muted)}}footer a{{color:var(--pine)}}
</style></head><body><main>
<nav class="top"><a href="https://nongmani.com/app/">← 농마니 장터</a> · <a href="/terms/">이용약관</a> · <a href="/privacy/">개인정보처리방침</a> · <a href="/refund/">교환·환불 정책</a></nav>
<h1>{title}</h1>
<p class="meta">시행일 2026년 10월 27일</p>
{body}
<footer><a href="/terms/">이용약관</a> · <b><a href="/privacy/">개인정보처리방침</a></b> · <a href="/refund/">교환·환불 정책</a><br>{BIZ}<br>농마니는 통신판매중개자로서 거래 당사자가 아니며, 판매자가 올린 상품 정보와 거래에 대한 책임은 각 판매자에게 있습니다.</footer>
</main></body></html>
'''
