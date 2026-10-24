#!/usr/bin/env python3
"""v86: 대화 보조 — 상품 '자주 묻는 질문', 판매자 답변 시간 표시, 빠른 답장 버튼."""
import sys, pathlib
p = pathlib.Path(sys.argv[1]); s = p.read_text(encoding="utf-8")
def patch(old, new, label, count=1):
    global s
    n = s.count(old)
    if n != count: sys.exit(f"{label}: expected {count}, found {n}")
    s = s.replace(old, new)

# ---------- 1) 상품 올리기: 자주 묻는 질문 칸 ----------
patch('''        <div class="row2 giftsell">''',
'''        <details class="faqform"><summary>자주 묻는 질문 미리 답하기 <span class="meta">(채우면 손님 문의가 줄어요)</span></summary>
          <div class="row2"><div class="field"><label for="sFqHarv">언제 캤나요? (채취·수확일)</label><input id="sFqHarv" maxlength="60" placeholder="예: 10월 20일 채취"></div>
          <div class="field"><label for="sFqSize">크기·상태는요?</label><input id="sFqSize" maxlength="60" placeholder="예: 뿌리 길이 15cm 안팎, 10~12뿌리"></div></div>
          <div class="row2"><div class="field"><label for="sFqKeep">어떻게 보관하나요?</label><input id="sFqKeep" maxlength="60" placeholder="예: 신문지에 싸서 냉장 2주"></div>
          <div class="field"><label for="sFqShip">언제 보내 주나요?</label><input id="sFqShip" maxlength="60" placeholder="예: 주문 다음 날 발송, 주말 제외"></div></div></details>
        <div class="row2 giftsell">''', "form faq")
patch('''gift:!!$("#sGift")?.checked,giftWrap:wrapFee($("#sGiftWrap")?.value),''',
      '''gift:!!$("#sGift")?.checked,giftWrap:wrapFee($("#sGiftWrap")?.value),faq:faqRead("sFq"),''', "add faq")

# 내 상품 목록에서 채우기
patch('''    <div class="actions"><span class="meta">🎁 선물 포장 ${p.gift?''',
'''    <details class="faqform"><summary>자주 묻는 질문 ${faqCount(p)?`<span class="chip ok">${faqCount(p)}/4 채움</span>`:'<span class="chip gold">비어 있음 · 채우면 문의가 줄어요</span>'}</summary>${FAQ_Q.map(([k,q,ph])=>`<div class="field"><label for="fq${k}-${p.id}">${q}</label><input id="fq${k}-${p.id}" maxlength="60" placeholder="${ph}" value="${esc((p.faq||{})[k]||"")}"></div>`).join("")}<div class="actions"><button class="btn sm primary" data-act="faqP" data-id="${p.id}">저장</button></div></details>
    <div class="actions"><span class="meta">🎁 선물 포장 ${p.gift?''', "my items faq")
patch('''  async giftP(id){''', '''  async faqP(id){const f={};FAQ_Q.forEach(([k])=>{const v=($("#fq"+k+"-"+id)?.value||"").trim().slice(0,60);if(v)f[k]=v});
    if(Object.values(f).some(v=>PII.test(v))){toast("전화번호·계좌·링크는 넣을 수 없어요");return}
    await guard(()=>S.db.doc("products/"+id).update({faq:f}),"자주 묻는 질문을 저장했습니다. 상품 화면에 보입니다")},
  async giftP(id){''', "act faq")

# 상품 화면에 보이기
patch('''    ${S.owner?`<div class="actions"><button class="btn sm gold" type="button" id="gPick">''',
      '''    ${faqHTML(p)}
    ${S.owner?`<div class="actions"><button class="btn sm gold" type="button" id="gPick">''', "detail faq")

# ---------- 2) 답변 시간 ----------
patch('''<div class="meta num">${r.n?`<span class="star">★</span> ${r.avg.toFixed(1)} (${r.n}) · `:""}완료 거래 ${t.done}건</div></div><button class="btn sm" type="button" data-profile="${esc(uid)}">프로필</button>''',
      '''<div class="meta num">${r.n?`<span class="star">★</span> ${r.avg.toFixed(1)} (${r.n}) · `:""}완료 거래 ${t.done}건</div>${respHTML(uid)}</div><button class="btn sm" type="button" data-profile="${esc(uid)}">프로필</button>''', "seller row resp")
