#!/usr/bin/env python3
"""v88: 선물 코너 보완 — 선물세트, 생산자 카드, 받는 분별 묶음, 명절 전 도착 마지막 주문일, 예약 주문(받는 날 맞춰 발송)·발송일별 목록."""
import sys, pathlib
p = pathlib.Path(sys.argv[1]); s = p.read_text(encoding="utf-8")
def patch(old, new, label, count=1):
    global s
    n = s.count(old)
    if n != count: sys.exit(f"{label}: expected {count}, found {n}")
    s = s.replace(old, new)

# ---------- 선물 코너 함수 다시 쓰기 ----------
i = s.index("const inGift=p=>{")
j = s.index("async function giftToggle(p){")
NEW = r'''const inGift=p=>{const g=giftCfg();return g.ids.includes(p.id)||((!!p.gift||!!p.set)&&!g.hide.includes(p.id))};
const giftList=()=>{const g=giftCfg();return live().filter(p=>p.stock>0&&inGift(p)).sort((a,b)=>(g.ids.includes(b.id)-g.ids.includes(a.id))||(!!b.set-!!a.set)||a.price-b.price)};
const GTIERS=[["all","전체",0,Infinity],["t1","5만 원 이하",0,50000],["t2","5~15만 원",50001,150000],["t3","15~30만 원",150001,300000],["t4","30만 원 이상",300001,Infinity]];
/* 받는 분별 묶음: 쇼핑도우미 선물 질문과 같은 기준 */
const keepsP=p=>p.form!=="생물";
const GTHEMES=[["any","모두",()=>true],["parents","👵 부모님께",p=>p.price>=30000||RECO_GIFT.includes(p.item||"")||!!p.set],["boss","🙇 은사·윗분께",p=>p.price<=150000&&keepsP(p)],["biz","🏢 거래처 대량",p=>p.price<=50000&&p.stock>=10],["light","💌 가볍게 마음만",p=>p.price<=30000]];
const mdKo=d=>{const [,m,dd]=String(d).split("-");return `${+m}월 ${+dd}일`};
const isoDay=t=>new Date(t+9*3600e3).toISOString().slice(0,10);
const dayTs=d=>Date.parse(d+"T12:00:00+09:00");
function giftDaysLeft(){const g=giftCfg();if(!g.cut)return null;return Math.round((dayTs(g.cut)-dayTs(kstDay()))/864e5)}
function giftCutText(){const g=giftCfg();if(!g.cut)return "";const d=giftDaysLeft();return d<0?"택배 마감이 지났어요 · 도착이 늦을 수 있어요":d===0?"오늘이 택배 마감일이에요":`${mdKo(g.cut)}까지 주문하면 제때 받아요${d<=3?` · 마감 D-${d}`:""}`}
/* 상품마다 명절 전 도착 마지막 주문일: 생물은 월~목에만 보내므로 마감일이 금~일이면 그 주 목요일로 당김 */
function lastOrderDay(p){const g=giftCfg();if(!g.cut)return "";let t=dayTs(g.cut);if(p.form==="생물")while([5,6,0].includes(kWD(t)))t-=864e5;return isoDay(t)}
function giftTag(p){const t=p.price<=150000?'<span class="chip ok">선물 한도 15만 원 안</span>':p.price<=300000?'<span class="chip gold">명절 기간 한도 30만 원 안</span>':'<span class="chip">프리미엄</span>';
  const lo=lastOrderDay(p),late=lo&&kstDay()>lo;
  return `<div class="gtag">${p.set?'<span class="chip gold">선물세트</span>':""}${t}${p.gift?`<span class="chip">🎁 포장${p.giftWrap?" +"+won(p.giftWrap):" 무료"}</span>`:""}</div>${lo?`<div class="glast ${late?"late":""}">${late?"명절 전 도착이 어려워요":`📦 ${esc(mdKo(lo))}까지 주문하면 명절 전 도착`}</div>`:""}`}
function renderGiftBan(){const el=$("#giftBan");if(!el)return;const g=giftCfg(),lv=giftLive(),pre=!lv&&S.owner&&g.on;
  if(!lv&&!pre){el.hidden=true;el.innerHTML="";return}
  const n=giftList().length,ct=giftCutText(),dl=giftDaysLeft();el.hidden=false;
  el.innerHTML=`<button class="giftban" type="button" data-gift="all"><span class="gi" aria-hidden="true">🎁</span><span class="gt"><b>${esc(g.title)} 코너${pre?' <span class="chip">미리보기 · 손님에겐 아직 안 보임</span>':""}${dl!=null&&dl>=0&&dl<=3?` <span class="chip hot">마감 D-${dl}</span>`:""}</b><span>${n?`${n}가지 · 마음 전하는 실속 선물부터 귀한 산양삼까지`:"선물 상품을 모으고 있어요"}${ct?` · <em>${esc(ct)}</em>`:""}</span></span><span class="go">보러 가기 →</span></button>
  <div class="gtiers" role="list">${GTHEMES.slice(1).map(([k,l])=>`<button type="button" role="listitem" data-gift="all|${k}">${l}</button>`).join("")}</div>`}
function openGift(key){const [tk,th]=String(key||"all").split("|"),g=giftCfg(),T=GTIERS.find(x=>x[0]===tk)||GTIERS[0],H=GTHEMES.find(x=>x[0]===th)||GTHEMES[0],dlg=$("#dlg");openA=null;
  const all=giftList().filter(H[2]),inT=t=>p=>p.price>=t[2]&&p.price<=t[3],list=all.filter(inT(T)),ct=giftCutText(),cur=`${T[0]}|${H[0]}`;
  dlg.innerHTML=`<div class="dlg giftdlg"><button class="close" aria-label="닫기" type="button">×</button>
   <div class="eyebrow">농부와 심마니 직거래 · 채취 근거 확인 상품</div><h2 style="font-size:24px;margin:2px 0 6px">🎁 ${esc(g.title)}</h2>
   ${ct?`<div class="notice" style="margin:0 0 10px">📦 ${esc(ct)}${g.cut&&kstDay()<=g.cut?" · 받는 날을 고르면 판매자가 그 날짜에 맞춰 보냅니다":""}</div>`:""}
   <div class="meta" style="margin:0 0 4px">누구에게 보내세요?</div>
   <div class="gtiers gthemes" role="tablist">${GTHEMES.map(([k,l])=>`<button type="button" role="tab" data-gift="${T[0]}|${k}" aria-pressed="${k===H[0]}">${l}</button>`).join("")}</div>
   <div class="gtiers" role="tablist">${GTIERS.map(t=>`<button type="button" role="tab" data-gift="${t[0]}|${H[0]}" aria-pressed="${t[0]===T[0]}">${t[1]}${t[0]==="all"?"":` <small class="num">${all.filter(inT(t)).length}</small>`}</button>`).join("")}</div>
   ${H[0]==="biz"?`<div class="notice" style="margin:10px 0 0">🏢 10개 넘게 보내시면 견적을 받아 보세요. 받는 곳이 여러 군데여도 한 번에 맡길 수 있어요. <button class="btn sm gold" type="button" data-gift-bulk="1">무료 견적 받기</button></div>`:""}
   <div class="grid hrow0 giftgrid" style="margin-top:12px">${list.length?list.map(p=>card(p).replace('<div class="cbody">','<div class="cbody">'+giftTag(p))).join(""):emptyBox(all.length?"이 가격대 선물이 아직 없습니다. 다른 가격대를 눌러 보세요.":"이 묶음에 맞는 선물을 모으고 있어요. 다른 묶음을 눌러 보세요.","")}</div>
   <div class="actions" style="margin-top:14px"><button class="btn gold" type="button" data-go="auction">🏔 귀한 산삼은 경매에서</button><button class="btn" type="button" data-gift-bulk="1">🏢 회사·단체 대량 주문 (견적 무료)</button></div>
   <p class="meta" style="margin:12px 0 0;line-height:1.6">선물마다 생산자 카드(누가 어디서 캤는지)를 넣어 보낼 수 있어요. ‘한도 안’ 표시는 공무원·교사·언론인 등에게 보낼 때 참고하시라고 붙였습니다. 청탁금지법상 농수산물·농수산가공품 선물은 평소 15만 원, 설·추석 기간에는 30만 원까지입니다 (상품 1개 값 기준 · 배송비·포장비 제외). 정확한 적용은 국민권익위원회에 확인해 주세요.</p></div>`;
  dlg.querySelector(".close").onclick=()=>dlg.close();
  dlg.querySelectorAll(".card").forEach(c=>c.addEventListener("click",()=>{S.fromGift=cur},true));
  if(!dlg.open)dlg.showModal();dlg.scrollTop=0;requestAnimationFrame(paintAll)}
function giftOptHTML(p){const tm=new Date(Date.now()+9*3600e3+2*864e5).toISOString().slice(0,10),lo=lastOrderDay(p),gl=typeof giftLive==="function"&&giftLive();
  return `<details class="giftopt" id="gOpt"><summary>🎁 선물로 보내기</summary>
   ${gl&&lo?`<p class="meta" style="margin:4px 0 6px">${kstDay()>lo?"지금 주문하면 명절 전에 도착하기 어려워요.":`📦 <b>${esc(mdKo(lo))}까지</b> 주문하면 명절 전에 도착해요.`}</p>`:""}
   <div class="field"><label for="gCard">카드 문구 (60자까지)</label><input id="gCard" maxlength="60" placeholder="예: 새해 복 많이 받으세요. 늘 건강하세요"></div>
   <div class="field"><label for="gDate">받고 싶은 날 (선택 · 고르면 판매자가 그날에 맞춰 보내요)</label><input id="gDate" type="date" min="${tm}"></div>
   ${p.gift||p.set?`<label class="gchk"><input type="checkbox" id="gWrap" checked> 선물 포장 ${p.giftWrap?"+"+won(p.giftWrap):"(무료)"}</label>`:`<p class="meta" style="margin:0 0 6px">이 상품은 선물 포장을 하지 않습니다</p>`}
   <label class="gchk"><input type="checkbox" id="gPc" checked> 생산자 카드 넣기 (누가 어디서 캤는지 · 무료)</label>
   <label class="gchk"><input type="checkbox" id="gHide" checked> 받는 분에게 가격이 안 보이게 (명세서 빼기)</label>
   <p class="meta" style="margin:6px 0 0">받는 분 이름·주소는 결제할 때 따로 적습니다. 주문자와 다른 곳으로 보낼 수 있어요.</p></details>`}
function giftNote(o){const g=o.gift;if(!g)return "";
  return `<div class="notice">🎁 <b>선물 주문</b>${g.wrap?` · 선물 포장${g.wrapFee?" ("+won(g.wrapFee)+")":""}`:""}${g.date?` · <b>${esc(mdKo(g.date))}</b> 도착 희망`:""}${g.hidePrice?" · <b>가격이 적힌 명세서를 넣지 마세요</b>":""}${g.card?`<br>카드 문구: “${esc(g.card)}”`:""}${g.prodCard?`<div class="actions" style="margin-top:6px"><button class="btn sm gold" type="button" data-pcard="${esc(o.id)}">🪪 생산자 카드 만들기·인쇄</button></div>`:""}</div>`}
/* ---------- 선물세트 ---------- */
function setRead(pre){const items=($("#"+pre+"Items")?.value||"").split(/\n|,/).map(x=>x.trim()).filter(Boolean).slice(0,8).map(x=>x.slice(0,40)),intro=($("#"+pre+"Intro")?.value||"").trim().slice(0,120);
  if([...items,intro].some(v=>PII.test(v)))return {bad:true};return items.length?{set:{items,intro}}:{}}
function setHTML(p){if(!p.set)return "";return `<div class="setbox"><b>🎁 선물세트 구성</b><ul>${p.set.items.map(x=>`<li>${esc(x)}</li>`).join("")}</ul>${p.set.intro?`<p class="meta" style="margin:4px 0 0">“${esc(p.set.intro)}”</p>`:""}</div>`}
/* ---------- 생산자 카드 ---------- */
function openProdCard(oid){const o=S.orders.find(x=>x.id===oid);if(!o)return;const s=S.sellers[o.sellerId]||{},pp=S.products.find(x=>x.id===o.productId)||{},t=trust(o.sellerId);
  const badges=[pp.proofOk?"채취 근거 확인":"",/인증/.test(pp.grow||"")?"인증 재배":"",pp.cert?"품질 검사 "+pp.cert:"",t.cert?"농마니 인증 판매자":""].filter(Boolean);
  const dlg=$("#dlg");openA=null;
  dlg.innerHTML=`<div class="dlg"><button class="close" aria-label="닫기" type="button">×</button>
   <p class="meta noprint" style="margin:0 0 8px">상자에 넣을 생산자 카드예요. 인쇄하거나 화면을 캡처해서 출력해 주세요. (명함 두 장 크기)</p>
   <div class="pcard" id="pcard">
    <div class="pc-top"><span class="pc-logo">농부와 <b>심마니</b></span><span class="pc-sub">산지에서 직접 보낸 선물</span></div>
    <div class="pc-who">${avaHTML(o.sellerId,"big")}<div><b class="pc-name">${esc(s.shopName||"")}</b><div>${esc((s.role||"").replace(/ \(.*\)/,""))} · ${esc(s.region||"")}</div></div></div>
    ${s.bio?`<p class="pc-bio">“${esc(s.bio)}”</p>`:""}
    <dl class="pc-dl"><dt>보내는 것</dt><dd>${esc(o.productName)}</dd>${pp.faq?.harv?`<dt>캔 날</dt><dd>${esc(pp.faq.harv)}</dd>`:""}${pp.region?`<dt>산지</dt><dd>${esc(pp.region)}</dd>`:""}${pp.faq?.keep?`<dt>보관</dt><dd>${esc(pp.faq.keep)}</dd>`:""}</dl>
    ${badges.length?`<div class="pc-badges">${badges.map(b=>`<span>✔ ${esc(b)}</span>`).join("")}</div>`:""}
    ${o.gift?.card?`<p class="pc-msg">${esc(o.gift.card)}</p>`:""}
    <div class="pc-foot">nongmani.com</div>
   </div>
   <div class="actions noprint" style="margin-top:12px"><button class="btn primary" type="button" id="pcPrint">인쇄하기</button></div></div>`;
  dlg.querySelector(".close").onclick=()=>dlg.close();
  $("#pcPrint").onclick=()=>{document.body.classList.add("printcard");try{window.print()}catch(e){toast("인쇄가 막혀 있어요. 화면을 캡처해서 출력해 주세요")}setTimeout(()=>document.body.classList.remove("printcard"),500)};
  if(!dlg.open)dlg.showModal();dlg.scrollTop=0}
/* ---------- 예약 주문: 받는 날에 맞춘 발송일 ---------- */
function sendOn(o){const d=o.gift?.date;if(!d)return null;let t=dayTs(d)-2*864e5;if(o.fresh)while([5,6,0].includes(kWD(t)))t-=864e5;else while(kWD(t)===0)t-=864e5;return Math.max(kDayEnd(t),kDayEnd(o.createdAt))}
const shipBy=o=>sendOn(o)||ordDue(o);
function sendPlanHTML(list){const m=new Map();list.filter(o=>o.status==="결제완료").forEach(o=>{const k=isoDay(shipBy(o));m.set(k,(m.get(k)||0)+1)});if(!m.size)return "";
  const today=kstDay();return `<div class="sendplan"><b>📅 보낼 날짜별</b> ${[...m.entries()].sort().map(([k,n])=>`<span class="chip ${k<today?"hot":k===today?"gold":""}">${k<today?"지남 · ":k===today?"오늘 · ":""}${esc(kDayLabel(dayTs(k)))} ${n}건</span>`).join(" ")}</div>`}
'''
s = s[:i] + NEW + s[j:]

