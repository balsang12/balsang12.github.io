#!/usr/bin/env python3
"""v89: 대량 주문 — 대량·단체 선물 요청서, 판매자 수량 할인, 계산서 발행 가능 표시."""
import sys, pathlib
p = pathlib.Path(sys.argv[1]); s = p.read_text(encoding="utf-8")
def patch(old, new, label, count=1):
    global s
    n = s.count(old)
    if n != count: sys.exit(f"{label}: expected {count}, found {n}")
    s = s.replace(old, new)

# ---------- 1) 대량·단체 선물 요청서 ----------
patch('''  <div class="sechead"><h2>채취 의뢰 · 견적 받기</h2><span class="meta">몇 가지만 답하면 요청서가 완성됩니다. 견적 발송은 판매자에게도 무료입니다</span></div>''',
      '''  <div class="sechead"><h2>채취 의뢰 · 견적 받기</h2><span class="meta">몇 가지만 답하면 요청서가 완성됩니다. 견적 발송은 판매자에게도 무료입니다</span></div>
  <button type="button" class="bulkcta" data-gift-bulk="1"><span><b>🏢 회사·단체 대량 선물이세요?</b><span>개수, 받는 곳, 예산, 계산서만 알려 주면 판매자들이 무료로 견적을 보내요</span></span><span class="go">대량 요청서 쓰기</span></button>''', "request cta")
import re as _re
_m=_re.search(r'  const gb=e\.target\.closest\("\[data-gift-bulk\]"\);if\(gb\)\{[^\n]*\n',s)
s=s[:_m.start()]+'  const gb=e.target.closest("[data-gift-bulk]");if(gb){openBulk();return}\n'+s[_m.end():]

# 판매자: 받은 의뢰 목록 (대량 표시, 계산서 필요한 건 사업자 판매자에게 먼저)
patch('''  const open=S.requests.filter(r=>r.status==="모집중"&&r.buyerId!==S.uid).sort((a,b)=>b.createdAt-a.createdAt);''',
      '''  const canInv=!!(S.sellers[S.uid]||{}).biz;
  const open=S.requests.filter(r=>r.status==="모집중"&&r.buyerId!==S.uid).sort((a,b)=>(canInv?(!!b.bulk?.invoice-!!a.bulk?.invoice):0)||(!!b.bulk-!!a.bulk)||b.createdAt-a.createdAt);''', "seller req sort")
patch('''<div class="meta">${esc(r.form)} · ${esc(r.grow)} · ${esc(r.region)} · 납기 ${esc(r.due)}</div>${r.memo?`<div class="meta">"${esc(r.memo)}"</div>`:""}''',
      '''<div class="meta">${esc(r.form)} · ${esc(r.grow)} · ${esc(r.region)} · 납기 ${esc(r.due)}</div>${bulkInfo(r,canInv)}${r.memo?`<div class="meta">"${esc(r.memo)}"</div>`:""}''', "seller req bulk info")
# 손님: 내 요청서 · 견적에 계산서 가능 표시
patch('''    <div class="meta num">${esc(r.form)} · ${esc(r.grow)} · ${esc(r.region)} · 납기 ${esc(r.due)} · 견적 ${qs.length}건</div>''',
      '''    <div class="meta num">${esc(r.form)} · ${esc(r.grow)} · ${esc(r.region)} · 납기 ${esc(r.due)} · 견적 ${qs.length}건</div>${bulkInfo(r,true)}''', "buyer req bulk info")
patch('''<span><b style="font-size:15px">${esc(shopName(q.sellerId))}</b> <span class="meta">${esc(S.sellers[q.sellerId]?.region||"")}</span></span>''',
      '''<span><b style="font-size:15px">${esc(shopName(q.sellerId))}</b> <span class="meta">${esc(S.sellers[q.sellerId]?.region||"")}</span>${invChip(q.sellerId)}</span>''', "quote inv chip")

# ---------- 3) 계산서 발행 가능 표시 ----------
patch('''const regChip=uid=>{''', '''const invChip=uid=>(S.sellers[uid]||{}).biz?' <span class="chip">🧾 계산서 발행 가능</span>':"";
const regChip=uid=>{''', "inv chip fn")
patch('''<b>${esc(shopName(uid))}</b>${certChip(uid)}${regChip(uid)}<div class="meta num">''',
      '''<b>${esc(shopName(uid))}</b>${certChip(uid)}${regChip(uid)}${invChip(uid)}<div class="meta num">''', "seller row inv")
