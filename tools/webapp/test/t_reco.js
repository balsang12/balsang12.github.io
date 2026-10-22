const { chromium } = require('playwright');const fs=require('fs'),path=require('path');
const fake=fs.readFileSync(path.join(__dirname,'fake_supabase.js'),'utf8'),mock=fs.readFileSync(path.join(__dirname,'../../app/mock_new.js'),'utf8');
let fails=0;const ok=(c,m)=>{console.log((c?'PASS ':'FAIL ')+m);if(!c)fails++};
(async()=>{const b=await chromium.launch();const ctx=await b.newContext({viewport:{width:390,height:844},serviceWorkers:'block',locale:'ko-KR'});const p=await ctx.newPage();const errs=[];
p.on('pageerror',e=>errs.push(String(e)));
await p.route('**/vendor/supabase.js',r=>r.fulfill({contentType:'application/javascript',body:fake}));
await p.addInitScript('window.__SESSION={user:{id:"me"}};\n'+mock);await p.goto(process.argv[2]+'/app/');await p.waitForTimeout(1200);
ok(await p.locator('.recomini').isVisible(),'home recommender button next to search');
await p.locator('.recomini').click();await p.waitForTimeout(150);
ok((await p.locator('.reco h2').innerText()).includes('누가 드실'),'first question: for whom');
{const tx=await p.locator('.reco').innerText();ok(tx.includes('내가 먹을 것')&&tx.includes('가족·다른 분')&&tx.includes('선물할 것'),'three branches')}
await p.screenshot({path:'reco_first.png'});
{const r=await p.evaluate(()=>{const m=recoRun({src:"mtn"},recoCtx()).list,f=recoRun({src:"farm"},recoCtx()).list;return {m:m.length,mOk:m.every(i=>/^자연산/.test(i.x.grow||"")||["산양삼","장뇌삼","산삼"].includes(i.x.item||"")),f:f.length,fOk:f.every(i=>!/^자연산/.test(i.x.grow||""))}});
 ok(r.m>0&&r.mOk&&r.f>0&&r.fOk,'mountain/farm filter '+JSON.stringify(r))}
{const q=await p.evaluate(()=>[recoQuestions({for:"me"}).map(x=>x.k).join(),recoQuestions({for:"others",whoO:"family"}).map(x=>x.k).join(),recoQuestions({for:"gift"}).map(x=>x.k).join()]);
 ok(q[0].startsWith('for,src,how,budget')&&!q[0].includes('whoG')&&q[1].startsWith('for,whoO,src')&&q[2].startsWith('for,whoG,occ,src,taste,gbudget,wrap')&&!q[2].includes('how'),'branching '+JSON.stringify(q))}
await p.click('text=내가 먹을 것');await p.locator('.reco .any').click();await p.click('text=나물 무침·볶음');await p.click('text=2~5만 원');await p.click('text=바로 먹을 거라 신선하게');
ok((await p.locator('.reco h2').innerText()).includes('손질'),'branch: handling question for greens');
await p.click('text=바로 요리할 수 있는 것');ok((await p.locator('.reco h2').innerText()).includes('몇 분'),'branch: household size');
await p.click('text=1~2명');await p.click('#rcNext');await p.click('.reco .any');await p.waitForTimeout(150);
const res=await p.locator('.reco').innerText();await p.screenshot({path:'reco_result.png'});
ok(/이런 상품|딱 맞는/.test(res),'results screen: '+res.split('\n').slice(0,4).join(' | '));
ok(!/당뇨|면역|혈압|효능/.test(res),'no health wording');
const n=await p.locator('.rc').count();ok(n>=1,'has recommendations: '+n);
if(n){await p.locator('.rc').first().click();await p.waitForTimeout(200);ok(await p.locator('#dlg .dinfo h2').count()>0,'opens product')}
await p.evaluate(()=>go('shop'));await p.waitForTimeout(150);ok(await p.locator('#useBar [data-reco]').isVisible(),'market button');
// gift path
await p.keyboard.press('Escape');await p.waitForTimeout(100);await p.evaluate(()=>go('home'));await p.locator('.recomini').click();await p.waitForTimeout(150);
await p.click('text=선물할 것');ok((await p.locator('.reco h2').innerText()).includes('받는 분'),'gift: recipient');
await p.click('text=부모님·어르신');ok((await p.locator('.reco h2').innerText()).includes('어떤 때'),'gift: occasion');
await p.click('text=명절·연말 인사');await p.locator('.reco .any').click();
ok((await p.locator('.reco h2').innerText()).includes('좋아하세요'),'gift: taste');await p.click('text=실용적인 것 (나물·차)');
ok((await p.locator('.reco h2').innerText()).includes('선물 예산'),'gift: gift budget');await p.click('text=5만 원 이하');
ok((await p.locator('.reco h2').innerText()).includes('포장'),'gift: wrap');await p.locator('.reco .any').click();
await p.click('#rcNext');await p.locator('.reco .any').click();await p.waitForTimeout(150);
{const tx=await p.locator('.reco').innerText();await p.screenshot({path:'reco_gift.png'});ok(tx.includes('선물할 것')&&tx.includes('선물 한도'),'gift results header + law note: '+tx.split('\n').slice(0,3).join(' | '));ok(!/당뇨|면역|혈압|효능/.test(tx),'gift: no health wording')}
await p.keyboard.press('Escape');
// medNote
const mn=await p.evaluate(()=>[medNote("도라지","뿌리·줄기"),medNote("곰취","산나물"),medNote("산삼","뿌리 약초")].map(x=>!!x).join(','));ok(mn==='true,false,true','consult note on medicinal items only: '+mn);
ok(errs.length===0,'no errors '+errs.join('|'));await b.close();console.log(fails?fails+' FAILED':'ALL PASS');process.exit(fails?1:0)})();