# 주문 저장: 생산자 카드
patch('''wrap:!!$("#gWrap")?.checked,wrapFee:wf(),hidePrice:$("#gHide").checked}:null;''',
      '''wrap:!!$("#gWrap")?.checked,wrapFee:wf(),hidePrice:$("#gHide").checked,prodCard:!!$("#gPc")?.checked}:null;''', "order prodCard")
# 발송 안내를 받는 날 기준으로
patch('''function shipNoteSeller(o){if(o.status!=="결제완료")return "";const due=ordDue(o),late=Date.now()>due,''',
      '''function shipNoteSeller(o){if(o.status!=="결제완료")return "";const due=shipBy(o),late=Date.now()>due,sd=sendOn(o),''', "seller due")
patch('''`📦 <b>${kDayLabel(due)}까지</b> 보내 주세요.`}''',
      '''sd?`📅 <b>${kDayLabel(due)}</b>에 보내 주세요 (받는 날 ${esc(mdKo(o.gift.date))}${o.fresh?" · 너무 일찍 보내면 상할 수 있어요":""})`:`📦 <b>${kDayLabel(due)}까지</b> 보내 주세요.`}''', "seller send-on text")
patch('''if(o.status==="결제완료"){const due=ordDue(o);''', '''if(o.status==="결제완료"){const due=shipBy(o);''', "buyer due")
patch('''`${kDayLabel(due)}까지 발송 예정${o.fresh?" (생물은 월~목 발송)":""}`}''',
      '''sendOn(o)?`${kDayLabel(due)}에 발송 예정 · ${esc(mdKo(o.gift.date))} 도착 맞춤`:`${kDayLabel(due)}까지 발송 예정${o.fresh?" (생물은 월~목 발송)":""}`}''', "buyer send-on text")
