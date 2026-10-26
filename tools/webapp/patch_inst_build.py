import pathlib
p=pathlib.Path("web/build_app.py");s=p.read_text(encoding="utf-8")
DLG='''<div id="nmSel" hidden role="dialog" aria-modal="true" aria-labelledby="nmSelH" style="position:fixed;inset:0;z-index:9999;background:rgba(10,20,14,.55);place-items:center;padding:16px"><div style="background:var(--surface);color:var(--ink);border-radius:18px;max-width:400px;width:100%;padding:22px 20px;display:grid;gap:12px;font-size:17px;line-height:1.6"><h2 id="nmSelH" style="margin:0;font-size:22px;color:var(--pine)">📲 홈 화면에 농마니 아이콘 만들기</h2>
<p style="margin:0">아이콘을 만들어 두시면 다음부터 <b>바탕화면의 농마니를 한 번만 누르면</b> 가게가 바로 열립니다. 주문 확인도 빨라집니다.</p>
<div id="nmSelBody" style="display:grid;gap:10px"></div>
<button type="button" id="nmSelX" style="min-height:48px;border-radius:12px;border:1px solid var(--line);background:none;color:var(--ink);font:inherit;cursor:pointer">나중에 할게요</button></div></div>
'''
anchor='<script>(function(){\n  var standalone=matchMedia'
assert s.count(anchor)==1
s=s.replace(anchor,DLG+anchor)
JS='''  var kakao=/KAKAOTALK/i.test(ua),mob=/Android|iPhone|iPad|iPod/i.test(ua);
  function steps(a){return '<ol style="margin:0;padding-left:22px;display:grid;gap:8px">'+a.map(function(t){return "<li>"+t+"</li>"}).join("")+"</ol>"}
  function sellerGuide(){var b=document.getElementById("nmSelBody"),d=document.getElementById("nmSel");
    if(ev&&!kakao)b.innerHTML='<button type="button" id="nmSelGo" style="min-height:52px;border-radius:12px;border:0;background:var(--pine);color:var(--pine-ink);font:inherit;font-weight:700;font-size:18px;cursor:pointer">아이콘 만들기</button><p style="margin:0;color:var(--muted);font-size:15px">누른 뒤 뜨는 창에서 ‘설치’ 또는 ‘추가’를 누르시면 됩니다.</p>';
    else if(kakao)b.innerHTML=steps(["오른쪽 아래(아이폰은 오른쪽 위) <b>⋯ 메뉴</b>를 누르세요.","<b>‘다른 브라우저로 열기’</b>를 누르세요.","열린 화면에서 이 안내가 다시 나오면 따라 하시면 됩니다."]);
    else if(ios)b.innerHTML=steps(["사파리 아래쪽 <b>공유 버튼</b>(네모에 화살표 ↑)을 누르세요.","목록을 올려 <b>‘홈 화면에 추가’</b>를 누르세요.","오른쪽 위 <b>‘추가’</b>를 누르면 끝입니다."]);
    else b.innerHTML=steps(["오른쪽 위(삼성 인터넷은 아래) <b>메뉴(⋮ 또는 ≡)</b>를 누르세요.","<b>‘홈 화면에 추가’</b> 또는 <b>‘앱 설치’</b>를 누르세요.","‘추가’를 누르면 끝입니다."]);
    var g=document.getElementById("nmSelGo");if(g)g.onclick=function(){d.hidden=true;d.style.display="none";go()};
    d.hidden=false;d.style.display="grid"}
  document.getElementById("nmSelX").onclick=function(){var d=document.getElementById("nmSel");d.hidden=true;d.style.display="none"};
  window.nmSellerNew=function(){if(mob)sellerGuide()};
  var si=document.getElementById("sellInst");if(si&&mob){si.innerHTML='<button type="button" id="sellInstB" style="display:flex;gap:10px;align-items:center;width:100%;text-align:left;margin:4px 0 12px;padding:12px 14px;border-radius:14px;border:1px solid var(--pine);background:var(--surface);color:var(--ink);font:inherit;font-size:16px;cursor:pointer"><span style="font-size:24px" aria-hidden="true">📲</span><span style="flex:1"><b>홈 화면에 농마니 아이콘 만들기</b><br><span style="color:var(--muted);font-size:14px">한 번 만들어 두면 누르기만 해도 가게가 열립니다</span></span><span aria-hidden="true">›</span></button>';si.hidden=false;document.getElementById("sellInstB").onclick=sellerGuide}
'''
a2='  window.nmInstall=go;'
assert s.count(a2)==1
s=s.replace(a2,JS+a2)
p.write_text(s,encoding="utf-8");print("ok")