patch('''<div class="pstats num"><div><b>${r.n?r.avg.toFixed(1):"-"}</b><span>평점 (후기 ${r.n})</span></div><div><b>${t.done}</b><span>완료 거래</span></div><div><b>${qn}</b><span>보낸 견적</span></div></div>''',
      '''<div class="pstats num"><div><b>${r.n?r.avg.toFixed(1):"-"}</b><span>평점 (후기 ${r.n})</span></div><div><b>${t.done}</b><span>완료 거래</span></div><div><b>${respShort(uid)}</b><span>보통 답변까지</span></div></div>''', "profile resp")
patch('''<div class="meta">${S.sellers[other]?esc((S.sellers[other].role||"")+" · "+(S.sellers[other].region||"")):"구매자"}</div></div>''',
      '''<div class="meta">${S.sellers[other]?esc((S.sellers[other].role||"")+" · "+(S.sellers[other].region||"")):"구매자"}</div>${S.sellers[other]?respHTML(other):""}</div>''', "chat head resp")
patch('''.sort((a,b)=>(b.t.cert-a.t.cert)||(b.t.done-a.t.done)||(b.r.n-a.r.n)).slice(0,6);''',
      '''.sort((a,b)=>(b.t.cert-a.t.cert)||(respFast(b.id)-respFast(a.id))||(b.t.done-a.t.done)||(b.r.n-a.r.n)).slice(0,6);''', "seller sort")
# 판매자가 답할 때 기록
patch('''    const ok=await guard(()=>S.db.collection("messages").add({members:[S.uid,other].sort(),from:S.uid,to:other,text:text.slice(0,500),...(S.acting?{via:S.realUid}:{}),createdAt:Date.now()}));
    if(ok){ta.value="";ta.focus()}};''',
'''    const ok=await guard(()=>S.db.collection("messages").add({members:[S.uid,other].sort(),from:S.uid,to:other,text:text.slice(0,500),...(S.acting?{via:S.realUid}:{}),createdAt:Date.now()}));
    if(ok){ta.value="";ta.focus();respLog(other)}};
  qrBind();''', "send hook")
patch('''   <form class="compose" id="compose">''', '''   <div class="qr" id="qr">${qrHTML(other)}</div>
   <form class="compose" id="compose">''', "qr slot")