# 판매자 주문: 날짜별 요약 + 보낼 날짜 순서
patch('''  $("#sellerOrders").innerHTML=myO.length?myO.map(o=>''',
      '''  const myOs=[...myO].sort((a,b)=>(b.status==="결제완료")-(a.status==="결제완료")||(a.status==="결제완료"?shipBy(a)-shipBy(b):b.createdAt-a.createdAt));
  $("#sellerOrders").innerHTML=myO.length?sendPlanHTML(myO)+myOs.map(o=>''', "seller order list")

# ---------- 선물세트: 올리기·내 상품·상세·카드 ----------
patch('''        <div class="row2 giftsell">''',
'''        <details class="faqform setform"><summary>🎁 선물세트로 올리기 <span class="meta">(구성품을 적으면 선물 코너 앞쪽에 보여요)</span></summary>
          <div class="field"><label for="sSetItems">구성품 (한 줄에 하나, 최대 8개)</label><textarea id="sSetItems" rows="3" placeholder="예: 더덕 500g&#10;도라지청 1병&#10;오미자차 20포"></textarea></div>
          <div class="field"><label for="sSetIntro">받는 분께 드리는 소개 (120자)</label><input id="sSetIntro" maxlength="120" placeholder="예: 지리산 자락에서 직접 캔 더덕과 집에서 담근 도라지청을 함께 담았습니다"></div></details>
        <div class="row2 giftsell">''', "set form")
