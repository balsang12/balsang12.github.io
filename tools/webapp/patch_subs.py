#!/usr/bin/env python3
"""v92: 정기배송 — 약초차·청 정기배송, 효도 정기배송(받는 분 따로·카드·생산자 카드), 판매자 발송 목록, 손님 건너뛰기·해지."""
import sys, pathlib
p = pathlib.Path(sys.argv[1]); s = p.read_text(encoding="utf-8")
def patch(old, new, label, count=1):
    global s
    n = s.count(old)
    if n != count: sys.exit(f"{label}: expected {count}, found {n}")
    s = s.replace(old, new)

# 데이터 구독
patch('''  ["products","orders","requests","quotes","reviews","auctions","bids"].forEach(c=>sub(c,c));''',
      '''  ["products","orders","requests","quotes","reviews","auctions","bids","subs"].forEach(c=>sub(c,c));''', "subscribe")

# ---------- 상품 화면: 정기배송 신청 ----------
patch('''`+shipOptHTML(p)+giftOptHTML(p)''', '''`+shipOptHTML(p)+giftOptHTML(p)+subOptHTML(p)''', "detail sub opt")
patch('''  if($("#gPick"))$("#gPick").onclick=()=>giftToggle(p);''', '''  if($("#gPick"))$("#gPick").onclick=()=>giftToggle(p);
  subBind(p);''', "detail sub bind")
patch('''<dt>배송</dt><dd>${shipSpec(p)}</dd>''', '''<dt>배송</dt><dd>${shipSpec(p)}</dd>${p.sub?.on?`<dt>정기배송</dt><dd>🔁 매달 ${p.sub.day}일 발송${p.sub.pct?` · <b>${p.sub.pct}% 할인</b>`:""}</dd>`:""}''', "spec sub")
patch('''${p.qd?.length?'<span class="chip">수량 할인</span>':""}''', '''${p.qd?.length?'<span class="chip">수량 할인</span>':""}${p.sub?.on?'<span class="chip ok">정기배송</span>':""}''', "card sub chip")

# ---------- 판매자: 내 상품에서 정기배송 켜기 ----------
patch('''    <details class="faqform"><summary>📦 수량 할인 ${p.qd?.length?''',
'''    <details class="faqform"><summary>🔁 정기배송 ${p.sub?.on?`<span class="chip ok">매달 ${p.sub.day}일 · ${p.sub.pct||0}% 할인</span>`:'<span class="meta">약초차·청처럼 오래 두는 상품에 좋아요</span>'}</summary>${p.form==="생물"?'<p class="meta" style="margin:6px 0">생물은 날짜를 맞춰 보내기 어려워 정기배송을 열 수 없어요. 건조·가공품으로 열어 주세요.</p>':`<div class="qdrow"><label class="ochk"><input type="checkbox" id="sbOn-${p.id}" ${p.sub?.on?"checked":""}> 정기배송 받기</label><span>매달</span><input id="sbDay-${p.id}" type="number" min="1" max="28" value="${p.sub?.day||10}" class="num" aria-label="발송일"><span>일 발송 ·</span><input id="sbPct-${p.id}" type="number" min="0" max="30" value="${p.sub?.pct??5}" class="num" aria-label="정기배송 할인"><span>% 할인</span></div><div class="actions"><button class="btn sm primary" data-act="subP" data-id="${p.id}">저장</button></div>`}</details>
    <details class="faqform"><summary>📦 수량 할인 ${p.qd?.length?''', "my items sub")

# ---------- 판매자 화면: 보낼 정기배송 / 손님 화면: 내 정기배송 ----------
patch('''  $("#sellerOrders").innerHTML=revTodoHTML()+(''', '''  $("#sellerOrders").innerHTML=revTodoHTML()+subsSellerHTML()+(''', "seller subs")
patch('''  $("#myOrders").innerHTML=mine.length?mine.map(o=>{''', '''  $("#myOrders").innerHTML=subsBuyerHTML()+(mine.length?mine.map(o=>{''', "buyer subs start")
patch('''`<div class="empty">아직 주문이 없습니다. <button class="btn sm" data-go="shop">마켓 둘러보기</button></div>`;''',
      '''`<div class="empty">아직 주문이 없습니다. <button class="btn sm" data-go="shop">마켓 둘러보기</button></div>`);''', "buyer subs end")