FN = r'''
/* ---------- 대화 보조: 자주 묻는 질문 · 답변 시간 · 빠른 답장 ---------- */
const FAQ_Q=[["harv","언제 캤나요?","예: 10월 20일 채취"],["size","크기·상태는요?","예: 뿌리 길이 15cm 안팎, 10~12뿌리"],["keep","어떻게 보관하나요?","예: 신문지에 싸서 냉장 2주"],["ship","언제 보내 주나요?","예: 주문 다음 날 발송, 주말 제외"]];
function faqRead(pre){const f={},m={harv:"Harv",size:"Size",keep:"Keep",ship:"Ship"};Object.entries(m).forEach(([k,id])=>{const v=($("#"+pre+id)?.value||"").trim().slice(0,60);if(v&&!PII.test(v))f[k]=v});return f}
const faqCount=p=>FAQ_Q.filter(([k])=>(p.faq||{})[k]).length;
function faqHTML(p){const f=p.faq||{},l=FAQ_Q.filter(([k])=>f[k]);if(!l.length)return "";
  return `<div class="faqbox"><b>판매자가 미리 답했어요</b><dl>${l.map(([k,q])=>`<dt>${q}</dt><dd>${esc(f[k])}</dd>`).join("")}</dl></div>`}
/* 판매자 답변 시간: 판매자가 답을 보낼 때, 그 전에 손님이 처음 보낸 메시지부터 걸린 시간(분)을 최근 20개까지 기록 */
function respLog(other){const me=S.sellers[S.uid];if(!me||S.sellers[other])return;
  const l=S.msgs.filter(x=>(x.from===other&&x.to===S.uid)||(x.from===S.uid&&x.to===other)).sort((a,b)=>a.createdAt-b.createdAt);
  let lastMine=0;for(let i=l.length-1;i>=0;i--){if(l[i].from===S.uid&&Date.now()-l[i].createdAt>3000){lastMine=l[i].createdAt;break}}
  const firstQ=l.find(x=>x.from===other&&x.createdAt>lastMine);if(!firstQ)return;
  const mins=Math.max(1,Math.round((Date.now()-firstQ.createdAt)/6e4));if(mins>7*1440)return;
  const resp=[...(me.resp||[]),mins].slice(-20);me.resp=resp;S.db.doc("sellers/"+S.uid).update({resp}).catch(()=>{})}
function respMed(uid){const r=(S.sellers[uid]||{}).resp;if(!Array.isArray(r)||r.length<3)return null;const a=[...r].sort((x,y)=>x-y);return a[Math.floor(a.length/2)]}
const respFast=uid=>{const m=respMed(uid);return m!=null&&m<=180?1:0};
function respText(m){return m<=60?"1시간 안에":m<=180?"3시간 안에":m<=720?"반나절 안에":m<=1440?"하루 안에":`${Math.ceil(m/1440)}일 안에`}
function respShort(uid){const m=respMed(uid);return m==null?"-":respText(m).replace(" 안에","")}
function respHTML(uid){const m=respMed(uid);if(m==null)return `<div class="meta resp">💬 답변 기록이 아직 적어요</div>`;
  return `<div class="meta resp">${m<=180?'<span class="chip ok">⚡ 빠른 답변</span> ':""}💬 보통 ${respText(m)} 답해요</div>`}
/* 빠른 답장: 판매자는 자주 쓰는 답, 손님은 자주 묻는 질문 */
const QR_SELLER=["문의 감사합니다. 확인하고 바로 답드릴게요.","오늘 캐서 내일 보내 드려요.","사진 더 찍어서 보내 드릴게요.","지금은 재고가 없어요. 들어오면 알려 드릴게요.","주문은 상품 화면에서 안전결제로 해 주세요."];
const QR_BUYER=["언제 캔 건가요?","크기는 어느 정도인가요?","언제 보내 주시나요?","사진 더 볼 수 있을까요?"];
function qrHTML(other){const l=S.sellers[S.uid]&&!S.sellers[other]?QR_SELLER:S.sellers[other]?QR_BUYER:[];return l.map(t=>`<button type="button" data-qr="${esc(t)}">${esc(t)}</button>`).join("")}
function qrBind(){const q=$("#qr");if(!q)return;q.hidden=!q.children.length;q.querySelectorAll("[data-qr]").forEach(b=>b.onclick=()=>{const ta=$("#cText");ta.value=(ta.value.trim()?ta.value.trim()+" ":"")+b.dataset.qr;ta.focus()})}
'''
patch('''function sellerRow(uid,ctx){''', FN + '''function sellerRow(uid,ctx){''', "fn")

CSS = '''.faqform{border:1px dashed var(--line);border-radius:12px;padding:8px 12px;margin:6px 0}.faqform summary{cursor:pointer;font-weight:600}
.faqbox{border:1px solid var(--pine-soft);background:color-mix(in srgb,var(--pine) 6%,var(--surface));border-radius:12px;padding:10px 12px;margin-top:6px}
.faqbox dl{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;margin:6px 0 0}.faqbox dt{color:var(--muted);font-size:14px}.faqbox dd{margin:0;font-size:14px}
.resp{font-size:13px}.resp .chip{font-size:11.5px}
.qr{display:flex;gap:6px;overflow-x:auto;padding:8px 10px 0;scrollbar-width:none}.qr[hidden]{display:none}
.qr button{flex:none;border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:999px;padding:5px 11px;font:inherit;font-size:13px;cursor:pointer;white-space:nowrap}
'''
patch('.hask{display:flex;', CSS + '.hask{display:flex;', "css")
p.write_text(s, encoding="utf-8"); print("ok")