patch('''faq:faqRead("sFq"),''', '''faq:faqRead("sFq"),...(()=>{const r=setRead("sSet");return r.bad?{}:r})(),''', "set add")
patch('''    <details class="faqform"><summary>자주 묻는 질문 ${faqCount(p)?''',
'''    <details class="faqform"><summary>🎁 선물세트 ${p.set?`<span class="chip gold">구성 ${p.set.items.length}가지</span>`:'<span class="meta">구성품을 적으면 선물세트가 돼요</span>'}</summary><div class="field"><label for="msItems-${p.id}">구성품 (한 줄에 하나)</label><textarea id="msItems-${p.id}" rows="3">${esc((p.set?.items||[]).join("\\n"))}</textarea></div><div class="field"><label for="msIntro-${p.id}">받는 분께 드리는 소개</label><input id="msIntro-${p.id}" maxlength="120" value="${esc(p.set?.intro||"")}"></div><div class="actions"><button class="btn sm primary" data-act="setP" data-id="${p.id}">저장</button></div></details>
    <details class="faqform"><summary>자주 묻는 질문 ${faqCount(p)?''', "my items set")
patch('''  async faqP(id){''', '''  async setP(id){const r=setRead("ms");const items=($("#msItems-"+id)?.value||"").split(/\\n|,/).map(x=>x.trim()).filter(Boolean).slice(0,8).map(x=>x.slice(0,40)),intro=($("#msIntro-"+id)?.value||"").trim().slice(0,120);
    if([...items,intro].some(v=>PII.test(v))){toast("전화번호·계좌·링크는 넣을 수 없어요");return}
    await guard(()=>S.db.doc("products/"+id).update({set:items.length?{items,intro}:null}),items.length?"선물세트로 저장했습니다. 선물 코너에 보입니다":"선물세트 표시를 뺐습니다")},
  async faqP(id){''', "act set")
