#!/usr/bin/env python3
"""v91: 후기 — 사진 후기, 판매자 답글, 별점 분포·사진 후기 모아보기, 경매 낙찰품 후기, 효능 문구 검사."""
import sys, pathlib, re
p = pathlib.Path(sys.argv[1]); s = p.read_text(encoding="utf-8")
def patch(old, new, label, count=1):
    global s
    n = s.count(old)
    if n != count: sys.exit(f"{label}: expected {count}, found {n}")
    s = s.replace(old, new)

# ---------- 후기 쓰기: 사진 3장, 효능 문구 검사, 경매 후기 ----------
i = s.index("function openReview(o){")
j = s.index("  dlg.showModal();", i) + len("  dlg.showModal();\n}")
s = s[:i] + r'''function openReview(o){
  let rating=5,photos=[];const dlg=$("#dlg");openA=null;
  dlg.innerHTML=`<form class="dinfo" id="revForm" style="position:relative"><button class="close" aria-label="닫기" type="button">×</button>
  <h2 style="font-size:22px">${esc(o.productName)} 후기</h2>
  <div class="rstars" id="stars">${[1,2,3,4,5].map(i=>`<button type="button" data-s="${i}" aria-label="${i}점">★</button>`).join("")}</div>
  <div class="field"><label for="revText">어땠나요?</label><textarea id="revText" rows="4" required placeholder="신선도, 손질 상태, 포장, 향과 맛"></textarea>
   <p class="meta" style="margin:4px 0 0">병이 나았다·혈압이 내렸다 같은 건강 효과는 적을 수 없어요. 상품 상태와 맛, 포장 이야기를 들려주세요.</p></div>
  <div class="field"><label for="revPh">사진 (선택, 3장까지)</label><input id="revPh" type="file" accept="image/*" multiple><div class="revthumbs" id="revPrev"></div></div>
  <button class="btn primary" type="submit">후기 올리기</button></form>`;
  const ps=()=>dlg.querySelectorAll("#stars button").forEach(b=>b.classList.toggle("on",+b.dataset.s<=rating));ps();
  dlg.querySelectorAll("#stars button").forEach(b=>b.onclick=()=>{rating=+b.dataset.s;ps()});
  dlg.querySelector(".close").onclick=()=>dlg.close();
  const prev=()=>{$("#revPrev").innerHTML=photos.map((u,i)=>`<span><img src="${u}" alt="후기 사진 ${i+1}"><button type="button" data-rmph="${i}" aria-label="사진 빼기">×</button></span>`).join("");$("#revPrev").querySelectorAll("[data-rmph]").forEach(b=>b.onclick=()=>{photos.splice(+b.dataset.rmph,1);prev()})};
  $("#revPh").onchange=async e=>{for(const f of [...e.target.files].slice(0,3-photos.length)){try{photos.push(await shrinkPhoto(f))}catch(_){toast("사진을 읽지 못했습니다. 다른 사진을 골라 주세요")}}e.target.value="";prev()};
  $("#revForm").onsubmit=async e=>{e.preventDefault();const text=$("#revText").value.trim();
    const hit=revClaim(text);if(hit){toast(`‘${hit}’ 같은 건강 효과 표현은 후기에 쓸 수 없어요. 상품 상태·맛·포장 이야기로 고쳐 주세요`);return}
    if(PII.test(text)){toast("전화번호·계좌·링크는 후기에 적을 수 없어요");return}
    if(await guard(()=>S.db.collection("reviews").add({productId:o.productId||null,orderId:o.id||null,...(o.auctionId?{auctionId:o.auctionId}:{}),buyerId:S.uid,sellerId:o.sellerId,rating,text:text.slice(0,1000),...(photos.length?{photos}:{}),createdAt:Date.now()}),"후기를 올렸습니다"))dlg.close()};
  dlg.showModal();
}''' + s[j:]

# ---------- 상품 화면 후기 목록 ----------
patch('''   <div class="bids"><h3 style="font-size:17px">구매 후기 ${rs.length}개</h3>${rs.length?rs.map(r=>`<div class="item sunk"><span class="star">${"★".repeat(r.rating)}${"☆".repeat(5-r.rating)}</span><div>${esc(r.text)}</div></div>`).join(""):'<div class="meta">수령 확인한 구매자만 후기를 쓸 수 있습니다.</div>'}</div>''',
      '''   <div class="bids" id="revBox">${revBoxHTML(rs,"all")}</div>''', "product reviews")
