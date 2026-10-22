#!/usr/bin/env python3
"""v76: 명절 선물 코너 — 운영자 기간 설정, 첫 화면 배너, 가격대·청탁금지법 표시, 선물 옵션, 대량 주문 견적."""
import sys, pathlib
p = pathlib.Path(sys.argv[1]); s = p.read_text(encoding="utf-8")
def patch(old, new, label, count=1):
    global s
    n = s.count(old)
    if n != count: sys.exit(f"{label}: expected {count}, found {n}")
    s = s.replace(old, new)

# ---------- 1) 운영자 설정 ----------
patch('''    <label style="display:flex;gap:8px;align-items:center;font-size:14px"><input type="checkbox" id="cfgBeta">''',
'''    <div class="giftcfg"><h3 style="margin:14px 0 6px">🎁 명절 선물 코너</h3>
      <label style="display:flex;gap:8px;align-items:center;font-size:14px"><input type="checkbox" id="cfgGift"> 선물 코너 열기 (아래 기간에만 손님 첫 화면에 보입니다)</label>
      <div class="actions" style="margin:6px 0"><span class="meta">빠른 입력</span><button class="btn sm" type="button" data-gpre="ny">연말·새해</button><button class="btn sm" type="button" data-gpre="seol27">2027 설</button></div>
      <div class="field"><label for="cfgGiftTitle">코너 이름</label><input id="cfgGiftTitle" maxlength="30" placeholder="예: 2027 설 선물"></div>
      <div class="row2"><div class="field"><label for="cfgGiftStart">여는 날</label><input id="cfgGiftStart" type="date"></div><div class="field"><label for="cfgGiftEnd">닫는 날</label><input id="cfgGiftEnd" type="date"></div></div>
      <div class="field"><label for="cfgGiftCut">택배 마감일 (이날까지 주문하면 제때 도착)</label><input id="cfgGiftCut" type="date"></div>
      <p class="meta" style="margin:0 0 8px">판매자가 ‘선물 포장 가능’으로 표시한 상품이 자동으로 들어갑니다. 상품 화면의 ‘선물 코너에 넣기/빼기’로 직접 고를 수도 있습니다.</p></div>
    <label style="display:flex;gap:8px;align-items:center;font-size:14px"><input type="checkbox" id="cfgBeta">''', "cfg html")

patch('''$("#cfgHours").value=S.site?.csHours||""}''',
      '''$("#cfgHours").value=S.site?.csHours||"";giftCfgFill()}''', "cfg fill")
patch('''["cfgVideo","cfgReview","cfgProof","cfgPhone","cfgHours"]''',
      '''["cfgVideo","cfgReview","cfgProof","cfgPhone","cfgHours","cfgGiftTitle","cfgGiftStart","cfgGiftEnd","cfgGiftCut"]''', "cfg focus")
patch('''  if(vw>rw){toast("인증 영상 기준은 직접 승인 기준보다 낮아야 합니다");return}
  const v={''', '''  if(vw>rw){toast("인증 영상 기준은 직접 승인 기준보다 낮아야 합니다");return}
  const gS=$("#cfgGiftStart").value,gE=$("#cfgGiftEnd").value,gC=$("#cfgGiftCut").value;
  if($("#cfgGift").checked&&!(gS&&gE)){toast("선물 코너를 열려면 여는 날과 닫는 날을 골라 주세요");return}
  if(gS&&gE&&gS>gE){toast("선물 코너 닫는 날이 여는 날보다 빠릅니다");return}
  const v={giftOn:$("#cfgGift").checked,giftTitle:$("#cfgGiftTitle").value.trim().slice(0,30),giftStart:gS,giftEnd:gE,giftCut:gC,''', "cfg save")

# ---------- 2) 첫 화면 배너 ----------
patch('''  <div class="hgroup auc hauc" id="homeAucKinds">''',
      '''  <div class="giftwrap" id="giftBan" hidden></div>
  <div class="hgroup auc hauc" id="homeAucKinds">''', "home slot")
