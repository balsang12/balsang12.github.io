const { chromium } = require('playwright');const fs=require('fs'),path=require('path');
const fake=fs.readFileSync(path.join(__dirname,'fake_supabase.js'),'utf8'),mock=fs.readFileSync(path.join(__dirname,'../../app/mock_new.js'),'utf8');
let fails=0;const ok=(c,m)=>{console.log((c?'PASS ':'FAIL ')+m);if(!c)fails++};
const post=`(()=>{const D=window.__D;D.settings.site={beta:false};D.sellers.s1.ship={dry:3000,fresh:6000,free:50000,island:4000};D.sellers.s1.resp=[30,40,50];
 const f=k=>Object.keys(D.products).find(x=>D.products[x].name===k);window.__P1=f("자연산 곰취");window.__P2=f("마가목 열매");
 D.orders.old={productId:window.__P2,productName:"마가목 열매",unit:"500g",qty:1,unitPrice:32000,ship:3000,total:35000,buyerId:"late",sellerId:"s1",status:"결제완료",createdAt:Date.now()-6*864e5};})();`;
(async()=>{const b=await chromium.launch();
async function open(uid){const ctx=await b.newContext({viewport:{width:390,height:844},serviceWorkers:'block',locale:'ko-KR'});const p=await ctx.newPage();const errs=[];p.on('pageerror',e=>errs.push(String(e)));
 await p.route('**/vendor/supabase.js',r=>r.fulfill({contentType:'application/javascript',body:fake}));await p.addInitScript(`window.__SESSION={user:{id:"${uid}"}};\n`+mock+'\n'+post);await p.goto(process.argv[2]+'/app/');await p.waitForTimeout(1300);return {p,errs,ctx}}
let {p,errs,ctx}=await open('buyer');
// 기한 계산
const d=await p.evaluate(()=>{const T=s=>Date.parse(s);return [kDayLabel(shipDue(T("2026-10-22T10:00:00+09:00"),true)),kDayLabel(shipDue(T("2026-10-22T10:00:00+09:00"),false)),kDayLabel(shipDue(T("2026-10-20T10:00:00+09:00"),true)),kDayLabel(shipDue(T("2026-10-20T10:00:00+09:00"),false))]});
ok(JSON.stringify(d)==='["10월 26일(월)","10월 26일(월)","10월 26일(월)","10월 23일(금)"]','ship deadlines '+JSON.stringify(d));
await p.evaluate(()=>openProduct(window.__P1));await p.waitForTimeout(300);
{const tx=await p.locator('#dlg .spec').innerText();ok(tx.includes('6,000원')&&tx.includes('50,000원 이상 무료')&&tx.includes('4,000원')&&tx.includes('월~목'),'spec shows seller shipping: '+tx.split('\n').filter(x=>x.includes('원')).slice(-1))}
ok((await p.locator('#shipLbl').innerText()).includes('6,000원'),'fresh fee');
ok((await p.locator('#oFree').innerText()).includes('32,000원 더 담으면 무료배송'),'free-shipping hint');
await p.click('#plus');await p.click('#plus');ok((await p.locator('#shipLbl').innerText())==='무료배송','free at 54,000원');
await p.click('#minus');await p.click('#minus');await p.check('#oIsland');ok((await p.locator('#shipLbl').innerText()).includes('10,000원'),'island adds 4,000');
await p.screenshot({path:path.join(__dirname,'ship_buy.png')});
await p.check('#oAgree').catch(()=>{});await p.click('#buy');await p.waitForTimeout(800);
const o1=await p.evaluate(()=>window.__calls.filter(c=>c[0]==='upsert'&&c[1]==='orders').pop());
ok(o1&&o1[3].ship===10000&&o1[3].island===true&&o1[3].fresh===true&&o1[3].shipDue>Date.now(),'order 1 saved with ship/island/fresh/due');
await p.evaluate(()=>openProduct(window.__P2));await p.waitForTimeout(300);
ok(await p.locator('#oBundle').isVisible()&&(await p.locator('#oBundle').innerText()).includes('자연산 곰취'),'bundle notice');
ok((await p.locator('#shipLbl').innerText()).includes('묶음 배송'),'bundle ship 0: '+await p.locator('#shipLbl').innerText());
await p.screenshot({path:path.join(__dirname,'ship_bundle.png')});
await p.check('#oAgree').catch(()=>{});await p.click('#buy');await p.waitForTimeout(800);
const o2=await p.evaluate(()=>window.__calls.filter(c=>c[0]==='upsert'&&c[1]==='orders').pop());
ok(o2&&o2[3].ship===0&&o2[3].bundleWith===o1[2],'order 2 bundled with order 1');
await p.evaluate(()=>{go('my');renderMy()});await p.waitForTimeout(200);
ok((await p.locator('#myOrders').innerText()).includes('발송 예정'),'buyer sees ship-by date');
ok(errs.length===0,'no errors buyer '+errs.join('|'));await ctx.close();
// 판매자
({p,errs,ctx}=await open('s1'));
await p.evaluate(()=>go('seller'));await p.waitForTimeout(300);
{const tx=await p.locator('#sellerOrders').innerText();ok(tx.includes('발송 기한 지남'),'seller sees overdue');}
await p.screenshot({path:path.join(__dirname,'ship_seller.png'),fullPage:false});
ok(await p.inputValue('#shShipFresh')==='6000'&&await p.inputValue('#shFreeOver')==='50000','shop form shows shipping');
await p.fill('#shFreeOver','30000');await p.click('#shopForm button[type=submit]');await p.waitForTimeout(500);
const sv=await p.evaluate(()=>window.__calls.filter(c=>c[0]==='upsert'&&c[1]==='sellers'&&c[2]==='s1').pop());
ok(sv&&sv[3].ship.free===30000&&sv[3].ship.fresh===6000&&Array.isArray(sv[3].resp)&&sv[3].resp.length===3,'shop save keeps reply times and saves shipping '+JSON.stringify(sv&&{ship:sv[3].ship,resp:sv[3].resp}));
ok(errs.length===0,'no errors seller '+errs.join('|'));
// 판매자가 묶음 주문을 보는 화면 (손님 주문 2건 넣고)
await ctx.close();
({p,errs,ctx}=await open('s1'));
await p.evaluate(()=>{const n=Date.now();S.orders.push({id:"a1",productId:window.__P1,productName:"자연산 곰취",unit:"500g",qty:1,unitPrice:18000,ship:10000,island:true,fresh:true,total:28000,buyerId:"buyer",sellerId:"s1",status:"결제완료",createdAt:n-6e4,shipDue:shipDue(n,true)},{id:"a2",productId:window.__P2,productName:"마가목 열매",unit:"500g",qty:1,unitPrice:32000,ship:0,bundleWith:"a1",total:32000,buyerId:"buyer",sellerId:"s1",status:"결제완료",createdAt:n,shipDue:shipDue(n,false)});go('seller');renderSeller()});await p.waitForTimeout(300);
{const tx=await p.locator('#sellerOrders').innerText();ok(tx.includes('묶음 배송')&&tx.includes('생물')&&tx.includes('제주·도서산간'),'seller sees bundle + fresh + island notes')}
await p.locator('#sellerOrders .item').first().screenshot({path:path.join(__dirname,'ship_seller_order.png')});
ok(errs.length===0,'no errors seller 2 '+errs.join('|'));
await b.close();console.log(fails?fails+' FAILED':'ALL PASS');process.exit(fails?1:0)})();
