const { chromium } = require('playwright');const fs=require('fs'),path=require('path');
const fake=fs.readFileSync(path.join(__dirname,'fake_supabase.js'),'utf8'),mock=fs.readFileSync(path.join(__dirname,'../../app/mock_new.js'),'utf8');
let fails=0;const ok=(c,m)=>{console.log((c?'PASS ':'FAIL ')+m);if(!c)fails++};
(async()=>{const b=await chromium.launch();
for(const [q,v] of [['?go=seller','seller'],['#seller','seller'],['?go=nothing','home'],['','home']]){const c=await b.newContext({viewport:{width:390,height:844},locale:'ko-KR',serviceWorkers:'block'});const p=await c.newPage();const errs=[];p.on('pageerror',e=>errs.push(String(e)));
 await p.route('**/vendor/supabase.js',r=>r.fulfill({contentType:'application/javascript',body:fake}));await p.addInitScript(mock);await p.goto(process.argv[2]+'/app/'+q);await p.waitForTimeout(1300);
 ok(await p.evaluate(()=>S.view)===v&&!errs.length,`${q||'(none)'} → ${v}`);
 if(q==='?go=seller')await p.screenshot({path:path.join(__dirname,'golink_seller.png')});await c.close()}
await b.close();console.log(fails?fails+' FAILED':'ALL PASS');process.exit(fails?1:0)})();