patch('''  renderUses();renderAlertHome();''', '''  renderUses();renderAlertHome();renderGiftBan();''', "home call")

# ---------- 3) 판매자: 상품 올릴 때 선물 포장 ----------
patch('''        <div class="field"><label for="sDesc">상품 설명</label><textarea id="sDesc" rows="3" placeholder="재배·채취 과정, 손질 방법, 보관법"></textarea></div>''',
'''        <div class="field"><label for="sDesc">상품 설명</label><textarea id="sDesc" rows="3" placeholder="재배·채취 과정, 손질 방법, 보관법"></textarea></div>
        <div class="row2 giftsell"><label style="display:flex;gap:8px;align-items:center;font-size:14px"><input type="checkbox" id="sGift"> 🎁 선물 포장 가능 (명절 선물 코너에 함께 보여요)</label>
          <div class="field"><label for="sGiftWrap">선물 포장비 (원, 무료면 0)</label><input id="sGiftWrap" type="number" min="0" max="50000" step="500" value="0" class="num"></div></div>''', "sell form")
patch('''desc:$("#sDesc").value.slice(0,1000),...proofFields(pNeedS,pRefS,sSiteId),''',
      '''desc:$("#sDesc").value.slice(0,1000),gift:!!$("#sGift")?.checked,giftWrap:wrapFee($("#sGiftWrap")?.value),...proofFields(pNeedS,pRefS,sSiteId),''', "sell add")

# 내 상품 목록에서 켜고 끄기
patch('''${p.cat!=="가공품"?`<button class="btn sm" data-act="dupP" data-id="${p.id}">이걸로 하나 더</button>`:""}<button class="btn sm danger" data-act="delP" data-id="${p.id}">삭제</button></div>''',
'''${p.cat!=="가공품"?`<button class="btn sm" data-act="dupP" data-id="${p.id}">이걸로 하나 더</button>`:""}<button class="btn sm danger" data-act="delP" data-id="${p.id}">삭제</button></div>
    <div class="actions"><span class="meta">🎁 선물 포장 ${p.gift?`<b>가능</b>${p.giftWrap?` · 포장비 ${won(p.giftWrap)}`:" · 무료"}`:"안 함"}</span><input id="gw-${p.id}" type="number" min="0" max="50000" step="500" value="${p.giftWrap||0}" aria-label="선물 포장비" style="max-width:90px" class="num"><button class="btn sm" data-act="giftP" data-id="${p.id}">${p.gift?"포장비 저장":"선물 포장 켜기"}</button>${p.gift?`<button class="btn sm" data-act="giftOff" data-id="${p.id}">끄기</button>`:""}</div>''', "my items")

patch('''  async pause(id){''', '''  async giftP(id){await guard(()=>S.db.doc("products/"+id).update({gift:true,giftWrap:wrapFee($("#gw-"+id)?.value)}),"선물 포장 가능으로 표시했습니다. 명절 선물 코너에 함께 보입니다")},
  async giftOff(id){await guard(()=>S.db.doc("products/"+id).update({gift:false}),"선물 포장 표시를 껐습니다")},
  async pause(id){''', "act gift")

# ---------- 4) 판매자 주문: 선물 안내 ----------
patch('''    ${o.memo?`<div class="meta">배송 메모: ${esc(o.memo)}</div>`:""}
    ${ordRate(o)<FEE''', '''    ${o.memo?`<div class="meta">배송 메모: ${esc(o.memo)}</div>`:""}
    ${giftNote(o)}
    ${ordRate(o)<FEE''', "seller order gift")
patch('''${day(o.createdAt)}${o.fromQuote?" · 견적 주문":""}</div>''',
      '''${day(o.createdAt)}${o.fromQuote?" · 견적 주문":""}${o.gift?" · 🎁 선물":""}</div>''', "buyer order gift")

# ---------- 5) 상품 상세: 선물 옵션 + 운영자 고르기 ----------
patch('''<dt>배송</dt><dd>${won(ship)}</dd><dt>재고</dt>''',
      '''<dt>배송</dt><dd>${won(ship)}</dd>${p.gift?`<dt>선물 포장</dt><dd>가능 · ${p.giftWrap?won(p.giftWrap):"무료"}</dd>`:""}<dt>재고</dt>''', "spec gift")
