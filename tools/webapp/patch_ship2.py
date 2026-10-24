#!/usr/bin/env python3
"""v87: 배송 — 판매자 배송비 설정(생물/건조·무료 기준·도서산간), 묶음 배송, 발송 기한, 생물 월~목 발송·포장 기준, 상함 신고 안내."""
import sys, pathlib
p = pathlib.Path(sys.argv[1]); s = p.read_text(encoding="utf-8")
def patch(old, new, label, count=1):
    global s
    n = s.count(old)
    if n != count: sys.exit(f"{label}: expected {count}, found {n}")
    s = s.replace(old, new)

# ---------- 1) 상점 정보: 배송비 ----------
patch('''        <div class="field"><label for="shBiz">사업자등록 (선택)</label>''',
'''        <fieldset class="shipset"><legend>배송비</legend>
          <div class="row2"><div class="field"><label for="shShipDry">건조·가공품 배송비 (원)</label><input id="shShipDry" type="number" min="0" max="30000" step="500" class="num" placeholder="3500"></div>
          <div class="field"><label for="shShipFresh">생물 배송비 (아이스박스 포함, 원)</label><input id="shShipFresh" type="number" min="0" max="30000" step="500" class="num" placeholder="5000"></div></div>
          <div class="row2"><div class="field"><label for="shFreeOver">이 금액 이상이면 무료배송 (원, 없으면 0)</label><input id="shFreeOver" type="number" min="0" step="1000" class="num" placeholder="0"></div>
          <div class="field"><label for="shIsland">제주·도서산간 추가 (원)</label><input id="shIsland" type="number" min="0" max="30000" step="500" class="num" placeholder="3000"></div></div>
          <p class="meta" style="margin:0">같은 손님이 이틀 안에 내 상품을 더 사면 배송비는 한 번만 받고 한 상자로 묶어 보냅니다.</p></fieldset>
        <div class="field"><label for="shBiz">사업자등록 (선택)</label>''', "shop html")
patch('''$("#shBiz").value=me.biz||""}''', '''$("#shBiz").value=me.biz||"";const sc=shipCfg(S.uid);$("#shShipDry").value=sc.dry;$("#shShipFresh").value=sc.fresh;$("#shFreeOver").value=sc.free;$("#shIsland").value=sc.island}''', "shop fill")
# 저장할 때 기존 값(답변 시간 등)을 지우지 않도록 합쳐서 저장
patch('''guard(()=>S.db.doc("sellers/"+S.uid).set({shopName:$("#shName").value.trim().slice(0,40),''',
      '''const cl=(id,d)=>{const v=$("#"+id).value;return v===""?d:Math.max(0,Math.min(id==="shFreeOver"?10000000:30000,Math.round(+v/100)*100||0))};
  const shipC={dry:cl("shShipDry",3500),fresh:cl("shShipFresh",5000),free:cl("shFreeOver",0),island:cl("shIsland",3000)};
  const {id:_omit,...prev}=S.sellers[S.uid]||{};
  guard(()=>S.db.doc("sellers/"+S.uid).set({...prev,ship:shipC,shopName:$("#shName").value.trim().slice(0,40),''', "shop save")

# ---------- 2) 상품 등록: 생물 포장 안내 ----------
patch('''          <div class="field"><label for="sForm">형태</label><select id="sForm"><option>생물</option><option>건조</option><option>덖음·차</option></select></div>''',
      '''          <div class="field"><label for="sForm">형태</label><select id="sForm"><option>생물</option><option>건조</option><option>덖음·차</option></select><p class="meta freshtip" style="margin:4px 0 0">🧊 생물은 아이스박스·아이스팩으로, 물기를 빼서 포장하고 <b>월~목에만</b> 보내 주세요.</p></div>''', "form tip")

# ---------- 3) 상품 화면: 배송비 계산 ----------
patch('''  let qty=1;const ship=p.form==="생물"?5000:3500,own=p.sellerId===S.uid,dlg=$("#dlg");''',
      '''  let qty=1,ship=shipCalc(p,1,{}).ship;const own=p.sellerId===S.uid,dlg=$("#dlg");''', "detail ship var")
patch('''<dt>배송</dt><dd>${won(ship)}</dd>''', '''<dt>배송</dt><dd>${shipSpec(p)}</dd>''', "spec ship")
patch('''<span class="meta" style="white-space:nowrap">배송비 ${won(ship)} 포함</span>''', '''<span class="meta" style="white-space:nowrap" id="shipLbl">배송비 ${won(ship)} 포함</span>''', "ship label")
patch('''<input id="oMemo" placeholder="받는 분과 요청 사항 (실제 주소는 넣지 마세요)"></div>`+giftOptHTML(p)''',
      '''<input id="oMemo" placeholder="받는 분과 요청 사항 (실제 주소는 넣지 마세요)"></div>`+shipOptHTML(p)+giftOptHTML(p)''', "ship opt")
