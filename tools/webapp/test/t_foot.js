const { chromium } = require('playwright');const fs=require('fs'),path=require('path');
const fake=fs.readFileSync(path.join(__dirname,'fake_supabase.js'),'utf8'),mock=fs.readFileSync(path.join(__dirname,'../../app/mock_new.js'),'utf8');
(async()=>{const b=await chromium.launch();const c=await b.newContext({viewport:{width:390,height:844},locale:'ko-KR',serviceWorkers:'block'});const p=await c.newPage();const errs=[];p.on('pageerror',e=>errs.push(String(e)));
await p.route('**/vendor/supabase.js',r=>r.fulfill({contentType:'application/javascript',body:fake}));await p.addInitScript(mock);await p.goto(process.argv[2]+'/app/');await p.waitForTimeout(1300);
await p.click('footer >> text=산야초 사전');await p.waitForTimeout(300);const v=await p.evaluate(()=>S.view);console.log(v==='herbs'&&!errs.length?'ALL PASS':'FAIL '+v+errs);await b.close()})();
