const { chromium } = require('playwright');const fs=require('fs'),path=require('path');
const fake=fs.readFileSync(path.join(__dirname,'fake_supabase.js'),'utf8');
let fails=0;const ok=(c,m)=>{console.log((c?'PASS ':'FAIL ')+m);if(!c)fails++};
const now=Date.now();
const D=(beta)=>`window.__D=${JSON.stringify({
 settings:{site:{beta}},sellers:{s1:{shopName:"지리산 박씨네"}},
 auctions:{
  a1:{title:"지리산 자연산 산삼 1뿌리",cat:"산삼",item:"산삼",grow:"자연산 (산에서 채취)",weight:"1뿌리 18g",form:"생물",region:"경남 산청",date:"2026-10-01",permit:"사유림 소유자 동의서",start:1000000,buyNow:0,status:"진행중",endsAt:now+2*864e5,sellerId:"s1",proofOk:true,photo:"",createdAt:now},
  a2:{title:"천마 1kg",titleEn:"Gastrodia tuber 1 kg",titleZh:"天麻 1公斤",cat:"천마",item:"천마",grow:"재배",weight:"1kg",form:"생물",region:"강원 인제",permit:"본인 소유 임야·재배",start:50000,status:"진행중",endsAt:now+3600e3,sellerId:"s1",createdAt:now},
  a3:{title:"마감된 산양삼",cat:"산양삼",item:"산양삼",grow:"재배",weight:"10뿌리",region:"전남 화순",permit:"본인 소유 임야·재배",start:200000,status:"진행중",endsAt:now-864e5,sellerId:"s1",createdAt:now}},
 products:{p1:{name:"자연산 고사리 말린것",item:"고사리",cat:"산나물",form:"건조",unit:"500g",price:30000,stock:5,region:"강원 정선",grow:"자연산 (산에서 채취)",permit:"사유림 소유자 동의서",status:"판매중",sellerId:"s1",createdAt:now},
  p2:{name:"오미자청",item:"오미자",cat:"가공품",form:"청",unit:"1병",price:25000,stock:0,region:"경북 문경",grow:"재배 (인증 없음)",status:"판매중",sellerId:"s1",proc:{ingr:"오미자, 설탕",vol:"500ml",shelf:"제조일로부터 1년"},createdAt:now}},
 orders:{o1:{productId:"p1",productName:"자연산 고사리 말린것",unit:"500g",qty:1,total:35000,buyerId:"me",sellerId:"s1",status:"발송완료",courier:"CJ",tracking:"123",createdAt:now}},
 bids:{b1:{auctionId:"a1",bidderId:"x",amount:1000000,t:now-1000},b2:{auctionId:"a3",bidderId:"x",amount:250000,t:now-2*864e5}}})};`;