patch('''  if($("#gPick"))$("#gPick").onclick=()=>giftToggle(p);''',
      '''  if($("#gPick"))$("#gPick").onclick=()=>giftToggle(p);
  $("#revBox")?.addEventListener("click",ev=>{const f=ev.target.closest("[data-rvf]");if(f){$("#revBox").innerHTML=revBoxHTML(rs,f.dataset.rvf)}});''', "review filter bind")
# 판매자 프로필 받은 후기
patch('''${rv.length?`<div class="list">${rv.map(x=>`<div class="item sunk"><span class="star">${"★".repeat(x.rating)}${"☆".repeat(5-x.rating)}</span><div>${esc(x.text)}</div><div class="meta num">${day(x.createdAt)}</div></div>`).join("")}</div>`''',
      '''${rv.length?`<div class="list">${rv.map(x=>revItemHTML(x,true)).join("")}</div>`''', "profile reviews")
# 판매자 화면: 답글 기다리는 후기
patch('''  $("#sellerOrders").innerHTML=myO.length?sendPlanHTML(myO)''', '''  $("#sellerOrders").innerHTML=revTodoHTML()+(myO.length?sendPlanHTML(myO)''', "seller rev todo")
patch('''</div>`).join(""):`<div class="empty">아직 받은 주문이 없습니다.</div>`;''', '''</div>`).join(""):`<div class="empty">아직 받은 주문이 없습니다.</div>`);''', "seller orders close paren")
# 경매 낙찰품 후기
patch('''      else if(dd==="환불")act=`<div class="meta">판매자 책임으로 환불 처리되었습니다.</div>`;''',
      '''      else if(dd==="환불")act=`<div class="meta">판매자 책임으로 환불 처리되었습니다.</div>`;
      else if(["수령확인","정산완료"].includes(dd)&&!S.reviews.some(r=>r.auctionId===a.id))act=`<div class="actions"><button class="btn sm" data-act="reviewA" data-id="${a.id}">후기 쓰기</button></div>`;''', "auction review btn")
patch('''  review(id){openReview(S.orders.find(o=>o.id===id))},''',
      '''  review(id){openReview(S.orders.find(o=>o.id===id))},
  reviewA(id){const a=S.auctions.find(x=>x.id===id);if(a)openReview({auctionId:a.id,productName:a.title,sellerId:a.sellerId})},
  async replyR(id){const t=($("#rr-"+id)?.value||"").trim();if(!t){toast("답글을 적어 주세요");return}if(PII.test(t)){toast("전화번호·계좌·링크는 적을 수 없어요");return}const hit=revClaim(t);if(hit){toast(`‘${hit}’ 같은 건강 효과 표현은 답글에도 쓸 수 없어요`);return}
    await guard(()=>S.db.doc("reviews/"+id).update({reply:t.slice(0,500),replyAt:Date.now()}),"답글을 달았습니다")},''', "act reply")

