const { chromium } = require('playwright');const fs=require('fs'),path=require('path');
const fake=fs.readFileSync(path.join(__dirname,'fake_supabase.js'),'utf8'),mock=fs.readFileSync(path.join(__dirname,'../../app/mock_new.js'),'utf8');
let fails=0;const ok=(c,m)=>{console.log((c?'PASS ':'FAIL ')+m);if(!c)fails++};
const post=`(()=>{const D=window.__D;D.settings.site={beta:false};D.sellers.s1.resp=[30,40,50,200];
 D.messages.q1={members:["buyer","s2"].sort(),from:"buyer",to:"s2",text:"언제 캔 건가요?",createdAt:Date.now()-90*60e3};
 const k=Object.keys(D.products).find(k=>D.products[k].sellerId==="s1");D.products[k].faq={harv:"10월 20일 채취",ship:"주문 다음 날 발송"};window.__FAQP=k;})();`;
(async()=>{const b=await chromium.launch();
async function open(uid){const ctx=await b.newContext({viewport:{width:390,height:844},serviceWorkers:'block',locale:'ko-KR'});const p=await ctx.newPage();const errs=[];p.on('pageerror',e=>errs.push(String(e)));
 await p.route('**/vendor/supabase.js',r=>r.fulfill({contentType:'application/javascript',body:fake}));await p.addInitScript(`window.__SESSION={user:{id:"${uid}"}};\n`+mock+'\n'+post);await p.goto(process.argv[2]+'/app/');await p.waitForTimeout(1300);return {p,errs,ctx}}
// 판매자 s2: 빠른 답장 + 답변 시간 기록 + 자주 묻는 질문 채우기
let {p,errs,ctx}=await open('s2');
await p.evaluate(()=>openThread('buyer'));await p.waitForTimeout(300);
ok(await p.locator('#qr button').count()===5,'seller quick replies: '+await p.locator('#qr button').count());
await p.locator('#qr button',{hasText:'오늘 캐서'}).click();ok((await p.inputValue('#cText')).includes('오늘 캐서 내일'),'chip fills message');
await p.screenshot({path:path.join(__dirname,'chat_seller.png')});
await p.click('#compose button[type=submit]');await p.waitForTimeout(600);
const sv=await p.evaluate(()=>window.__calls.filter(c=>c[0]==='rpc'&&c[1]==='doc_update'&&c[2].p_col==='sellers'&&c[2].p_id==='s2').pop());
const rs=sv&&sv[2].p_patch&&sv[2].p_patch.resp;ok(Array.isArray(rs)&&rs.slice(-1)[0]>=85&&rs.slice(-1)[0]<=95,'reply time logged: '+JSON.stringify(rs));
await p.evaluate(()=>go('seller'));await p.waitForTimeout(200);
const pid=await p.evaluate(()=>S.products.find(x=>x.sellerId==='s2'&&x.status==='판매중').id);
await p.locator(`[data-act="faqP"][data-id="${pid}"]`).locator('xpath=ancestor::details').locator('summary').click();
await p.fill('#fqharv-'+pid,'10월 22일 수확');await p.fill('#fqkeep-'+pid,'냉장 2주');await p.click(`[data-act="faqP"][data-id="${pid}"]`);await p.waitForTimeout(500);
ok(await p.evaluate(id=>{const x=S.products.find(y=>y.id===id);return x.faq&&x.faq.harv==='10월 22일 수확'&&x.faq.keep==='냉장 2주'},pid),'seller saves FAQ');
ok(errs.length===0,'no errors seller '+errs.join('|'));await ctx.close();
// 손님: 상품의 자주 묻는 질문, 판매자 답변 시간, 손님용 빠른 질문
({p,errs,ctx}=await open('buyer'));
await p.evaluate(()=>openProduct(window.__FAQP));await p.waitForTimeout(300);
{const tx=await p.locator('#dlg').innerText();ok(tx.includes('판매자가 미리 답했어요')&&tx.includes('10월 20일 채취')&&tx.includes('주문 다음 날 발송'),'FAQ on product page');ok(tx.includes('⚡ 보통 1시간 안에 답해요'),'seller reply time on product page')}
await p.screenshot({path:path.join(__dirname,'chat_product.png'),fullPage:false});
await p.evaluate(()=>{const f=document.querySelector('.faqbox');f.scrollIntoView({block:'center'})});await p.waitForTimeout(200);await p.screenshot({path:path.join(__dirname,'chat_faq.png')});
await p.keyboard.press('Escape');await p.evaluate(()=>openThread('s1'));await p.waitForTimeout(300);
ok(await p.locator('#qr button').count()===4,'buyer quick questions');
ok((await p.locator('.chead').innerText()).includes('보통 1시간 안에'),'reply time in chat header');
await p.screenshot({path:path.join(__dirname,'chat_buyer.png')});
await p.evaluate(()=>openProfile('s2'));await p.waitForTimeout(200);ok((await p.locator('#dlg').innerText()).includes('답변 기록이 아직 적어요')||(await p.locator('#dlg .pstats').innerText()).includes('-'),'new seller has no time yet');
ok(errs.length===0,'no errors buyer '+errs.join('|'));
await b.close();console.log(fails?fails+' FAILED':'ALL PASS');process.exit(fails?1:0)})();