# 생산자 카드: 정기배송에도
patch('''function openProdCard(oid){const o=S.orders.find(x=>x.id===oid);if(!o)return;''',
      '''function openProdCard(oid){const o=S.orders.find(x=>x.id===oid)||(S.subs||[]).find(x=>x.id===oid);if(!o)return;''', "prodcard subs")

# 선물 코너: 효도 정기배송 묶음
patch('''["light","💌 가볍게 마음만",p=>p.price<=30000]];''', '''["light","💌 가볍게 마음만",p=>p.price<=30000],["subs","🔁 효도 정기배송",p=>!!p.sub?.on]];''', "gift theme")
patch('''const inGift=p=>{const g=giftCfg();return g.ids.includes(p.id)||((!!p.gift||!!p.set)&&!g.hide.includes(p.id))};''',
      '''const inGift=p=>{const g=giftCfg();return g.ids.includes(p.id)||((!!p.gift||!!p.set||!!p.sub?.on)&&!g.hide.includes(p.id))};''', "inGift subs")

# 동작
patch('''  async qdP(id){''', '''  async subP(id){const on=!!$("#sbOn-"+id)?.checked,day=Math.min(28,Math.max(1,Math.floor(+$("#sbDay-"+id).value||10))),pct=Math.min(30,Math.max(0,Math.floor(+$("#sbPct-"+id).value||0)));
    await guard(()=>S.db.doc("products/"+id).update({sub:{on,day,pct}}),on?`정기배송을 열었습니다. 매달 ${day}일에 보내 주세요`:"정기배송을 닫았습니다. 이미 구독 중인 손님 것은 계속 보내 주세요")},
  async subShip(id){const x=S.subs.find(y=>y.id===id);const t=($("#str-"+id)?.value||"").trim();if(!t){toast("송장번호를 넣어 주세요");return}
    await guard(()=>S.db.doc("subs/"+id).update({lastSent:kstDay(),lastCourier:$("#scr-"+id).value,lastTracking:t.slice(0,40),nextDate:addMonths(x.nextDate,x.every||1),sent:(x.sent||0)+1}),"발송 처리했습니다. 다음 발송일로 넘어갔어요")},
  async subSkip(id){const x=S.subs.find(y=>y.id===id);await guard(()=>S.db.doc("subs/"+id).update({nextDate:addMonths(x.nextDate,x.every||1),skipAt:Date.now()}),`이번 회차를 건너뛰었어요. 다음 발송은 ${mdKo(addMonths(x.nextDate,x.every||1))}이에요`)},
  async subEvery(id){const x=S.subs.find(y=>y.id===id),e=(x.every||1)===1?2:1;await guard(()=>S.db.doc("subs/"+id).update({every:e}),e===1?"매달 받도록 바꿨어요":"2개월마다 받도록 바꿨어요")},
  subEnd(id){const b=document.querySelector(`[data-act="subEnd"][data-id="${id}"]`);if(!b.dataset.armed){b.dataset.armed=1;b.textContent="한 번 더 누르면 해지";setTimeout(()=>{b.textContent="해지";delete b.dataset.armed},3000);return}
    guard(()=>S.db.doc("subs/"+id).update({status:"해지",endAt:Date.now()}),"정기배송을 해지했어요. 더는 결제·발송되지 않아요")},
  async qdP(id){''', "acts")