patch('''    const upd=()=>{$("#qv").textContent=qty;$("#tot").textContent=won(p.price*qty+ship+wf())};upd();''',
      '''    let sc={};const upd=()=>{sc=shipCalc(p,qty,{island:$("#oIsland")?.checked,gift:!!$("#gOpt")?.open});ship=sc.ship;$("#qv").textContent=qty;$("#tot").textContent=won(p.price*qty+ship+wf());
      $("#shipLbl").textContent=ship?`배송비 ${won(ship)} 포함`:sc.bundle?"묶음 배송 · 배송비 0원":"무료배송";
      const bn=$("#oBundle");if(bn){bn.hidden=!sc.bundle;if(sc.bundle)bn.innerHTML=`🚚 이틀 안에 주문한 <b>${esc(sc.bundle.productName)}</b>과 한 상자로 묶어 보내요. 배송비는 ${sc.ship?won(sc.ship)+"만 더":"더 내지 않아도"} 돼요.`}
      const fr=$("#oFree");if(fr){fr.hidden=!(sc.freeLeft>0);if(sc.freeLeft>0)fr.textContent=`${won(sc.freeLeft)} 더 담으면 무료배송`}};upd();
    $("#oIsland")&&($("#oIsland").onchange=upd);''', "upd ship")
patch('''ship,total:p.price*qty+ship+wf(),buyerId:S.uid,sellerId:p.sellerId,memo:$("#oMemo").value.slice(0,300),...(gf?{gift:gf}:{}),status:"결제완료",createdAt:Date.now()});''',
      '''ship,total:p.price*qty+ship+wf(),buyerId:S.uid,sellerId:p.sellerId,memo:$("#oMemo").value.slice(0,300),...(gf?{gift:gf}:{}),...(sc.island?{island:true}:{}),...(sc.bundle?{bundleWith:sc.bundle.bundleWith||sc.bundle.id}:{}),fresh:p.form==="생물",shipDue:shipDue(Date.now(),p.form==="생물"),status:"결제완료",createdAt:Date.now()});''', "order add")

# ---------- 4) 판매자 주문: 기한·묶음·생물 안내 ----------
patch('''    ${giftNote(o)}
    ${ordRate(o)<FEE''', '''    ${giftNote(o)}${shipNoteSeller(o)}
    ${ordRate(o)<FEE''', "seller notes")
# ---------- 5) 손님 주문: 기한·상함 신고 ----------
patch('''    ${OSTEPS.includes(ordEff(o))?flow(ordEff(o)):""}${o.status==="분쟁"?''',
      '''    ${OSTEPS.includes(ordEff(o))?flow(ordEff(o)):""}${shipNoteBuyer(o)}${o.status==="분쟁"?''', "buyer notes")

