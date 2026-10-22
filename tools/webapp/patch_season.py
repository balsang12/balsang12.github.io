#!/usr/bin/env python3
"""v77: 첫 화면을 약초만이 아닌 약초·산나물·버섯·열매로 — 고정 제목 + 철마다 바뀌는 한 줄."""
import sys, pathlib
p = pathlib.Path(sys.argv[1]); s = p.read_text(encoding="utf-8")
def patch(old, new, label, count=1):
    global s
    n = s.count(old)
    if n != count: sys.exit(f"{label}: expected {count}, found {n}")
    s = s.replace(old, new)

patch('''    <h1>어떤 약초를 <br>찾으세요?</h1>
    <p class="hsub">심마니가 산에서 캔 약초부터 농부가 밭에서 키운 약초까지</p>''',
      '''    <h1>산과 밭에서 온 것, <br>무엇을 찾으세요?</h1>
    <p class="hsub hseason" id="hSeason"></p>''', "h1")
patch('placeholder="약초 이름으로 찾기" aria-label="품목 검색"', 'placeholder="약초·산나물 이름으로 찾기" aria-label="품목 검색"', "ph")
patch('<b>약초 알아보기</b><br><span>약초 300여 가지의 생김새, 옛 문헌 기록, 최근 연구를 약초 사전에서 읽어 보세요</span>',
      '<b>약초·산나물 알아보기</b><br><span>약초·산나물 300여 가지의 생김새, 옛 문헌 기록, 최근 연구를 사전에서 읽어 보세요</span>', "herbcard")
patch('<label for="askQ"><b>어떤 약초인지 기억나는 대로 적어 주세요</b></label>', '<label for="askQ"><b>어떤 약초·나물인지 기억나는 대로 적어 주세요</b></label>', "ask")
patch('<p class="meta">찾는 약초 이름을 알고 계시면 이름으로 검색해 주세요. 예: 도라지, 더덕, 오미자</p>',
      '<p class="meta">찾는 약초·나물 이름을 알고 계시면 이름으로 검색해 주세요. 예: 곰취, 더덕, 오미자</p>', "hint")
patch('<b>약초 알아보기</b><br><span>약초마다 옛 문헌에 어떻게 기록됐는지',
      '<b>약초·산나물 알아보기</b><br><span>품목마다 옛 문헌에 어떻게 기록됐는지', "herbcard2")
patch('<button data-go="herbs"><b>약초 사전</b>', '<button data-go="herbs"><b>약초·산나물 사전</b>', "menu")

FN = r'''
/* ---------- 철마다 바뀌는 첫 화면 한 줄 ---------- */
const SEASONS=[[[3,4,5],"🌱","봄 산나물 철이에요",["곰취","두릅","참나물","취나물"]],[[6,7,8],"☀️","여름 열매·약초 철",["오디","오미자","산딸기","블루베리"]],[[9,10,11],"🍄","가을 버섯·뿌리 철",["송이","능이","더덕","도라지"]],[[12,1,2],"🎁","겨울 약초·선물 철",["산양삼","천마","대추","생강청"]]];
function seasonNow(){const m=new Date(Date.now()+9*3600e3).getUTCMonth()+1;return SEASONS.find(x=>x[0].includes(m))}
function renderSeason(){const el=$("#hSeason");if(!el)return;const z=seasonNow();if(el.dataset.k===z[2])return;el.dataset.k=z[2];
  el.innerHTML=`<span>${z[1]} <b>${z[2]}</b></span> ${z[3].map(n=>`<button type="button" class="sq" data-sq="${n}">${n}</button>`).join("")}`;
  const q=$("#homeQ");if(q&&!q.value)q.placeholder=`${z[3].slice(0,3).join(", ")}…`}
'''
patch('''function renderHome(){''', FN + '''function renderHome(){renderSeason();''', "fn")
patch('''  const gf=e.target.closest("[data-gift]");''',
      '''  const sq=e.target.closest("[data-sq]");if(sq){$("#homeQ").value=sq.dataset.sq;$("#homeSearch").requestSubmit();return}
  const gf=e.target.closest("[data-gift]");''', "click")

CSS = '''.hseason{display:flex;flex-wrap:wrap;align-items:center;gap:6px}.hseason b{color:var(--pine)}
.hseason .sq{border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:999px;padding:3px 10px;font:inherit;font-size:13.5px;cursor:pointer}
.hseason .sq:hover{border-color:var(--pine)}
@media (max-width:700px){.hhead .hsub.hseason{display:flex;font-size:14px;margin:0}.hhead .hseason>span{width:100%}}
'''
patch('.hask{display:flex;', CSS + '.hask{display:flex;', "css")
p.write_text(s, encoding="utf-8"); print("ok")