FN = r'''
/* ---------- 정기배송 ---------- */
function addMonths(d,n){const [y,m,dd]=String(d).split("-").map(Number);const t=new Date(Date.UTC(y,m-1+n,1));const last=new Date(Date.UTC(t.getUTCFullYear(),t.getUTCMonth()+1,0)).getUTCDate();return `${t.getUTCFullYear()}-${String(t.getUTCMonth()+1).padStart(2,"0")}-${String(Math.min(dd,last)).padStart(2,"0")}`}
function firstSubDate(day){const t=kstDay(),[y,m]=t.split("-").map(Number);let d=`${y}-${String(m).padStart(2,"0")}-${String(day).padStart(2,"0")}`;if(d<=isoDay(Date.now()+2*864e5))d=addMonths(d,1);return d}
const subUnit=p=>Math.round(p.price*(100-(p.sub?.pct||0))/100/10)*10;
function subOptHTML(p){if(!p.sub?.on||p.form==="생물")return "";const fd=firstSubDate(p.sub.day);
  return `<details class="subopt" id="sOpt"><summary>🔁 정기배송으로 받기${p.sub.pct?` · ${p.sub.pct}% 할인`:""}</summary>
   <div class="row2"><div class="field"><label for="sbEvery">얼마마다 받을까요?</label><select id="sbEvery"><option value="1">매달</option><option value="2">2개월마다</option></select></div>
   <div class="field"><label for="sbQty">한 번에 몇 개</label><input id="sbQty" type="number" min="1" max="${Math.max(1,Math.min(20,p.stock))}" value="1" class="num"></div></div>
   <label class="gchk"><input type="checkbox" id="sbGift"> 💝 효도 정기배송 · 받는 분이 따로 있어요 (부모님 등)</label>
   <div id="sbGiftBox" hidden><div class="field"><label for="sbCard">매번 넣을 카드 문구 (60자)</label><input id="sbCard" maxlength="60" placeholder="예: 늘 건강하세요. 사랑합니다"></div>
    <label class="gchk"><input type="checkbox" id="sbPc" checked> 생산자 카드 넣기</label><p class="meta" style="margin:0 0 6px">받는 분 이름·주소는 결제할 때 따로 적습니다.</p></div>
   <p class="meta" style="margin:4px 0" id="sbSum"></p>
   <p class="meta" style="margin:0 0 8px">첫 발송 <b>${esc(mdKo(fd))}</b> · 그 뒤 매번 ${p.sub.day}일에 보내요. 결제일 3일 전에 미리 알려 드리고, ‘내 거래’에서 언제든 건너뛰기·주기 바꾸기·해지할 수 있어요.</p>
   <button class="btn gold needWrite" type="button" id="sbGo">정기배송 시작하기 (테스트)</button></details>`}
function subBind(p){const g=$("#sbGo");if(!g)return;const c=shipCfg(p.sellerId),ship=c.dry;
  const upd=()=>{const q=Math.max(1,Math.floor(+$("#sbQty").value||1));$("#sbSum").innerHTML=`1회 <b class="num">${won(subUnit(p)*q+ship)}</b> (상품 ${won(subUnit(p)*q)}${p.sub.pct?` · 정가보다 ${won((p.price-subUnit(p))*q)} 할인`:""} + 배송비 ${won(ship)})`};upd();
  $("#sbQty").oninput=upd;$("#sbGift").onchange=()=>{$("#sbGiftBox").hidden=!$("#sbGift").checked};
  g.onclick=async()=>{if(!S.uid){toast("로그인이 필요합니다");return}if(BETA()){await betaStop((findHerb(p.item)||guessHerb(p.name)||{}).name||p.name,"market");return}
    const q=Math.max(1,Math.floor(+$("#sbQty").value||1)),gift=$("#sbGift").checked?{card:$("#sbCard").value.trim().slice(0,60),prodCard:$("#sbPc").checked}:null;
    if(gift&&PII.test(gift.card)){toast("카드 문구에 전화번호·계좌는 넣을 수 없어요");return}
    g.disabled=true;const ok=await guard(()=>S.db.collection("subs").add({productId:p.id,productName:p.name,unit:p.unit,sellerId:p.sellerId,buyerId:S.uid,qty:q,every:+$("#sbEvery").value||1,price:subUnit(p),pct:p.sub.pct||0,ship,...(gift?{gift}:{}),nextDate:firstSubDate(p.sub.day),sent:0,status:"구독중",createdAt:Date.now()}),"정기배송을 시작했어요. ‘내 거래’에서 다음 발송일을 볼 수 있어요");
    if(ok){$("#dlg").close();go("my")}else g.disabled=false}}
function subsBuyerHTML(){const l=(S.subs||[]).filter(x=>x.buyerId===S.uid&&x.status==="구독중").sort((a,b)=>a.nextDate<b.nextDate?-1:1);if(!l.length)return "";
  return `<div class="subbox"><b>🔁 내 정기배송 ${l.length}건</b>${l.map(x=>`<div class="item sunk"><div class="itop"><b>${esc(x.productName)}${x.gift?' <span class="chip gold">효도</span>':""}</b><span class="chip ok">${(x.every||1)===1?"매달":"2개월마다"}</span></div>
    <div class="meta num">${x.qty}×${esc(x.unit||"")} · 1회 ${won(x.price*x.qty+(x.ship||0))} · 다음 발송 <b>${esc(mdKo(x.nextDate))}</b>${x.sent?` · ${x.sent}회 받음`:""}</div>
    ${x.lastTracking?`<div class="meta">지난 송장: ${esc(x.lastCourier||"")} ${esc(x.lastTracking)}</div>`:""}
    <div class="actions"><button class="btn sm" data-act="subSkip" data-id="${x.id}">이번 회차 건너뛰기</button><button class="btn sm" data-act="subEvery" data-id="${x.id}">${(x.every||1)===1?"2개월마다로":"매달로"} 바꾸기</button><button class="btn sm danger" data-act="subEnd" data-id="${x.id}">해지</button></div></div>`).join("")}</div>`}
function subsSellerHTML(){if(!S.uid)return "";const all=(S.subs||[]).filter(x=>x.sellerId===S.uid&&x.status==="구독중");if(!all.length)return "";
  const soon=isoDay(Date.now()+7*864e5),due=all.filter(x=>x.nextDate<=soon).sort((a,b)=>a.nextDate<b.nextDate?-1:1),today=kstDay();
  return `<div class="subbox"><b>🔁 정기배송 ${all.length}건 · 일주일 안에 보낼 것 ${due.length}건</b>${due.map(x=>`<div class="item sunk"><div class="itop"><b>${esc(x.productName)} ${x.qty}×${esc(x.unit||"")}</b>${x.nextDate<today?'<span class="chip hot">발송일 지남</span>':x.nextDate===today?'<span class="chip gold">오늘 발송</span>':`<span class="chip">${esc(mdKo(x.nextDate))} 발송</span>`}</div>
    <div class="meta">${(x.every||1)===1?"매달":"2개월마다"} · ${x.sent||0}회 보냄${x.gift?" · 💝 효도 정기배송 (받는 분 따로)":""}</div>
    ${x.gift?`<div class="notice">${x.gift.card?`카드 문구: “${esc(x.gift.card)}”`:"카드 문구 없음"}${x.gift.prodCard?`<div class="actions" style="margin-top:6px"><button class="btn sm gold" type="button" data-pcard="${esc(x.id)}">🪪 생산자 카드 만들기·인쇄</button></div>`:""}</div>`:""}
    <div class="actions"><select id="scr-${x.id}" aria-label="택배사"><option>우체국택배</option><option>CJ대한통운</option><option>한진택배</option><option>롯데택배</option></select><input id="str-${x.id}" placeholder="송장번호" aria-label="송장번호"><button class="btn sm primary" data-act="subShip" data-id="${x.id}">발송 처리</button></div></div>`).join("")||'<div class="meta">이번 주에 보낼 정기배송은 없어요.</div>'}</div>`}
'''
patch('''function sellerRow(uid,ctx){''', FN + '''function sellerRow(uid,ctx){''', "fn")

CSS = '''.subopt{border:1px solid var(--pine);border-radius:14px;padding:8px 12px;margin-top:8px;background:var(--pine-soft)}.subopt summary{cursor:pointer;font-weight:700;color:var(--pine)}
.subbox{border:1px solid var(--pine);background:color-mix(in srgb,var(--pine) 7%,var(--surface));border-radius:12px;padding:10px 12px;margin:0 0 12px;display:grid;gap:8px}
.subbox .actions{flex-wrap:wrap}.subbox .actions input{flex:1 1 120px;min-width:0}
'''
patch('.hask{display:flex;', CSS + '.hask{display:flex;', "css")
p.write_text(s, encoding="utf-8"); print("ok")
