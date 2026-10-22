#!/usr/bin/env python3
"""Turn the claude.ai artifact version of 농마니 (app/index.html) into the public web app.

Usage: python3 build_app.py <artifact index.html> <output dir>
Every patch must apply exactly once; the script stops otherwise, so app changes never slip through silently.
"""
import sys, pathlib, shutil

src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
s = src.read_text(encoding="utf-8")
here = pathlib.Path(__file__).parent

def patch(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit(f"patch '{label}': expected 1 match, found {n}")
    s = s.replace(old, new)

HEAD = """<meta name="description" content="농부와 심마니 직거래 장터. 농부가 밭에서 키운 산나물, 심마니가 산에서 캔 약초를 직접 사고팝니다. 귀한 산삼·송이는 경매로.">
<link rel="canonical" href="https://nongmani.com/app/">
<link rel="alternate" hreflang="en" href="https://nongmani.com/app/global.html?lang=en">
<link rel="alternate" hreflang="ja" href="https://nongmani.com/app/global.html?lang=ja">
<link rel="alternate" hreflang="zh-Hans" href="https://nongmani.com/app/global.html?lang=zh-Hans">
<link rel="manifest" href="manifest.webmanifest">
<meta name="theme-color" content="#2B5B41">
<link rel="icon" href="icon.svg">
<link rel="apple-touch-icon" href="icon-192.png">
<meta name="apple-mobile-web-app-title" content="농마니">
<meta property="og:title" content="농부와 심마니 직거래 장터">
<meta property="og:description" content="산에서 캔 약초, 밭에서 키운 산나물을 직접 사고파는 장터">
<meta property="og:image" content="https://nongmani.com/seller/og.png">
"""
patch("</head><body>", HEAD + "</head><body>\n<script src=\"vendor/supabase.js\"></script>\n<script src=\"nm-claude.js\"></script>", "head+scripts")

patch('<div class="logo"><b>', '<div class="logo" translate="no"><b>', "logo no-translate")

# language switch at the top for overseas visitors
patch('<div class="who" id="who"></div>',
      '<a class="nmlang" href="global.html" translate="no" lang="en" aria-label="English, 中文, 日本語">🌐 EN · 中文 · 日本語</a>\n    <div class="who" id="who"></div>', "lang switch")
patch(".who{display:flex;", ".nmlang{border:1px solid var(--line);border-radius:999px;padding:5px 11px;font-size:13px;font-weight:700;color:var(--pine);text-decoration:none;white-space:nowrap;line-height:1.3}.nmlang:hover{border-color:var(--pine)}@media(max-width:480px){.logo small{display:none}.nmlang{padding:4px 9px}}\n.who{display:flex;", "lang css")

patch('    <button data-go="help"><b>고객센터</b>', '    <button id="nmInstMenu" hidden type="button"><b>📲 홈 화면에 추가</b><span>앱처럼 아이콘을 눌러 바로 열기</span></button>\n    <button data-go="help"><b>고객센터</b>', "install menu")

# signed-out visitors can browse; writing opens the sign-in sheet instead of a dead button
patch('function applyWrite(){document.querySelectorAll(".needWrite").forEach(b=>{b.disabled=!S.canWrite||!S.uid;b.title=b.disabled?"로그인과 참여 권한이 필요합니다":""})}',
      'function applyWrite(){document.querySelectorAll(".needWrite").forEach(b=>{b.disabled=!!S.uid&&!S.canWrite;b.title=b.disabled?"이 계정은 이 작업을 할 수 없습니다":""})}',
      "applyWrite")

patch('if(!S.db){toast("저장소에 연결되지 않았습니다. claude.ai에 로그인한 상태로 열어 주세요");return false}',
      'if(!S.db){toast("저장소에 연결되지 않았습니다. 새로고침해 주세요");return false}\n  if(!S.uid){nmAuth.open("로그인하면 바로 이어서 할 수 있어요.");return false}',
      "guard login")
patch("  catch(e){\n    const m={invalid_argument:",
      "  catch(e){\n    if(e?.code===\"login\"){nmAuth.open(\"로그인이 필요합니다.\");return false}\n    const m={invalid_argument:",
      "guard catch")

patch('if(!db||!S.uid){ban.hidden=false;ban.textContent="저장소에 연결되지 않아 둘러보기만 할 수 있습니다. claude.ai에 로그인한 상태로 열면 입찰·주문·출품이 저장됩니다.";render();return}',
      'if(!db){ban.hidden=false;ban.textContent="저장소에 연결하지 못했습니다. 인터넷 연결을 확인하고 새로고침해 주세요.";render();return}\n'
      '  if(!S.uid){ban.hidden=false;ban.innerHTML=\'<button type="button" class="btn sm primary" onclick="nmAuth.open()">로그인</button> 하면 주문·입찰·판매를 할 수 있어요.\';$("#who").innerHTML=\'<button type="button" class="btn sm" onclick="nmAuth.open()">로그인</button>\'}\n'
      '  else $("#who").insertAdjacentHTML("beforeend",\' <button type="button" class="btn sm" onclick="nmAuth.signOut()" aria-label="로그아웃">로그아웃</button>\');',
      "startup")
patch("""if(!S.canWrite){ban.hidden=false;ban.textContent="보기 전용 권한으로 열었습니다. 입찰·주문·출품을 하려면 페이지 소유자에게 '참여자(Contributor)' 이상 권한을 요청하세요."}""",
      """if(S.uid&&!S.canWrite){ban.hidden=false;ban.textContent="이 계정은 지금 거래를 할 수 없습니다. 운영자에게 문의해 주세요."}""",
      "readonly banner")
patch('subMsgs();\n  db.collection("shopmgr")', 'if(S.uid)subMsgs();\n  db.collection("shopmgr")', "messages need sign-in")

# shop-manager invite codes are checked on the server; hashes are no longer readable by everyone
patch("const hh=await mgrHash(raw),shop=Object.keys(S.sellers).find(u=>S.sellers[u].mgrHash===hh);",
      "const hh=await mgrHash(raw),shop=await nmAuth.mgrFind(hh);",
      "manager link")

FOOT = """<footer style="max-width:1100px;margin:32px auto 0;padding:18px 16px 40px;border-top:1px solid var(--line);font-size:13px;color:var(--muted);line-height:1.7">
농마니(농부와 심마니) · ‘농마니’ 상표출원 제40-2026-0219569호 · <a href="https://nongmani.com/nongmani-yakcho/" style="color:var(--pine)">약초 백과</a> · <a href="#" onclick="go('help');scrollTo(0,0);return false" style="color:var(--pine)">고객센터</a> · <a href="https://nongmani.com/seller/" style="color:var(--pine)">판매자 모집</a> · <a href="global.html?lang=en" style="color:var(--pine)" lang="en">English</a> · <a href="global.html?lang=zh-Hans" style="color:var(--pine)" lang="zh-Hans">中文</a> · <a href="global.html?lang=ja" style="color:var(--pine)" lang="ja">日本語</a><br>
시범 운영 중입니다. 사업자 정보는 등록 후 표시됩니다.
</footer>
<div id="nmIntl" hidden style="position:fixed;left:12px;right:12px;bottom:84px;z-index:50;background:var(--ink);color:var(--bg);border-radius:14px;padding:12px 14px;gap:10px;align-items:center;box-shadow:0 6px 24px rgba(0,0,0,.25);font-size:15px" translate="no">
<span style="flex:1" id="nmIntlT"></span><a id="nmIntlA" style="background:var(--gold);color:var(--gold-ink);border-radius:10px;padding:8px 12px;font-weight:700;text-decoration:none;white-space:nowrap"></a><button type="button" id="nmIntlX" aria-label="Close" style="background:none;border:0;color:inherit;font-size:22px;min-width:40px;min-height:40px;cursor:pointer">×</button></div>
<script>(function(){var l=(navigator.language||"ko").toLowerCase();if(/^ko/.test(l))return;try{if(localStorage.getItem("nm_intl_x"))return}catch(e){}
var g=/^zh/.test(l)?"zh-Hans":/^ja/.test(l)?"ja":"en",T={en:["Shopping from abroad? See Nongmani in English.","English"],ja:["日本語で見ますか？","日本語版"],"zh-Hant":["想用中文瀏覽？","中文版"],"zh-Hans":["想用中文浏览？","中文版"]}[g];
var e=document.getElementById("nmIntl");document.getElementById("nmIntlT").textContent=T[0];var a=document.getElementById("nmIntlA");a.textContent=T[1];a.href="global.html?lang="+g;e.hidden=false;e.style.display="flex";
document.getElementById("nmIntlX").onclick=function(){e.hidden=true;e.style.display="none";try{localStorage.setItem("nm_intl_x","1")}catch(x){}}})();</script>
<div id="nmInst" hidden style="position:fixed;left:12px;right:12px;bottom:84px;z-index:49;background:var(--surface);color:var(--ink);border:1px solid var(--pine);border-radius:14px;padding:12px 14px;gap:10px;align-items:center;box-shadow:0 6px 24px rgba(0,0,0,.18);font-size:15px">
<span style="font-size:24px" aria-hidden="true">📲</span><span style="flex:1">농마니를 홈 화면에 추가하면 앱처럼 바로 열 수 있어요</span><button type="button" id="nmInstGo" style="background:var(--pine);color:var(--pine-ink);border:0;border-radius:10px;padding:8px 12px;font:inherit;font-weight:700;white-space:nowrap;cursor:pointer">추가하기</button><button type="button" id="nmInstX" aria-label="닫기" style="background:none;border:0;color:var(--muted);font-size:22px;min-width:40px;min-height:40px;cursor:pointer">×</button></div>
<div id="nmIos" hidden role="dialog" aria-modal="true" aria-labelledby="nmIosH" style="position:fixed;inset:0;z-index:9999;background:rgba(10,20,14,.55);place-items:center;padding:16px"><div style="background:var(--surface);color:var(--ink);border-radius:18px;max-width:380px;width:100%;padding:22px 20px;display:grid;gap:12px;font-size:16px;line-height:1.6"><h2 id="nmIosH" style="margin:0;font-size:22px;color:var(--pine)">홈 화면에 추가하기</h2>
<ol style="margin:0;padding-left:20px;display:grid;gap:8px;font-size:16px"><li>사파리 아래쪽의 <b>공유 버튼</b>(네모에 화살표 ↑)을 누르세요.</li><li>목록을 올려 <b>‘홈 화면에 추가’</b>를 누르세요.</li><li>오른쪽 위 <b>‘추가’</b>를 누르면 끝입니다.</li></ol>
<p style="margin:0;color:var(--muted);font-size:14px">카카오톡 안에서 열었다면 오른쪽 아래 ⋯ 메뉴에서 <b>‘다른 브라우저로 열기’</b>를 먼저 눌러 주세요.</p><button type="button" id="nmIosX" style="min-height:48px;border-radius:12px;border:1px solid var(--line);background:none;font:inherit;cursor:pointer">닫기</button></div></div>
<script>(function(){
  var standalone=matchMedia("(display-mode: standalone)").matches||navigator.standalone===true;if(standalone)return;
  var ua=navigator.userAgent,ios=/iPhone|iPad|iPod/.test(ua)&&!/CriOS|FxiOS/.test(ua),ev=null,bar=document.getElementById("nmInst");
  function get(k){try{return localStorage.getItem(k)}catch(e){return null}}function put(k,v){try{localStorage.setItem(k,v)}catch(e){}}
  var n=(+get("nm_visits")||0)+1;put("nm_visits",n);
  var muted=+get("nm_inst_x")||0,ready=function(){return (ev||ios)&&n>=2&&Date.now()-muted>30*864e5&&document.getElementById("nmIntl").hidden};
  function show(){if(!ready())return;bar.hidden=false;bar.style.display="flex";var m=document.getElementById("nmInstMenu");if(m)m.hidden=false}
  function go(){if(ev){ev.prompt();ev.userChoice.then(function(c){if(c&&c.outcome==="accepted"){bar.hidden=true;bar.style.display="none"}ev=null})}else if(ios){var d=document.getElementById("nmIos");d.hidden=false;d.style.display="grid"}}
  addEventListener("beforeinstallprompt",function(e){e.preventDefault();ev=e;var m=document.getElementById("nmInstMenu");if(m)m.hidden=false;setTimeout(show,4000)});
  addEventListener("appinstalled",function(){bar.hidden=true;bar.style.display="none";put("nm_inst_x",String(Date.now()+3650*864e5))});
  document.getElementById("nmInstGo").onclick=go;
  document.getElementById("nmInstX").onclick=function(){bar.hidden=true;bar.style.display="none";put("nm_inst_x",String(Date.now()))};
  document.getElementById("nmIosX").onclick=function(){var d=document.getElementById("nmIos");d.hidden=true;d.style.display="none"};
  var m=document.getElementById("nmInstMenu");if(m){m.onclick=go;if(ios)m.hidden=false}
  window.nmInstall=go;if(ios)setTimeout(show,4000);
})();</script>
<script>if("serviceWorker" in navigator)addEventListener("load",()=>navigator.serviceWorker.register("sw.js").catch(()=>{}));</script>
</body></html>"""
patch("</body></html>", FOOT, "footer")

out.mkdir(parents=True, exist_ok=True)
(out / "index.html").write_text(s, encoding="utf-8")
for f in ["nm-claude.js", "global.html", "herb-i18n.js", "herb-i18n-ja.js", "manifest.webmanifest", "sw.js", "icon.svg", "icon-192.png", "icon-512.png"]:
    p = here / "app" / f
    if p.exists() and p.resolve() != (out / f).resolve():
        shutil.copy(p, out / f)
(out / "vendor").mkdir(exist_ok=True)
shutil.copy(here / "vendor/package/dist/umd/supabase.js", out / "vendor/supabase.js")
print("built", out / "index.html", len(s))
