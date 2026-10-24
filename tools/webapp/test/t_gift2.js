const { chromium } = require('playwright');const fs=require('fs'),path=require('path');
const fake=fs.readFileSync(path.join(__dirname,'fake_supabase.js'),'utf8'),mock=fs.readFileSync(path.join(__dirname,'../../app/mock_new.js'),'utf8');
let fails=0;const ok=(c,m)=>{console.log((c?'PASS ':'FAIL ')+m);if(!c)fails++};
const K=t=>new Date(t+9*3600e3).toISOString().slice(0,10),today=K(Date.now()),later=K(Date.now()+20*864e5),past=K(Date.now()-5*864e5);
const post=`(()=>{const D=window.__D;D.settings.site={beta:false,giftOn:true,giftTitle:"연말·새해 선물",giftStart:"${past}",giftEnd:"${later}",giftCut:"${later}"};
 D.sellers.s1.bio="지리산 자락에서 30년째 약초를 캡니다.";
 D.products.set1={name:"지리산 더덕·도라지청 선물세트",item:"더덕",cat:"뿌리·줄기",price:89000,unit:"1세트",form:"건조",stock:8,region:"경남 산청",sellerId:"s1",grow:"자연산 (산에서 채취)",permit:"사유림 소유자 동의서",status:"판매중",proofOk:true,faq:{harv:"10월 20일 채취",keep:"서늘한 곳 6개월"},set:{items:["더덕 500g","도라지청 1병","오미자차 20포"],intro:"지리산에서 직접 캔 더덕과 집에서 담근 청을 담았습니다"},createdAt:Date.now()};
 const k=Object.keys(D.products).find(x=>D.products[x].name==="자연산 곰취");D.products[k].gift=true;window.__FR=k;})();`;
(async()=>{const b=await chromium.launch();
async function open(uid){const ctx=await b.newContext({viewport:{width:390,height:844},serviceWorkers:'block',locale:'ko-KR'});const p=await ctx.newPage();const errs=[];p.on('pageerror',e=>errs.push(String(e)));
 await p.route('**/vendor/supabase.js',r=>r.fulfill({contentType:'application/javascript',body:fake}));await p.addInitScript(`window.__SESSION={user:{id:"${uid}"}};\n`+mock+'\n'+post);await p.goto(process.argv[2]+'/app/');await p.waitForTimeout(1300);return {p,errs,ctx}}
let {p,errs,ctx}=await open('buyer');
{const r=await p.evaluate(()=>{window.__o=S.site;S.site={...S.site,giftCut:"2027-02-06"};const a=lastOrderDay({form:"생물"}),b=lastOrderDay({form:"건조"});
  const so=t=>kDayLabel(sendOn({gift:{date:"2027-02-01"},fresh:t,createdAt:Date.parse("2027-01-10T10:00:00+09:00")}));return [a,b,so(true),so(false)]});
 ok(JSON.stringify(r)==='["2027-02-04","2027-02-06","1월 28일(목)","1월 30일(토)"]','last-order day & send-on '+JSON.stringify(r));
 await p.evaluate(()=>{S.site=window.__o;render()})}
ok(await p.locator('#giftBan [data-gift="all|parents"]').isVisible(),'banner has recipient groups');
await p.click('#giftBan [data-gift="all|parents"]');await p.waitForTimeout(300);
{const tx=await p.locator('.giftdlg').innerText();ok(tx.includes('누구에게 보내세요')&&tx.includes('지리산 더덕·도라지청 선물세트'),'parents group shows set');ok(tx.includes('까지 주문하면 명절 전 도착'),'last-order tag on cards')}
ok(await p.locator('.giftdlg .card').first().innerText().then(t=>t.includes('선물세트')),'set listed first');
await p.screenshot({path:path.join(__dirname,'gift2_parents.png')});
await p.click('.giftdlg [data-gift="all|boss"]');await p.waitForTimeout(200);
{const n=await p.evaluate(()=>[...document.querySelectorAll('.giftdlg .card')].map(c=>S.products.find(x=>x.id===c.dataset.pid)).every(x=>x.price<=150000&&x.form!=="생물"));ok(n,'boss group: ≤15만 and keeps')}
await p.click('.giftdlg [data-gift="all|biz"]');await p.waitForTimeout(200);ok((await p.locator('.giftdlg').innerText()).includes('무료 견적 받기'),'biz group offers quote');
await p.click('.giftdlg [data-gift="all|parents"]');await p.waitForTimeout(200);
await p.locator('.giftdlg .card[data-pid="set1"]').click();await p.waitForTimeout(300);
{const tx=await p.locator('#dlg').innerText();ok(tx.includes('선물세트 구성')&&tx.includes('도라지청 1병'),'set box on product page');ok(tx.includes('명절 전에 도착해요'),'last-order note in gift options')}
ok(await p.locator('#dlg [data-gift="all|parents"]').count()===1,'back keeps group');
await p.fill('#gCard','새해 복 많이 받으세요');await p.fill('#gDate',await p.evaluate(()=>new Date(Date.now()+9*3600e3+10*864e5).toISOString().slice(0,10)));
await p.locator('#gOpt').scrollIntoViewIfNeeded();await p.screenshot({path:path.join(__dirname,'gift2_opt.png')});
await p.click('#buy');await p.waitForTimeout(800);
const od=await p.evaluate(()=>window.__calls.filter(c=>c[0]==='upsert'&&c[1]==='orders').pop());
ok(od&&od[3].gift&&od[3].gift.prodCard===true&&od[3].gift.date,'order has producer card + date');
ok(errs.length===0,'no errors buyer '+errs.join('|'));await ctx.close();
// 판매자
({p,errs,ctx}=await open('s1'));
await p.evaluate(o=>{S.orders.push({...o,id:"g1"});go('seller');renderSeller()},od[3]);await p.waitForTimeout(300);
{const tx=await p.locator('#sellerOrders').innerText();ok(tx.includes('보낼 날짜별'),'send plan summary');ok(tx.includes('에 보내 주세요 (받는 날'),'send-on instruction')}
await p.locator('#sellerOrders').screenshot({path:path.join(__dirname,'gift2_seller.png')});
await p.click('[data-pcard="g1"]');await p.waitForTimeout(300);
{const tx=await p.locator('#pcard').innerText();ok(tx.includes('지리산 박씨네')&&tx.includes('30년째')&&tx.includes('10월 20일 채취')&&tx.includes('채취 근거 확인')&&tx.includes('새해 복'),'producer card content')}
await p.locator('#pcard').screenshot({path:path.join(__dirname,'gift2_card.png')});
await p.keyboard.press('Escape');
const mp=await p.evaluate(()=>S.products.find(x=>x.sellerId==='s1'&&x.status==='판매중'&&!x.set).id);
await p.evaluate(id=>{const d=document.querySelector(`[data-act="setP"][data-id="${id}"]`).closest('details');d.open=true},mp);
await p.fill('#msItems-'+mp,'곰취 500g\n참나물 300g');await p.click(`[data-act="setP"][data-id="${mp}"]`);await p.waitForTimeout(500);
ok(await p.evaluate(id=>JSON.stringify(S.products.find(x=>x.id===id).set),mp)==='{"items":["곰취 500g","참나물 300g"],"intro":""}','seller makes a set from my items');
ok(errs.length===0,'no errors seller '+errs.join('|'));
await b.close();console.log(fails?fails+' FAILED':'ALL PASS');process.exit(fails?1:0)})();