FN = r'''
/* ---------- 후기: 사진·답글·분포·효능 문구 ---------- */
function revClaim(t){t=String(t||"");return CLAIMS.find(w=>t.includes(w))||CLAIMS_INTL.find(w=>t.toLowerCase().includes(w.toLowerCase()))||""}
function revItemHTML(r,showDate){const own=S.uid&&r.sellerId===S.uid,bad=!!revClaim(r.text);
  return `<div class="item sunk rv"><div class="itop"><span class="star">${"★".repeat(r.rating)}${"☆".repeat(5-r.rating)}</span>${showDate||true?`<span class="meta num">${day(r.createdAt)}${r.auctionId?" · 경매 낙찰":""}</span>`:""}</div>
   ${bad?'<div class="meta">건강 효과에 관한 표현이 있어 내용을 가렸어요.</div>':`<div>${esc(r.text)}</div>`}
   ${(r.photos||[]).length?`<div class="revthumbs">${r.photos.slice(0,3).map((u,i)=>`<img src="${esc(u)}" alt="후기 사진 ${i+1}" loading="lazy">`).join("")}</div>`:""}
   ${r.reply?`<div class="rvreply"><b>판매자 답글</b> ${esc(r.reply)}</div>`:own?`<div class="actions"><input id="rr-${esc(r.id)}" maxlength="500" placeholder="손님께 답글 달기" aria-label="답글"><button class="btn sm primary" data-act="replyR" data-id="${esc(r.id)}">답글 달기</button></div>`:""}</div>`}
function revBoxHTML(rs,f){if(!rs.length)return '<h3 style="font-size:17px">구매 후기 0개</h3><div class="meta">수령 확인한 구매자만 후기를 쓸 수 있습니다.</div>';
  const n=rs.length,avg=rs.reduce((a,b)=>a+b.rating,0)/n,ph=rs.filter(r=>(r.photos||[]).length),cnt=k=>rs.filter(r=>r.rating===k).length,list=f==="photo"?ph:rs;
  return `<h3 style="font-size:17px">구매 후기 ${n}개</h3>
   <div class="rvsum"><div class="rvavg"><b class="num">${avg.toFixed(1)}</b><span class="star">${"★".repeat(Math.round(avg))}${"☆".repeat(5-Math.round(avg))}</span></div>
    <div class="rvbars">${[5,4,3,2,1].map(k=>`<div><span>${k}점</span><i><b style="width:${Math.round(cnt(k)/n*100)}%"></b></i><span class="num">${cnt(k)}</span></div>`).join("")}</div></div>
   <div class="gtiers"><button type="button" data-rvf="all" aria-pressed="${f!=="photo"}">전체 ${n}</button><button type="button" data-rvf="photo" aria-pressed="${f==="photo"}">📷 사진 후기 ${ph.length}</button></div>
   ${list.length?list.map(r=>revItemHTML(r)).join(""):'<div class="meta">사진 후기가 아직 없어요.</div>'}`}
function revTodoHTML(){if(!S.uid)return "";const l=S.reviews.filter(r=>r.sellerId===S.uid&&!r.reply).sort((a,b)=>b.createdAt-a.createdAt);if(!l.length)return "";
  return `<div class="revtodo"><b>💬 답글을 기다리는 후기 ${l.length}개</b><p class="meta" style="margin:2px 0 6px">불만 후기에도 정중히 답하면 다른 손님의 믿음이 커져요. 후기는 지울 수 없고 답글만 달 수 있어요.</p>${l.slice(0,5).map(r=>`<div class="meta">‘${esc((S.products.find(x=>x.id===r.productId)||S.auctions.find(x=>x.id===r.auctionId)||{}).name||(S.auctions.find(x=>x.id===r.auctionId)||{}).title||"")}’</div>${revItemHTML(r)}`).join("")}</div>`}
'''
patch('''function sellerRow(uid,ctx){''', FN + '''function sellerRow(uid,ctx){''', "fn")

CSS = '''.revthumbs{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 0}.revthumbs img{width:76px;height:76px;object-fit:cover;border-radius:10px;background:var(--sunk)}
.revthumbs span{position:relative}.revthumbs span button{position:absolute;top:-6px;right:-6px;width:22px;height:22px;border-radius:50%;border:0;background:var(--ink);color:var(--surface);cursor:pointer;line-height:22px;padding:0}
.rvreply{margin-top:6px;padding:8px 10px;border-radius:10px;background:var(--pine-soft);font-size:14px}.rvreply b{color:var(--pine);margin-right:4px}
.rvsum{display:flex;gap:16px;align-items:center;margin:4px 0 8px}.rvavg{display:grid;justify-items:center}.rvavg b{font-size:30px;line-height:1.1}
.rvbars{flex:1;display:grid;gap:3px;font-size:12.5px;min-width:0}.rvbars div{display:grid;grid-template-columns:30px 1fr 24px;gap:6px;align-items:center}
.rvbars i{height:7px;border-radius:99px;background:var(--sunk);overflow:hidden}.rvbars i b{display:block;height:100%;background:var(--gold)}
.revtodo{border:1px solid var(--gold);background:var(--gold-soft);border-radius:12px;padding:10px 12px;margin:0 0 12px}
.rv .actions input{flex:1;min-width:0}
'''
patch('.hask{display:flex;', CSS + '.hask{display:flex;', "css")
p.write_text(s, encoding="utf-8"); print("ok")
