// Browser test of the web build with a stand-in Supabase. Usage: node t_web.js <base url>
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const base = process.argv[2];
const mock = fs.readFileSync(path.join(__dirname, '../../app/mock_new.js'), 'utf8');
const fake = fs.readFileSync(path.join(__dirname, 'fake_supabase.js'), 'utf8');
let fails = 0; const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };

async function open(b, pre, shot) {
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, serviceWorkers: 'block' });
  const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.route('**/vendor/supabase.js', r => r.fulfill({ contentType: 'application/javascript', body: fake }));
  await p.route('https://fonts.googleapis.com/**', r => r.fulfill({ contentType: 'text/css', body: '' }));
  await p.route(/upload\.wikimedia|commons\.wikimedia/, r => r.fulfill({ status: 404, body: '' }));
  await p.addInitScript(pre + '\n' + mock);
  await p.goto(base + '/app/'); await p.waitForTimeout(1500);
  if (shot) await p.screenshot({ path: shot });
  return { p, errs, ctx };
}
(async () => {
  const b = await chromium.launch();
  // 1) signed out: browse, then any write asks to sign in
  let { p, errs, ctx } = await open(b, 'window.__SESSION=null;', 'shot_anon.png');
  ok(await p.locator('#connBanner').isVisible(), 'signed-out banner shows');
  ok((await p.locator('#connBanner').innerText()).includes('로그인'), 'banner offers sign-in');
  ok(await p.locator('#who button', { hasText: '로그인' }).count() === 1, 'header sign-in button');
  const nProd = await p.evaluate(() => S.products.length);
  ok(nProd > 0, 'products load without sign-in: ' + nProd);
  ok(await p.evaluate(() => Object.keys(S.info || {}).length) > 0, 'herb dictionary loads');
  ok(await p.evaluate(() => S.orders.length) >= 0, 'orders query runs');
  const r = await p.evaluate(() => guard(() => Promise.resolve()));
  ok(r === false && await p.locator('.nmauth').isVisible(), 'writing opens the sign-in sheet');
  await p.screenshot({ path: 'shot_login.png' });
  await p.fill('#nmMail', 'hong@naver.com'); await p.click('#nmMailForm button'); await p.waitForTimeout(200);
  ok((await p.locator('#nmMsg').innerText()).includes('hong@naver.com'), 'email link sent message');
  await p.click('#nmKakao'); await p.waitForTimeout(200);
  ok((await p.locator('#nmMsg').innerText()).includes('이메일'), 'kakao not ready falls back politely');
  ok(await p.locator('button.needWrite:disabled').count() === 0, 'no dead write buttons when signed out');
  ok(errs.length === 0, 'no console errors (signed out) ' + errs.slice(0, 3).join(' | '));
  await ctx.close();

  // 2) signed in as operator
  ({ p, errs, ctx } = await open(b, 'window.__SESSION={user:{id:"me"}};window.__ADMIN=true;window.__MGR="s1";', 'shot_admin.png'));
  ok(await p.evaluate(() => S.uid) === 'me', 'uid from session');
  ok(await p.evaluate(() => !document.querySelector('#adminTab').hidden && S.owner === true), 'operator tab enabled');
  ok(await p.locator('#who').innerText().then(t => t.includes('로그아웃')), 'sign-out button');
  ok(!(await p.locator('#connBanner').isVisible()), 'no banner when signed in');
  const w = await p.evaluate(async () => { const a = await guard(() => S.db.collection('alerts').add({ key: '더덕', kind: 'product', uid: S.uid, createdAt: Date.now() })); return [a, window.__calls.filter(c => c[0] === 'upsert').length]; });
  ok(w[0] === true && w[1] === 1, 'write goes through (add)');
  const u = await p.evaluate(async () => { const id = S.products[0].id; const a = await guard(() => S.db.doc('products/' + id).update({ stock: 3 })); await new Promise(r => setTimeout(r, 600)); return [a, S.products.find(x => x.id === id).stock]; });
  ok(u[0] === true && u[1] === 3, 'update merges and the list refreshes');
  const m = await p.evaluate(async () => { document.querySelector('#mgrIn') || document.body.insertAdjacentHTML('beforeend', '<input id="mgrIn">'); document.querySelector('#mgrIn').value = 'ABCD-2345'; await mgrAct('link'); return window.__calls.filter(c => c[0] === 'rpc' && c[1] === 'mgr_find').length + ':' + JSON.stringify(window.__calls.filter(c => c[0] === 'upsert' && c[1] === 'shopmgr').map(c => c[3].links[0].shop)); });
  ok(m.startsWith('1:') && m.includes('s1'), 'manager link checked on server: ' + m);
  const nf = await p.evaluate(() => guard(() => S.db.doc('products/nope').update({ stock: 1 })));
  ok(nf === false && await p.evaluate(() => S.canWrite) !== false, 'missing doc does not lock the app');
  await p.evaluate(() => go('admin')); await p.waitForTimeout(400); await p.screenshot({ path: 'shot_admin_tab.png' });
  ok(errs.length === 0, 'no console errors (signed in) ' + errs.slice(0, 3).join(' | '));
  await ctx.close(); await b.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS'); process.exit(fails ? 1 : 0);
})();