(async()=>{const b=await chromium.launch();
async function open(pre,url){const ctx=await b.newContext({viewport:{width:390,height:844},serviceWorkers:'block',locale:'en-US'});const p=await ctx.newPage();const errs=[];
 p.on('pageerror',e=>errs.push(String(e)));p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
 await p.route('**/vendor/supabase.js',r=>r.fulfill({contentType:'application/javascript',body:fake}));
 await p.route('https://fonts.googleapis.com/**',r=>r.fulfill({contentType:'text/css',body:''}));
 await p.addInitScript(pre);await p.goto(process.argv[2]+url);await p.waitForTimeout(1200);return {p,errs,ctx}}
let {p,errs,ctx}=await open('window.__SESSION=null;'+D(true),'/app/global.html?lang=en');
await p.screenshot({path:'g_en.png',fullPage:true});
ok((await p.locator('#h1').innerText()).includes('Wild mountain ginseng'),'english heading');
ok(await p.locator('#list .card').count()===2,'two open auctions');
ok((await p.locator('#list .card').first().innerText()).includes('Harvest papers checked'),'proof badge first');
ok(await p.locator('#done .card').count()===1,'closed auction shown');
ok((await p.locator('#list').innerText()).includes('Gastrodia tuber 1 kg'),'seller english title shown');
ok(await p.locator('#beta').isVisible(),'beta notice');
ok(await p.locator('[data-lang="zh-Hant"]').count()===0,'no traditional chinese option');
await p.click('[data-lang="zh-Hans"]');await p.waitForTimeout(200);
ok((await p.locator('#list .card').first().innerText()).includes('野山参')&&(await p.locator('#list .card').first().innerText()).includes('¥'),'simplified + CNY');
await p.locator('#list .card').first().click();await p.waitForTimeout(200);
ok(await p.locator('#dlg[open]').count()===1,'detail opens');
await p.click('#notify');await p.waitForTimeout(300);
ok(await p.locator('.nmauth').isVisible()&&(await p.locator('#nmAuthH').innerText()).includes('登录'),'login sheet in chinese');
await p.screenshot({path:'g_zh_login.png'});
await p.fill('#nmMail','a@b.co');await p.click('#nmSend');await p.waitForTimeout(200);
ok(await p.evaluate(()=>JSON.parse(localStorage.getItem('nm_return')).url.includes('global.html')),'return page remembered');
ok(errs.length===0,'no errors signed out '+errs.join('|'));await ctx.close();
({p,errs,ctx}=await open('window.__SESSION={user:{id:"me"}};'+D(false),'/app/global.html?lang=en'));
await p.locator('#list .card').first().click();await p.waitForTimeout(200);
ok(await p.locator('#bidIn').count()===1,'bid box when live');
ok(+(await p.inputValue('#bidIn'))===1010000,'min next bid 1,010,000');
await p.fill('#bidIn','1005000');await p.click('#bidBtn');await p.waitForTimeout(200);
ok((await p.locator('#toast').innerText()).includes('1,010,000'),'too low rejected');
await p.fill('#bidIn','1020000');await p.click('#bidBtn');ok((await p.locator('#bidBtn').innerText()).includes('Confirm'),'two-step confirm');
await p.click('#bidBtn');await p.waitForTimeout(800);
const c=await p.evaluate(()=>window.__calls.filter(c=>c[0]==='upsert'&&c[1]==='bids').map(c=>c[3]));
ok(c.length===1&&c[0].amount===1020000&&c[0].bidderId==='me','bid saved');
await p.screenshot({path:'g_bid.png'});
// market + orders
await p.keyboard.press('Escape');await p.waitForTimeout(100);await p.click('[data-tab="mkt"]');await p.waitForTimeout(200);
ok(await p.locator('#mlist .card').count()===2,'two products listed');
ok((await p.locator('#mlist .card').first().innerText()).includes('Bracken')||(await p.locator('#mlist .card').first().innerText()).length>0,'product name shown');
await p.locator('#mlist .card').first().click();await p.waitForTimeout(200);
ok((await p.locator('.warn').innerText()).includes('Boil'),'preparation warning in english');
ok((await p.locator('#buy').innerText()).includes('Order'),'order button with total');
await p.click('#buy');await p.waitForTimeout(800);
const oc=await p.evaluate(()=>window.__calls.filter(c=>c[0]==='upsert'&&c[1]==='orders').map(c=>c[3]));
ok(oc.length===1&&oc[0].total===33500&&oc[0].buyerId==='me','order saved with shipping');
ok(await p.evaluate(()=>S.tab)==='ord','moved to my orders');
await p.screenshot({path:'g_orders.png',fullPage:true});
ok((await p.locator('#olist').innerText()).includes('Shipped'),'order status translated');
await p.click('[data-recv="o1"]');await p.waitForTimeout(400);
ok(await p.evaluate(()=>window.__calls.some(c=>c[0]==='rpc'&&c[1]==='doc_update'&&c[2].p_col==='orders'&&c[2].p_patch.status==='수령확인')),'receive confirmed');

ok(errs.length===0,'no errors signed in '+errs.join('|'));
await b.close();console.log(fails?fails+' FAILED':'ALL PASS');process.exit(fails?1:0)})();
