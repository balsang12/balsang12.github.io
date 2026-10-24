const { chromium } = require('playwright');const fs=require('fs'),path=require('path');
const fake=fs.readFileSync(path.join(__dirname,'fake_supabase.js'),'utf8'),mock=fs.readFileSync(path.join(__dirname,'../../app/mock_new.js'),'utf8');
let fails=0;const ok=(c,m)=>{console.log((c?'PASS ':'FAIL ')+m);if(!c)fails++};
const post=`(()=>{const D=window.__D;D.settings.site={beta:false};D.sellers.s1.biz="면세사업자";
 const k=Object.keys(D.products).find(x=>D.products[x].name==="약도라지 3년근");D.products[k].qd=[{n:5,pct:5},{n:10,pct:10}];D.products[k].stock=50;window.__QP=k;
 D.requests.bk1={item:"산양삼 선물세트",qty:30,unit:"개",form:"선물용",grow:"상관없음",due:"2026-12-20",region:"전국",memo:"",bulk:{count:30,places:"many",placeN:30,budget:80000,wrap:true,prodCard:true,invoice:true,org:"○○상사"},buyerId:"buyer",status:"모집중",createdAt:Date.now()-1000};})();`;
(async()=>{const b=await chromium.launch();
async function open(uid){const ctx=await b.newContext({viewport:{width:390,height:844},serviceWorkers:'block',locale:'ko-KR'});const p=await ctx.newPage();const errs=[];p.on('pageerror',e=>errs.push(String(e)));
 await p.route('**/vendor/supabase.js',r=>r.fulfill({contentType:'application/javascript',body:fake}));await p.addInitScript(`window.__SESSION={user:{id:"${uid}"}};\n`+mock+'\n'+post);await p.goto(process.argv[2]+'/app/');await p.waitForTimeout(1300);return {p,errs,ctx}}
let {p,errs,ctx}=await open('buyer');
// 수량 할인
await p.evaluate(()=>openProduct(window.__QP));await p.waitForTimeout(300);
ok((await p.locator('#dlg .spec').innerText()).includes('5개 이상 5% · 10개 이상 10% 할인'),'qd shown in spec');
ok((await p.locator('#qdLbl').innerText()).includes('5개부터 5% 할인'),'next-tier hint');
for(let i=0;i<9;i++)await p.click('#plus');
ok((await p.locator('#qdLbl').innerText()).includes('10% 할인'),'10 pcs → 10%');
const tot=await p.locator('#tot').innerText();ok(tot.startsWith('221,000'),'total with 10% off + ship: '+tot);
await p.screenshot({path:path.join(__dirname,'bulk_qd.png')});
await p.click('#buy');await p.waitForTimeout(800);
const od=await p.evaluate(()=>window.__calls.filter(c=>c[0]==='upsert'&&c[1]==='orders').pop());
ok(od&&od[3].qdPct===10&&od[3].qdOff===24000&&od[3].total===216000+5000,'order saved with discount '+JSON.stringify(od&&{t:od[3].total,o:od[3].qdOff}));
// 대량 요청서
await p.evaluate(()=>go('request'));await p.waitForTimeout(200);
ok(await p.locator('.bulkcta').isVisible(),'bulk CTA on request page');
await p.click('.bulkcta');await p.waitForTimeout(200);
await p.fill('#bkItem','더덕·도라지청 세트');await p.fill('#bkCount','40');await p.fill('#bkBudget','50000');await p.check('input[name="bkPl"][value="many"]');await p.fill('#bkPlN','40');
await p.fill('#bkDue',await p.evaluate(()=>new Date(Date.now()+9*3600e3+20*864e5).toISOString().slice(0,10)));await p.fill('#bkOrg','농마니상사 총무팀');await p.check('#bkInv');
await p.screenshot({path:path.join(__dirname,'bulk_form.png')});
await p.click('#bulkForm button[type=submit]');await p.waitForTimeout(700);
const rq=await p.evaluate(()=>window.__calls.filter(c=>c[0]==='upsert'&&c[1]==='requests').pop());
ok(rq&&rq[3].qty===40&&rq[3].bulk.places==='many'&&rq[3].bulk.placeN===40&&rq[3].bulk.invoice===true&&rq[3].bulk.org==='농마니상사 총무팀','bulk request saved '+JSON.stringify(rq&&rq[3].bulk));
ok((await p.locator('#myReqs').innerText()).includes('대량·단체'),'buyer sees bulk tag');
ok(errs.length===0,'no errors buyer '+errs.join('|'));await ctx.close();
// 판매자: 사업자(s1)는 계산서 필요 의뢰가 맨 위, 일반(s2)는 경고
({p,errs,ctx}=await open('s1'));await p.evaluate(()=>go('seller'));await p.waitForTimeout(300);
{const first=await p.locator('#openReqs .item').first().innerText();ok(first.includes('대량·단체')&&first.includes('계산서 필요')&&!first.includes('사업자 판매자만'),'invoicing seller sees bulk first')}
await p.locator('#openReqs .item').first().screenshot({path:path.join(__dirname,'bulk_seller.png')});
ok((await p.evaluate(()=>sellerRow('s1',''))).includes('계산서 발행 가능'),'invoice chip on seller row');
// 판매자 수량 할인 저장
const mp=await p.evaluate(()=>S.products.find(x=>x.sellerId==='s1'&&x.status==='판매중').id);
await p.evaluate(id=>{document.querySelector(`[data-act="qdP"][data-id="${id}"]`).closest('details').open=true},mp);
await p.fill('#mq1n-'+mp,'3');await p.fill('#mq1p-'+mp,'5');await p.click(`[data-act="qdP"][data-id="${mp}"]`);await p.waitForTimeout(500);
ok(await p.evaluate(id=>JSON.stringify(S.products.find(x=>x.id===id).qd),mp)==='[{"n":3,"pct":5}]','seller saves qty discount');
ok(errs.length===0,'no errors s1 '+errs.join('|'));await ctx.close();
({p,errs,ctx}=await open('s2'));await p.evaluate(()=>go('seller'));await p.waitForTimeout(300);
ok((await p.locator('#openReqs').innerText()).includes('사업자 판매자만 발행 가능'),'non-business seller warned');
ok(errs.length===0,'no errors s2 '+errs.join('|'));
await b.close();console.log(fails?fails+' FAILED':'ALL PASS');process.exit(fails?1:0)})();