patch('''    ${p.stock>0&&!own?`<div class="field"><label for="oMemo">배송 메모</label><input id="oMemo" placeholder="받는 분과 요청 사항 (실제 주소는 넣지 마세요)"></div>`''',
'''    ${S.owner?`<div class="actions"><button class="btn sm gold" type="button" id="gPick">${inGift(p)?"🎁 선물 코너에서 빼기":"🎁 선물 코너에 넣기"}</button></div>`:""}
    ${p.stock>0&&!own?`<div class="field"><label for="oMemo">배송 메모</label><input id="oMemo" placeholder="받는 분과 요청 사항 (실제 주소는 넣지 마세요)"></div>`+giftOptHTML(p)''', "detail gift opt")
patch('''   <div class="thumb">${thumbHTML(p,"pid")}</div>
   <div class="dinfo">''', '''   ${backGift}<div class="thumb">${thumbHTML(p,"pid")}</div>
   <div class="dinfo">''', "detail back")
patch('''  let qty=1;const ship=p.form==="생물"?5000:3500,own=p.sellerId===S.uid,dlg=$("#dlg");''',
      '''  let qty=1;const ship=p.form==="생물"?5000:3500,own=p.sellerId===S.uid,dlg=$("#dlg");
  const backGift=S.fromGift?`<button class="btn sm" type="button" data-gift="${esc(S.fromGift)}" style="margin-bottom:8px">← 선물 코너로</button>`:"",gMode=!!S.fromGift;S.fromGift=null;''', "detail vars")
patch('''    const upd=()=>{$("#qv").textContent=qty;$("#tot").textContent=won(p.price*qty+ship)};upd();''',
      '''    const wf=()=>$("#gOpt")?.open&&$("#gWrap")?.checked?(p.giftWrap||0):0;
    const upd=()=>{$("#qv").textContent=qty;$("#tot").textContent=won(p.price*qty+ship+wf())};upd();
    if($("#gOpt")){if(gMode)$("#gOpt").open=true;$("#gOpt").addEventListener("toggle",upd);$("#gWrap")&&($("#gWrap").onchange=upd);upd()}''', "detail upd")
patch('''        await S.db.collection("orders").add({productId:p.id,productName:p.name,unit:p.unit,qty,unitPrice:p.price,ship,total:p.price*qty+ship,buyerId:S.uid,sellerId:p.sellerId,memo:$("#oMemo").value.slice(0,300),status:"결제완료",createdAt:Date.now()});''',
      '''        const gf=$("#gOpt")?.open?{card:$("#gCard").value.trim().slice(0,60),date:$("#gDate").value||"",wrap:!!$("#gWrap")?.checked,wrapFee:wf(),hidePrice:$("#gHide").checked}:null;
        await S.db.collection("orders").add({productId:p.id,productName:p.name,unit:p.unit,qty,unitPrice:p.price,ship,total:p.price*qty+ship+wf(),buyerId:S.uid,sellerId:p.sellerId,memo:$("#oMemo").value.slice(0,300),...(gf?{gift:gf}:{}),status:"결제완료",createdAt:Date.now()});''', "order add")
patch('''  dlg.querySelector(".close").onclick=()=>dlg.close();
  if($("#buy")){''', '''  dlg.querySelector(".close").onclick=()=>dlg.close();
  if($("#gPick"))$("#gPick").onclick=()=>giftToggle(p);
  if($("#buy")){''', "detail pick")

# ---------- 6) 클릭 연결 ----------
patch('''  const xp=e.target.closest("[data-xp]");if(xp){openProduct(xp.dataset.xp);return}''',
'''  const gf=e.target.closest("[data-gift]");if(gf){openGift(gf.dataset.gift);return}
  const gb=e.target.closest("[data-gift-bulk]");if(gb){if($("#dlg").open)$("#dlg").close();go("request");toast("수량이 많은 선물은 요청서 메모에 ‘선물용 · 받는 곳 ○군데 · 포장 원함’처럼 적어 주세요. 견적은 무료입니다");return}
  const gp=e.target.closest("[data-gpre]");if(gp){giftPreset(gp.dataset.gpre);return}
  const xp=e.target.closest("[data-xp]");if(xp){openProduct(xp.dataset.xp);return}''', "click")