patch('''${t.verified?'<span class="chip ok">조합·작목반 확인</span>':""}${regChip(uid)}''',
      '''${t.verified?'<span class="chip ok">조합·작목반 확인</span>':""}${regChip(uid)}${invChip(uid)}''', "profile inv")
patch('''<option value="">아직 없음</option><option>면세사업자</option><option>과세사업자</option></select></div>''',
      '''<option value="">아직 없음</option><option>면세사업자</option><option>과세사업자</option></select><p class="meta" style="margin:4px 0 0">사업자등록이 있으면 <b>🧾 계산서 발행 가능</b> 표시가 붙고, 계산서가 필요한 회사·단체 대량 의뢰를 먼저 받습니다.</p></div>''', "biz hint")

# ---------- 2) 수량 할인 ----------
patch('''        <div class="row2 giftsell">''',
'''        <div class="row2 qdform"><div class="field"><label for="sQd1n">수량 할인 ① (개 이상)</label><div class="qdrow"><input id="sQd1n" type="number" min="2" placeholder="10" class="num"><span>개 이상</span><input id="sQd1p" type="number" min="1" max="50" placeholder="5" class="num"><span>% 할인</span></div></div>
          <div class="field"><label for="sQd2n">수량 할인 ② (선택)</label><div class="qdrow"><input id="sQd2n" type="number" min="2" placeholder="30" class="num"><span>개 이상</span><input id="sQd2p" type="number" min="1" max="50" placeholder="10" class="num"><span>% 할인</span></div></div></div>
        <div class="row2 giftsell">''', "qd form")
patch('''faq:faqRead("sFq"),''', '''faq:faqRead("sFq"),qd:qdRead("sQd"),''', "qd add")
patch('''    <details class="faqform"><summary>🎁 선물세트 ${p.set?''',
'''    <details class="faqform"><summary>📦 수량 할인 ${p.qd?.length?`<span class="chip ok">${esc(qdText(p))}</span>`:'<span class="meta">많이 사면 깎아 주기</span>'}</summary><div class="qdrow">${[0,1].map(i=>`<input id="mq${i+1}n-${p.id}" type="number" min="2" placeholder="${i?30:10}" value="${p.qd?.[i]?.n||""}" class="num" aria-label="개 이상"><span>개 이상</span><input id="mq${i+1}p-${p.id}" type="number" min="1" max="50" placeholder="${i?10:5}" value="${p.qd?.[i]?.pct||""}" class="num" aria-label="% 할인"><span>%</span>`).join("<br>")}</div><div class="actions"><button class="btn sm primary" data-act="qdP" data-id="${p.id}">저장</button></div></details>
    <details class="faqform"><summary>🎁 선물세트 ${p.set?''', "my items qd")
patch('''  async setP(id){''', '''  async qdP(id){await guard(()=>S.db.doc("products/"+id).update({qd:qdRead("mq","-"+id)}),"수량 할인을 저장했습니다")},
  async setP(id){''', "act qd")
# 상품 화면: 할인 표시와 계산
patch('''<dt>배송</dt><dd>${shipSpec(p)}</dd>''', '''<dt>배송</dt><dd>${shipSpec(p)}</dd>${p.qd?.length?`<dt>수량 할인</dt><dd><b>${esc(qdText(p))}</b></dd>`:""}''', "spec qd")
patch('''$("#tot").textContent=won(p.price*qty+ship+wf());''', '''$("#tot").textContent=won(subOf(p,qty)+ship+wf());const qdl=$("#qdLbl");if(qdl){const q=qdPct(p,qty),nx=(p.qd||[]).find(x=>x.n>qty);qdl.innerHTML=q?`<span class="chip ok">${q}% 할인 · -${won(p.price*qty-subOf(p,qty))}</span>`:nx?`${nx.n}개부터 ${nx.pct}% 할인`:"";qdl.hidden=!qdl.innerHTML}''', "upd qd")
patch('''<span class="meta" style="white-space:nowrap" id="shipLbl">''', '''<span class="meta qdlbl" id="qdLbl" hidden></span><span class="meta" style="white-space:nowrap" id="shipLbl">''', "qd label")
patch('''ship,total:p.price*qty+ship+wf(),''', '''ship,total:subOf(p,qty)+ship+wf(),...(qdPct(p,qty)?{qdPct:qdPct(p,qty),qdOff:p.price*qty-subOf(p,qty)}:{}),''', "order qd")
patch('''${p.set?'<span class="chip gold">선물세트</span>':""}''', '''${p.set?'<span class="chip gold">선물세트</span>':""}${p.qd?.length?'<span class="chip">수량 할인</span>':""}''', "card qd chip")
# 판매자 주문: 할인 표시
patch('''    ${giftNote(o)}${shipNoteSeller(o)}''', '''    ${o.qdPct?`<div class="meta">📦 수량 할인 ${o.qdPct}% 적용 (-${won(o.qdOff||0)})</div>`:""}${giftNote(o)}${shipNoteSeller(o)}''', "seller order qd")