patch('''    ${faqHTML(p)}''', '''    ${setHTML(p)}${faqHTML(p)}''', "detail set")
patch('''${isProc(p)?'<span class="chip gold">농가 가공</span>':""}''', '''${isProc(p)?'<span class="chip gold">농가 가공</span>':""}${p.set?'<span class="chip gold">선물세트</span>':""}''', "card chip")
# 클릭: 생산자 카드
patch('''  const gf=e.target.closest("[data-gift]");''', '''  const pcd=e.target.closest("[data-pcard]");if(pcd){openProdCard(pcd.dataset.pcard);return}
  const gf=e.target.closest("[data-gift]");''', "click pcard")

CSS = '''.glast{font-size:12px;color:var(--pine);margin:0 0 4px;font-weight:600}.glast.late{color:var(--berry)}
.gthemes button{font-weight:600}
.setbox{border:1px solid var(--gold);background:var(--gold-soft);border-radius:12px;padding:10px 12px;margin-top:6px}.setbox ul{margin:6px 0 0;padding-left:20px}
.sendplan{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:0 0 10px;font-size:14px}
.pcard{max-width:360px;margin:0 auto;border:1px solid var(--line);border-radius:14px;padding:18px;background:#fffdf7;color:#1d2a20;font-size:14px;line-height:1.6}
.pc-top{display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid #e6dcc4;padding-bottom:8px;margin-bottom:10px}.pc-logo{font-family:var(--display);font-size:18px;color:#2B5B41}.pc-logo b{color:#8A5B0B}.pc-sub{font-size:12px;color:#6b6b5e}
.pc-who{display:flex;gap:12px;align-items:center}.pc-name{font-size:18px}.pc-bio{margin:10px 0;font-style:italic}
.pc-dl{display:grid;grid-template-columns:auto 1fr;gap:2px 12px;margin:8px 0}.pc-dl dt{color:#6b6b5e}.pc-dl dd{margin:0}
.pc-badges{display:flex;flex-wrap:wrap;gap:4px 10px;font-size:12.5px;color:#2B5B41;margin:6px 0}.pc-msg{border-top:1px dashed #d8ccb0;padding-top:8px;margin:8px 0 0;font-size:15px}
.pc-foot{text-align:right;font-size:11px;color:#8a8a7a;margin-top:8px}
@media print{body.printcard *{visibility:hidden}body.printcard #pcard,body.printcard #pcard *{visibility:visible}body.printcard #pcard{position:fixed;left:0;top:0;border:1px solid #ccc}}
'''
patch('.hask{display:flex;', CSS + '.hask{display:flex;', "css")
p.write_text(s, encoding="utf-8"); print("ok")