# ---------- 7) 함수 ----------
FN = r'''
/* ---------- 명절 선물 코너 ---------- */
const wrapFee=v=>Math.max(0,Math.min(50000,Math.round((+v||0)/100)*100));
const kstDay=()=>new Date(Date.now()+9*3600e3).toISOString().slice(0,10);
const giftCfg=()=>{const s=S.site||{};return {on:!!s.giftOn,title:s.giftTitle||"명절 선물",start:s.giftStart||"",end:s.giftEnd||"",cut:s.giftCut||"",ids:Array.isArray(s.giftIds)?s.giftIds:[],hide:Array.isArray(s.giftHide)?s.giftHide:[]}};
const giftLive=()=>{const g=giftCfg(),t=kstDay();return g.on&&g.start&&g.end&&g.start<=t&&t<=g.end};
const inGift=p=>{const g=giftCfg();return g.ids.includes(p.id)||(!!p.gift&&!g.hide.includes(p.id))};
const giftList=()=>{const g=giftCfg();return live().filter(p=>p.stock>0&&inGift(p)).sort((a,b)=>(g.ids.includes(b.id)-g.ids.includes(a.id))||a.price-b.price)};
const GTIERS=[["all","전체",0,Infinity],["t1","5만 원 이하",0,50000],["t2","5~15만 원",50001,150000],["t3","15~30만 원",150001,300000],["t4","30만 원 이상",300001,Infinity]];
const mdKo=d=>{const [,m,dd]=String(d).split("-");return `${+m}월 ${+dd}일`};
function giftCutText(){const g=giftCfg();if(!g.cut)return "";return kstDay()<=g.cut?`${mdKo(g.cut)}까지 주문하면 제때 받아요`:"택배 마감이 지났어요 · 도착이 늦을 수 있어요"}
function giftTag(p){const t=p.price<=150000?'<span class="chip ok">선물 한도 15만 원 안</span>':p.price<=300000?'<span class="chip gold">명절 기간 한도 30만 원 안</span>':'<span class="chip">프리미엄</span>';
  return `<div class="gtag">${t}${p.gift?`<span class="chip">🎁 포장${p.giftWrap?" +"+won(p.giftWrap):" 무료"}</span>`:""}</div>`}
function renderGiftBan(){const el=$("#giftBan");if(!el)return;const g=giftCfg(),lv=giftLive(),pre=!lv&&S.owner&&g.on;
  if(!lv&&!pre){el.hidden=true;el.innerHTML="";return}
  const n=giftList().length,ct=giftCutText();el.hidden=false;
  el.innerHTML=`<button class="giftban" type="button" data-gift="all"><span class="gi" aria-hidden="true">🎁</span><span class="gt"><b>${esc(g.title)} 코너${pre?' <span class="chip">미리보기 · 손님에겐 아직 안 보임</span>':""}</b><span>${n?`${n}가지 · 마음 전하는 실속 선물부터 귀한 산양삼까지`:"선물 상품을 모으고 있어요"}${ct?` · <em>${esc(ct)}</em>`:""}</span></span><span class="go">보러 가기 →</span></button>
  <div class="gtiers" role="list">${GTIERS.slice(1).map(([k,l])=>`<button type="button" role="listitem" data-gift="${k}">${l}</button>`).join("")}<button type="button" data-gift-bulk="1">🏢 회사·단체 대량</button></div>`}
function openGift(tier){const g=giftCfg(),T=GTIERS.find(x=>x[0]===tier)||GTIERS[0],dlg=$("#dlg");openA=null;
  const all=giftList(),list=all.filter(p=>p.price>=T[2]&&p.price<=T[3]),ct=giftCutText();
  dlg.innerHTML=`<div class="dlg giftdlg"><button class="close" aria-label="닫기" type="button">×</button>
   <div class="eyebrow">농부와 심마니 직거래 · 채취 근거 확인 상품</div><h2 style="font-size:24px;margin:2px 0 6px">🎁 ${esc(g.title)}</h2>
   ${ct?`<div class="notice" style="margin:0 0 10px">📦 ${esc(ct)}${g.cut&&kstDay()<=g.cut?" · 받는 날을 고르면 판매자가 날짜에 맞춰 보냅니다":""}</div>`:""}
   <div class="gtiers" role="tablist">${GTIERS.map(([k,l])=>`<button type="button" role="tab" data-gift="${k}" aria-pressed="${k===T[0]}">${l}${k==="all"?"":` <small class="num">${all.filter(p=>p.price>=GTIERS.find(x=>x[0]===k)[2]&&p.price<=GTIERS.find(x=>x[0]===k)[3]).length}</small>`}</button>`).join("")}</div>
   <div class="grid hrow0 giftgrid" style="margin-top:12px">${list.length?list.map(p=>card(p).replace('<div class="cbody">','<div class="cbody">'+giftTag(p))).join(""):emptyBox(all.length?"이 가격대 선물이 아직 없습니다. 다른 가격대를 눌러 보세요.":"선물 상품을 모으고 있어요. 입고되면 이 코너에 보입니다.","")}</div>
   <div class="actions" style="margin-top:14px"><button class="btn gold" type="button" data-go="auction">🏔 귀한 산삼은 경매에서</button><button class="btn" type="button" data-gift-bulk="1">🏢 회사·단체 대량 주문 (견적 무료)</button></div>
   <p class="meta" style="margin:12px 0 0;line-height:1.6">‘한도 안’ 표시는 공무원·교사·언론인 등에게 보낼 때 참고하시라고 붙였습니다. 청탁금지법상 농수산물·농수산가공품 선물은 평소 15만 원, 설·추석 기간에는 30만 원까지입니다 (상품 1개 값 기준 · 배송비·포장비 제외). 정확한 적용은 국민권익위원회에 확인해 주세요.</p></div>`;
  dlg.querySelector(".close").onclick=()=>dlg.close();
  dlg.querySelectorAll(".card").forEach(c=>c.addEventListener("click",()=>{S.fromGift=T[0]},true));
  if(!dlg.open)dlg.showModal();dlg.scrollTop=0;requestAnimationFrame(paintAll)}
function giftOptHTML(p){const tm=new Date(Date.now()+9*3600e3+2*864e5).toISOString().slice(0,10);
  return `<details class="giftopt" id="gOpt"><summary>🎁 선물로 보내기</summary>
   <div class="field"><label for="gCard">카드 문구 (60자까지)</label><input id="gCard" maxlength="60" placeholder="예: 새해 복 많이 받으세요. 늘 건강하세요"></div>
   <div class="row2"><div class="field"><label for="gDate">받고 싶은 날 (선택)</label><input id="gDate" type="date" min="${tm}"></div>
   <div class="field">${p.gift?`<label style="display:flex;gap:8px;align-items:center;font-size:14px;margin-top:26px"><input type="checkbox" id="gWrap" checked> 선물 포장 ${p.giftWrap?"+"+won(p.giftWrap):"(무료)"}</label>`:`<p class="meta" style="margin-top:26px">이 상품은 선물 포장을 하지 않습니다</p>`}</div></div>
   <label style="display:flex;gap:8px;align-items:center;font-size:14px"><input type="checkbox" id="gHide" checked> 받는 분에게 가격이 안 보이게 (명세서 빼기)</label>
   <p class="meta" style="margin:6px 0 0">받는 분 이름·주소는 결제할 때 따로 적습니다. 주문자와 다른 곳으로 보낼 수 있어요.</p></details>`}
function giftNote(o){const g=o.gift;if(!g)return "";
  return `<div class="notice">🎁 <b>선물 주문</b>${g.wrap?` · 선물 포장${g.wrapFee?" ("+won(g.wrapFee)+")":""}`:""}${g.date?` · <b>${esc(mdKo(g.date))}</b> 도착 희망`:""}${g.hidePrice?" · <b>가격이 적힌 명세서를 넣지 마세요</b>":""}${g.card?`<br>카드 문구: “${esc(g.card)}”`:""}</div>`}
async function giftToggle(p){const g=giftCfg(),on=inGift(p);let ids=g.ids.filter(x=>x!==p.id),hide=g.hide.filter(x=>x!==p.id);
  if(on){if(p.gift)hide.push(p.id)}else ids.unshift(p.id);
  const v={giftIds:ids.slice(0,200),giftHide:hide.slice(0,200),updatedAt:Date.now()};
  if(await guard(()=>S.db.doc("settings/site").set({...(S.site||{}),...v}),on?"선물 코너에서 뺐습니다":"선물 코너에 넣었습니다")){S.site={...(S.site||{}),...v};$("#gPick")&&($("#gPick").textContent=inGift(p)?"🎁 선물 코너에서 빼기":"🎁 선물 코너에 넣기");render()}}
function giftCfgFill(){const g=giftCfg();if(!$("#cfgGift"))return;$("#cfgGift").checked=g.on;$("#cfgGiftTitle").value=(S.site||{}).giftTitle||"";$("#cfgGiftStart").value=g.start;$("#cfgGiftEnd").value=g.end;$("#cfgGiftCut").value=g.cut}
function giftPreset(k){const y=+kstDay().slice(0,4),P={ny:[`${y}년 연말·새해 선물`,`${y}-11-23`,`${y+1}-01-05`,`${y}-12-21`],seol27:["2027 설 선물","2027-01-11","2027-02-09","2027-02-01"]}[k];if(!P)return;
  $("#cfgGift").checked=true;$("#cfgGiftTitle").value=P[0];$("#cfgGiftStart").value=P[1];$("#cfgGiftEnd").value=P[2];$("#cfgGiftCut").value=P[3];toast("날짜를 채웠습니다. 확인하고 저장을 눌러 주세요")}
'''
patch('''function renderHome(){''', FN + '''function renderHome(){''', "fn")