FN = r'''
/* ---------- 배송: 판매자 배송비 · 묶음 배송 · 발송 기한 ---------- */
function shipCfg(uid){const c=(S.sellers[uid]||{}).ship||{},n=(v,d)=>Number.isFinite(+v)&&v!==""&&v!=null?+v:d;return {dry:n(c.dry,3500),fresh:n(c.fresh,5000),free:n(c.free,0),island:n(c.island,3000)}}
const BUNDLE_MS=48*3600e3;
function bundleRoot(p){if(!S.uid)return null;return S.orders.filter(o=>o.buyerId===S.uid&&o.sellerId===p.sellerId&&o.status==="결제완료"&&!o.gift&&Date.now()-o.createdAt<BUNDLE_MS).sort((a,b)=>a.createdAt-b.createdAt)[0]||null}
function shipCalc(p,qty,o){const c=shipCfg(p.sellerId),base=p.form==="생물"?c.fresh:c.dry,sub=p.price*qty;
  const free=c.free>0&&sub>=c.free,freeLeft=c.free>0&&!free?c.free-sub:0;let ship=free?0:base,bundle=null;
  if(!o.gift){const r=bundleRoot(p);if(r){const root=r.bundleWith?S.orders.find(x=>x.id===r.bundleWith)||r:r,grp=S.orders.filter(x=>x.id===root.id||x.bundleWith===root.id);
    const paid=grp.reduce((t,x)=>t+(x.ship||0)-(x.island?c.island:0),0);ship=Math.max(0,ship-paid);bundle={...r,bundleWith:root.id,productName:root.productName};
    if(o.island&&!grp.some(x=>x.island))ship+=c.island;return {ship,bundle,island:!!o.island&&!grp.some(x=>x.island),freeLeft:0}}}
  if(o.island)ship+=c.island;return {ship,bundle,island:!!o.island,freeLeft}}
function shipSpec(p){const c=shipCfg(p.sellerId),b=p.form==="생물"?c.fresh:c.dry;
  return `${p.form==="생물"?"아이스박스 · ":""}${b?won(b):"무료"}${c.free>0&&b?` · ${won(c.free)} 이상 무료`:""}${c.island?` · 제주·도서산간 +${won(c.island)}`:""}${p.form==="생물"?"<br><span class=\"meta\">생물은 월~목에 발송해요</span>":""}`}
function shipOptHTML(p){const c=shipCfg(p.sellerId);return `<div id="oBundle" class="notice" hidden></div><p class="meta" id="oFree" hidden style="margin:4px 0"></p>${c.island?`<label class="ochk"><input type="checkbox" id="oIsland"> 제주·도서산간으로 받아요 (+${won(c.island)})</label>`:""}`}
const kWD=t=>new Date(t+9*3600e3).getUTCDay();
function kDayEnd(t){const d=new Date(t+9*3600e3);d.setUTCHours(23,59,0,0);return d.getTime()-9*3600e3}
function shipDue(t,fresh){let d=t+3*864e5;while((fresh?[5,6,0]:[0]).includes(kWD(d)))d+=864e5;return kDayEnd(d)}
const ordDue=o=>o.shipDue||shipDue(o.createdAt,o.fresh);
const kDayLabel=t=>{const d=new Date(t+9*3600e3);return `${d.getUTCMonth()+1}월 ${d.getUTCDate()}일(${"일월화수목금토"[d.getUTCDay()]})`};
function shipNoteSeller(o){if(o.status!=="결제완료")return "";const due=ordDue(o),late=Date.now()>due,wd=kWD(Date.now()),grp=o.bundleWith?S.orders.find(x=>x.id===o.bundleWith):S.orders.find(x=>x.bundleWith===o.id);
  return `<div class="shipnote">${late?`<span class="chip hot">발송 기한 지남</span> 손님이 바로 취소할 수 있어요. 오늘 꼭 보내 주세요.`:`📦 <b>${kDayLabel(due)}까지</b> 보내 주세요.`}
   ${grp?`<br>🚚 <b>묶음 배송</b> · ‘${esc(grp.productName)}’ 주문과 한 상자로 보내고, 송장번호도 같은 번호를 넣어 주세요.`:""}${o.island?"<br>🏝 제주·도서산간 배송입니다.":""}
   ${o.fresh?`<br>🧊 생물: 아이스박스·아이스팩, 물기 빼서 포장${[5,6,0].includes(wd)?" · <b>오늘은 보내지 말고 월요일에 보내 주세요</b> (주말 택배 창고에서 상할 수 있어요)":" · 월~목에만 발송"}`:""}</div>`}
function shipNoteBuyer(o){const e=ordEff(o);
  if(o.status==="결제완료"){const due=ordDue(o);return `<div class="meta">${Date.now()>due?`<span class="chip hot">발송 기한 지남</span> 판매자가 기한 안에 보내지 않았어요. 아래에서 바로 취소할 수 있어요.`:`${kDayLabel(due)}까지 발송 예정${o.fresh?" (생물은 월~목 발송)":""}`}${o.bundleWith?" · 앞 주문과 묶음 배송":""}</div>`}
  if(e==="발송완료"&&o.fresh)return `<div class="meta">🧊 생물은 받은 뒤 <b>24시간 안에</b> 상태를 확인해 주세요. 상했으면 사진을 찍어 두고 아래 ‘문제 신고’로 알려 주세요.</div>`;return ""}
'''
patch('''function sellerRow(uid,ctx){''', FN + '''function sellerRow(uid,ctx){''', "fn")

CSS = '''.shipset{border:1px solid var(--line);border-radius:12px;padding:8px 12px 10px;margin:4px 0 10px}.shipset legend{font-weight:700;padding:0 4px}
.ochk{display:flex;gap:8px;align-items:center;font-size:14px;margin:6px 0}.ochk input{width:18px;height:18px;flex:none;margin:0}
.shipnote{font-size:13.5px;line-height:1.6;background:var(--sunk);border-radius:10px;padding:8px 10px;margin:6px 0}
'''
patch('.hask{display:flex;', CSS + '.hask{display:flex;', "css")
p.write_text(s, encoding="utf-8"); print("ok")
