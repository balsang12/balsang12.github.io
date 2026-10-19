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
  ok(await p.locator('#nmIntl').isVisible() && (await p.locator('#nmIntlA').getAttribute('href')) === 'global.html?lang=en', 'foreign visitor sees English link');
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
  // 3) 채취 증빙 단계
  const pf = await p.evaluate(async () => {
    const r = {};
    r.basic = proofNeed('더덕', '자연산 (산에서 채취)', 30000);
    r.wild = proofNeed('산삼', '자연산 (산에서 채취)', 200000);
    r.cult = proofNeed('장뇌삼', '재배 (인증 없음)', 200000);
    r.big = proofNeed('천마', '재배 (인증 없음)', 1500000);
    r.noOath = proofCheck({ item: '더덕', grow: '재배 (인증 없음)', price: 1, oath: false });
    r.noPhoto = proofCheck({ item: '산삼', grow: '자연산 (산에서 채취)', price: 1, oath: true });
    r.okBasic = proofCheck({ item: '더덕', grow: '재배 (인증 없음)', price: 1, oath: true });
    // 경매 출품: 자연산 산삼, 서류 사진 없음 → 막힘
    S.sellers[S.uid] = S.sellers[S.uid] || { shopName: '테스트', role: '심마니 (자연산 채취)', region: '강원' };
    $('#aCat').value = '산삼'; $('#aGrow').value = '자연산 (산에서 채취)'; $('#aTitle').value = '산삼 1뿌리'; $('#aWeight').value = '1뿌리'; $('#aRegion').value = '강원 인제'; $('#aStart').value = '200000'; $('#aBuyNow').value = '';
    aPhoto = 'data:image/png;base64,AAAA'; $('#aOath').checked = true; aucUI(); proofUI();
    r.lbl = $('#aProofLbl').textContent;
    const before = window.__calls.filter(c => c[0] === 'upsert' && c[1] === 'auctions').length;
    await $('#aucForm').onsubmit({ preventDefault() {} });
    r.blocked = window.__calls.filter(c => c[0] === 'upsert' && c[1] === 'auctions').length === before;
    aProof = 'data:image/png;base64,BBBB'; aPhoto = 'data:image/png;base64,AAAA';
    await $('#aucForm').onsubmit({ preventDefault() {} });
    const ups = window.__calls.filter(c => c[0] === 'upsert');
    const pr = ups.filter(c => c[1] === 'proofs').pop(), au = ups.filter(c => c[1] === 'auctions').pop();
    r.proofSaved = !!pr && pr[3].photo.includes('BBBB') && pr[3].status === '대기';
    r.aucRef = au && au[3].proofRef === pr[2] && au[3].proofNeed === 'photo' && au[3].status === '검수대기' && !('photo' in au[3] && au[3].photo.includes('BBBB'));
    r.noProofInAuc = au && !JSON.stringify(au[3]).includes('BBBB');
    // 운영자: 승인 전 증빙 확인 필요 → 확인 → 배지
    await new Promise(z => setTimeout(z, 700));
    const a = S.auctions.find(x => x.id === au[2]);
    await ACT.approveA(a.id); r.gate = S.auctions.find(x => x.id === a.id).status === '검수대기';
    S.proofs = [{ id: pr[2], ...pr[3] }]; go('admin'); renderAdmin();
    r.queue = document.querySelectorAll('#proofQueue [data-pfok]').length;
    document.querySelector('#proofQueue [data-pfok]').click(); await new Promise(z => setTimeout(z, 900));
    r.badge = !!S.auctions.find(x => x.id === a.id).proofOk;
    r.card = aucCard(S.auctions.find(x => x.id === a.id)).includes('채취 증빙 확인');
    // 산주 찾기
    r.land = await landReq({ herb: '산삼', parcel: '강원 인제군 기린면 산12', contact: '010' });
    r.landDoc = window.__calls.some(c => c[0] === 'upsert' && c[1] === 'landreqs' && c[3].by === S.uid);
    return r;
  });
  console.log(JSON.stringify(pf));
  ok(pf.basic === 'basic' && pf.wild === 'photo' && pf.cult === 'cert' && pf.big === 'photo', 'proof tiers by item and price');
  ok(pf.noOath && pf.noPhoto && pf.okBasic === '', 'proof checks');
  ok(pf.lbl.includes('필수'), 'proof photo marked required for wild ginseng');
  ok(pf.blocked, 'wild ginseng without papers is blocked');
  ok(pf.proofSaved && pf.aucRef && pf.noProofInAuc, 'papers stored apart from the public listing');
  ok(pf.gate, 'approval waits for proof check');
  ok(pf.queue >= 1 && pf.badge && pf.card, 'operator confirms papers and badge shows');
  ok(pf.land && pf.landDoc, 'landowner lookup request saved');
  // 4) 해외 제목
  const it = await p.evaluate(async () => {
    const r = {};
    $('#aCat').value = '천마'; $('#aGrow').value = '재배 (인증 없음)'; $('#aTitle').value = '천마 1kg'; $('#aWeight').value = '1kg'; $('#aRegion').value = '강원 인제'; $('#aStart').value = '50000'; $('#aBuyNow').value = '';
    aPhoto = 'data:image/png;base64,AAAA'; aProof = ''; $('#aOath').checked = true; aucUI();
    r.trHidden = $('#aTr').hidden;
    $('#aTitleEn').value = 'Gastrodia that cures cancer'; $('#aTitleZh').value = '';
    const n0 = window.__calls.filter(c => c[0] === 'upsert' && c[1] === 'auctions').length;
    await $('#aucForm').onsubmit({ preventDefault() {} });
    r.blocked = window.__calls.filter(c => c[0] === 'upsert' && c[1] === 'auctions').length === n0;
    $('#aTitleEn').value = 'Gastrodia tuber 1 kg'; $('#aTitleZh').value = '天麻 1公斤'; aPhoto = 'data:image/png;base64,AAAA'; $('#aOath').checked = true;
    await $('#aucForm').onsubmit({ preventDefault() {} });
    const au = window.__calls.filter(c => c[0] === 'upsert' && c[1] === 'auctions').pop();
    r.saved = au[3].titleEn === 'Gastrodia tuber 1 kg' && au[3].titleZh === '天麻 1公斤';
    r.cleared = $('#aTitleEn').value === '';
    return r;
  });
  console.log(JSON.stringify(it));
  ok(it.trHidden, 'no AI translate button on the public site');
  ok(it.blocked, 'health claim in English title blocked');
  ok(it.saved && it.cleared, 'foreign titles saved');
  ok(errs.length === 0, 'no console errors (signed in) ' + errs.slice(0, 3).join(' | '));
  await ctx.close(); await b.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS'); process.exit(fails ? 1 : 0);
})();
