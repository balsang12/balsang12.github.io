const { chromium } = require('playwright');const fs=require('fs'),path=require('path');
const fake=fs.readFileSync(path.join(__dirname,'fake_supabase.js'),'utf8'),mock=fs.readFileSync(path.join(__dirname,'../../app/mock_new.js'),'utf8');
let fails=0;const ok=(c,m)=>{console.log((c?'PASS ':'FAIL ')+m);if(!c)fails++};
const AND='Mozilla/5.0 (Linux; Android 14; SM-S918N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36';
const KAKAO=AND+' KAKAOTALK 10.8.0';
const IOS='Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1';
(async()=>{const b=await chromium.launch();
for(const [name,ua,want] of [['android',AND,'메뉴(⋮'],['kakao',KAKAO,'다른 브라우저로 열기'],['ios',IOS,'공유 버튼'],['desktop',null,null]]){
 const c=await b.newContext({viewport:ua?{width:390,height:844}:{width:1280,height:800},userAgent:ua||undefined,locale:'ko-KR',serviceWorkers:'block'});const p=await c.newPage();const errs=[];p.on('pageerror',e=>errs.push(String(e)));
 await p.route('**/vendor/supabase.js',r=>r.fulfill({contentType:'application/javascript',body:fake}));await p.addInitScript(mock);await p.goto(process.argv[2]+'/app/?go=seller');await p.waitForTimeout(1300);
 const card=await p.locator('#sellInstB').isVisible().catch(()=>false);
 if(!ua){ok(!card&&!errs.length,'desktop: no card, no errors '+errs.join(';'));await c.close();continue}
 ok(card,name+': seller card visible');
 await p.click('#sellInstB');await p.waitForTimeout(200);
 const t=await p.locator('#nmSel').innerText();ok(await p.locator('#nmSel').isVisible()&&t.includes(want),name+': guide shows '+want);
 await p.screenshot({path:path.join(__dirname,'inst_'+name+'.png')});
 await p.click('#nmSelX');ok(!(await p.locator('#nmSel').isVisible()),name+': closes');
 await p.evaluate(()=>window.nmSellerNew());await p.waitForTimeout(100);ok(await p.locator('#nmSel').isVisible(),name+': nmSellerNew opens guide');
 ok(!errs.length,name+': no errors '+errs.join(';'));await c.close()}
await b.close();console.log(fails?fails+' FAILED':'ALL PASS');process.exit(fails?1:0)})();
