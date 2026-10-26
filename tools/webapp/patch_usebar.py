import pathlib
p=pathlib.Path("app/index.html");s=p.read_text(encoding="utf-8")
def rep(a,b):
    global s
    assert s.count(a)==1,a[:60];s=s.replace(a,b)
rep('''el.innerHTML=`<button type="button" data-reco="1" style="font-weight:700;border-color:var(--gold);background:var(--gold-soft)">🧺 쇼핑도우미</button><span class="lbl">어떻게 드세요?</span>`+USES''',
    '''el.innerHTML=`<span class="lbl">용도별</span>`+USES''')
rep('''$("#shopCount").textContent=list.length?`상품 ${list.length}개${s==="unit"?" · 단위가 다른 상품은 1kg 기준으로 바꿔 비교":""}${s==="pop"?" · 판매량과 후기로 정렬":""}`:"";''',
    '''$("#shopCount").innerHTML=(list.length?`상품 ${list.length}개${s==="unit"?" · 단위가 다른 상품은 1kg 기준으로 바꿔 비교":""}${s==="pop"?" · 판매량과 후기로 정렬":""} · `:"")+`<button type="button" class="helplink" data-reco="1">🧺 뭘 살지 모르겠다면 쇼핑도우미</button>`;''')
rep('.usebar .lbl{font-size:12px;color:var(--muted);flex:none}',
    '.usebar .lbl{font-size:12px;color:var(--muted);flex:none}\n.helplink{background:none;border:0;padding:0;font:inherit;color:var(--pine);text-decoration:underline;text-underline-offset:3px;cursor:pointer}')
p.write_text(s,encoding="utf-8");print("ok")
