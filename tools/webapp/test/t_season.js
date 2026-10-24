const { chromium } = require('playwright');const fs=require('fs'),path=require('path');
const fake=fs.readFileSync(path.join(__dirname,'fake_supabase.js'),'utf8'),mock=fs.readFileSync(path.join(__dirname,'../../app/mock_new.js'),'utf8');
let fails=0;const ok=(c,m)=>{console.log((c?'PASS ':'FAIL ')+m);if(!c)fails++};
(async()=>{const b=await chromium.launch();
for(const [w,h,name] of [[390,844,'phone'],[1280,900,'laptop']]){
 const ctx=await b.newContext({viewport:{width:w,height:h},serviceWorkers:'block',locale:'ko-KR'});const p=await ctx.newPage();const errs=[];p.on('pageerror',e=>errs.push(String(e)));
 await p.route('**/vendor/supabase.js',r=>r.fulfill({contentType:'application/javascript',body:fake}));await p.addInitScript('window.__SESSION={user:{id:"buyer"}};\n'+mock);await p.goto(process.argv[2]+'/app/');await p.waitForTimeout(1300);
 ok((await p.locator('.hhead h1').innerText()).includes('누가 어디서 캤는지'),name+' h1');
 ok(await p.locator('#hSeason').isVisible(),name+' season line visible: '+await p.locator('#hSeason').innerText());
 await p.screenshot({path:path.join(__dirname,'season_'+name+'.png')});
 await p.locator('#hSeason .sq').first().click();await p.waitForTimeout(300);
 ok(await p.evaluate(()=>S.view)==='shop'&&(await p.inputValue('#shopQ')).length>0,name+' chip searches: '+await p.inputValue('#shopQ'));
 ok(errs.length===0,name+' no errors '+errs.join('|'));await ctx.close()}
await b.close();console.log(fails?fails+' FAILED':'ALL PASS');process.exit(fails?1:0)})();