CSS = '''.giftwrap{margin:6px 0 16px}
.giftban{display:flex;align-items:center;gap:12px;width:100%;text-align:left;border:1px solid var(--gold);background:linear-gradient(135deg,var(--gold-soft),var(--surface));border-radius:18px;padding:14px 16px;font:inherit;color:inherit;cursor:pointer}
.giftban .gi{font-size:32px;line-height:1}.giftban .gt{display:flex;flex-direction:column;gap:2px;min-width:0}.giftban b{font-family:var(--display);font-size:19px}
.giftban .gt>span{font-size:13.5px;color:var(--muted)}.giftban em{font-style:normal;color:var(--berry);font-weight:600}
.giftban .go{margin-left:auto;font-weight:700;color:var(--gold-deep);white-space:nowrap}
.gtiers{display:flex;gap:6px;overflow-x:auto;margin-top:8px;padding-bottom:2px;scrollbar-width:none}
.gtiers button{flex:none;border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:999px;padding:6px 12px;font:inherit;font-size:13.5px;cursor:pointer}
.gtiers button[aria-pressed="true"]{background:var(--gold);color:var(--gold-ink);border-color:var(--gold)}
.gtag{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:4px}.gtag .chip{font-size:11.5px}
.giftgrid{grid-template-columns:repeat(auto-fill,minmax(160px,1fr))}
.giftopt{border:1px solid var(--gold);border-radius:14px;padding:8px 12px;margin-top:8px;background:var(--gold-soft)}
.giftopt summary{cursor:pointer;font-weight:700;color:var(--gold-deep)}
.giftsell{align-items:end}
@media (max-width:700px){.giftban{padding:12px}.giftban .go{display:none}.giftban b{font-size:17px}}
'''
patch('.hask{display:flex;', CSS + '.hask{display:flex;', "css")
p.write_text(s, encoding="utf-8"); print("ok")
