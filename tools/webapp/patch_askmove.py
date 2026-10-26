import pathlib
p=pathlib.Path("app/index.html");s=p.read_text(encoding="utf-8")
def rep(a,b):
    global s
    assert s.count(a)==1,a[:70];s=s.replace(a,b)
OLD='''  <form class="askbox" id="askBox">
    <label for="askQ"><b>🔍 이름을 모르면 생김새로 찾기</b><br><span class="meta">기억나는 모양, 색, 먹던 방법, 캐는 철을 적어 주세요</span></label>
    <textarea id="askQ" rows="2" maxlength="200" placeholder="예: 잎이 넓고 쌉싸름한 봄 산나물 / 뿌리를 고추장에 무쳐 먹던 하얀 것"></textarea>
    <button class="btn primary" type="submit" id="askGo">물어보기</button>
    <div id="askOut" aria-live="polite"></div>
  </form>
'''
rep(OLD,'')
NEW='''  <details class="askd" id="askWrap"><summary>🔍 이름을 모르면 생김새로 찾기</summary>
  <form class="askbox" id="askBox">
    <label for="askQ" class="meta">기억나는 모양, 색, 먹던 방법, 캐는 철을 적어 주세요</label>
    <div class="askrow"><input id="askQ" maxlength="200" placeholder="예: 잎이 넓고 쌉싸름한 봄 산나물"><button class="btn sm" type="submit" id="askGo">찾기</button></div>
    <div id="askOut" aria-live="polite"></div>
  </form></details>
'''
rep('''  <div class="dtags" id="dictTags"></div>''', NEW+'''  <div class="dtags" id="dictTags"></div>''')
rep('section[data-view="herbs"] .askbox{margin:0 0 16px;scroll-margin-top:96px}',
    'section[data-view="herbs"] .askbox{margin:6px 0 12px;scroll-margin-top:96px}\n.askd{margin:2px 0 8px;scroll-margin-top:96px}.askd>summary{display:inline-block;cursor:pointer;list-style:none;color:var(--pine);font-size:14px;text-decoration:underline;text-underline-offset:3px;padding:4px 0}.askd>summary::-webkit-details-marker{display:none}\n.askrow{display:flex;gap:8px}.askrow input{flex:1;min-width:0;font:inherit;font-size:16px;border:1px solid var(--line);border-radius:10px;padding:8px 10px;background:var(--bg,#fff);color:var(--ink)}')
rep('function askGo(q){go("herbs");const t=$("#askQ");',
    'function askGo(q){go("herbs");$("#askWrap").open=true;const t=$("#askQ");')
p.write_text(s,encoding="utf-8");print("ok")