FN = r'''
/* ---------- 대량 주문: 수량 할인 · 대량 요청서 ---------- */
function qdRead(pre,suf){suf=suf||"";const out=[];[1,2].forEach(i=>{const n=Math.floor(+($("#"+pre+i+"n"+suf)?.value||0)),pc=Math.floor(+($("#"+pre+i+"p"+suf)?.value||0));if(n>=2&&pc>=1&&pc<=50)out.push({n,pct:pc})});
  return out.sort((a,b)=>a.n-b.n).filter((x,i,a)=>!i||x.n>a[i-1].n&&x.pct>a[i-1].pct)}
const qdText=p=>(p.qd||[]).map(x=>`${x.n}개 이상 ${x.pct}%`).join(" · ")+" 할인";
const qdPct=(p,qty)=>(p.qd||[]).filter(x=>qty>=x.n).reduce((m,x)=>Math.max(m,x.pct),0);
const subOf=(p,qty)=>{const pc=qdPct(p,qty);return pc?Math.round(p.price*qty*(100-pc)/100/10)*10:p.price*qty};
function bulkInfo(r,showInv){const b=r.bulk;if(!b)return "";
  return `<div class="bulkinfo"><span class="chip gold">🏢 대량·단체</span>${b.org?` <b>${esc(b.org)}</b>`:""} · ${b.count}개 · ${b.places==="many"?`받는 곳 여러 군데${b.placeN?` (약 ${b.placeN}곳)`:""}`:"한 곳으로"}${b.budget?` · 1개당 ${won(b.budget)} 안팎`:""}${b.wrap?" · 선물 포장":""}${b.prodCard?" · 생산자 카드":""}${b.invoice?` · <b>계산서 필요</b>${showInv===false?' <span class="chip hot">사업자 판매자만 발행 가능</span>':""}`:""}</div>`}
function openBulk(){const dlg=$("#dlg");openA=null;const tm=new Date(Date.now()+9*3600e3+5*864e5).toISOString().slice(0,10);
  dlg.innerHTML=`<div class="dlg"><button class="close" aria-label="닫기" type="button">×</button><form class="bulkform" id="bulkForm">
   <div class="eyebrow">견적은 무료 · 여러 판매자가 보냅니다</div><h2 style="font-size:22px;margin:2px 0 10px">🏢 대량·단체 선물 요청서</h2>
   <div class="field"><label for="bkItem">어떤 선물인가요?</label><input id="bkItem" required maxlength="60" placeholder="예: 산양삼 선물세트, 더덕·도라지청 세트, 오미자청"></div>
   <div class="row2"><div class="field"><label for="bkCount">몇 개인가요?</label><input id="bkCount" type="number" min="5" required class="num" placeholder="30"></div>
   <div class="field"><label for="bkBudget">1개당 예산 (원, 배송비 포함)</label><input id="bkBudget" type="number" min="5000" step="1000" class="num" placeholder="50000"></div></div>
   <div class="field"><label>어디로 보내나요?</label><div class="bkpl"><label class="ochk"><input type="radio" name="bkPl" value="one" checked> 한 곳으로 모아서</label><label class="ochk"><input type="radio" name="bkPl" value="many"> 받는 분마다 따로</label><input id="bkPlN" type="number" min="2" class="num" placeholder="몇 곳" aria-label="받는 곳 수" style="max-width:90px"></div></div>
   <div class="row2"><div class="field"><label for="bkDue">언제까지 받아야 하나요?</label><input id="bkDue" type="date" min="${tm}" required></div>
   <div class="field"><label for="bkOrg">회사·단체 이름 (선택)</label><input id="bkOrg" maxlength="40" placeholder="예: ○○상사 총무팀"></div></div>
   <label class="ochk"><input type="checkbox" id="bkWrap" checked> 선물 포장</label><label class="ochk"><input type="checkbox" id="bkPc" checked> 생산자 카드 넣기</label><label class="ochk"><input type="checkbox" id="bkInv"> 계산서가 필요해요 (사업자 판매자만 발행할 수 있어요)</label>
   <div class="field"><label for="bkMemo">더 바라는 점 (선택)</label><textarea id="bkMemo" rows="2" maxlength="300" placeholder="예: 로고 스티커를 붙이고 싶어요. 받는 분 명단은 견적이 정해지면 보낼게요"></textarea></div>
   <p class="meta" style="margin:0 0 8px">받는 분 이름·주소는 판매자를 고른 뒤 안전하게 따로 받습니다. 여기엔 전화번호·주소를 적지 마세요.</p>
   <div class="actions"><button class="btn primary needWrite" type="submit">무료로 견적 받기</button></div></form></div>`;
  dlg.querySelector(".close").onclick=()=>dlg.close();
  $("#bulkForm").onsubmit=async e=>{e.preventDefault();if(!S.uid){toast("로그인하면 요청서를 올릴 수 있어요");return}
    const item=$("#bkItem").value.trim(),count=Math.floor(+$("#bkCount").value),memo=$("#bkMemo").value.trim(),org=$("#bkOrg").value.trim();
    if(!item||!(count>=5)){toast("선물 이름과 개수(5개 이상)를 적어 주세요");return}
    if([item,memo,org].some(v=>PII.test(v))){toast("전화번호·계좌·링크는 적을 수 없어요");return}
    const pl=document.querySelector('input[name="bkPl"]:checked').value,bulk={count,places:pl,placeN:pl==="many"?Math.floor(+$("#bkPlN").value)||0:0,budget:Math.floor(+$("#bkBudget").value)||0,wrap:$("#bkWrap").checked,prodCard:$("#bkPc").checked,invoice:$("#bkInv").checked,org:org.slice(0,40)};
    const ok=await guard(()=>S.db.collection("requests").add({item:item.slice(0,60),qty:count,unit:"개",form:"선물용",grow:"상관없음",due:$("#bkDue").value,region:"전국",memo:memo.slice(0,300),bulk,buyerId:S.uid,status:"모집중",createdAt:Date.now()}),"대량 요청서를 올렸습니다. 견적이 오면 채취 의뢰 화면에서 볼 수 있어요");
    if(ok){dlg.close();go("request")}};
  if(!dlg.open)dlg.showModal();dlg.scrollTop=0;applyWrite()}
'''
patch('''function sellerRow(uid,ctx){''', FN + '''function sellerRow(uid,ctx){''', "fn")

CSS = '''.bulkcta{display:flex;align-items:center;gap:12px;width:100%;margin:0 0 14px;padding:12px 16px;border-radius:14px;border:1px solid var(--gold);background:var(--gold-soft);color:var(--ink);font:inherit;text-align:left;cursor:pointer}
.bulkcta>span:first-child{display:flex;flex-direction:column;gap:2px}.bulkcta span span{font-size:13.5px;color:var(--muted)}.bulkcta .go{margin-left:auto;font-weight:700;color:var(--gold-deep);white-space:nowrap}
@media (max-width:700px){.bulkcta .go{display:none}}
.bulkinfo{font-size:13.5px;margin:4px 0}.bkpl{display:flex;flex-wrap:wrap;gap:4px 14px;align-items:center}
.qdrow{display:flex;flex-wrap:wrap;align-items:center;gap:6px}.qdrow input{max-width:80px}.qdrow span{font-size:14px;color:var(--muted)}
.qdlbl{display:block;font-size:12.5px}
'''
patch('.hask{display:flex;', CSS + '.hask{display:flex;', "css")
p.write_text(s, encoding="utf-8"); print("ok")
