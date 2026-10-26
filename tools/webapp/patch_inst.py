import sys,pathlib
p=pathlib.Path("app/index.html");s=p.read_text(encoding="utf-8")
def rep(a,b,n=1):
    global s
    assert s.count(a)==n,(a[:60],s.count(a));s=s.replace(a,b)
# 1) seller tab: slot for the home-screen icon card (filled only by the web build)
rep('<div class="sechead"><h2>판매자 센터</h2><span class="meta" id="shopLabel"></span></div>',
    '<div class="sechead"><h2>판매자 센터</h2><span class="meta" id="shopLabel"></span></div>\n  <div id="sellInst" hidden></div>')
# 2) first shop creation (wizard) -> install guide
rep('if(ok){WZ.region=WZ.region||rg;WZ.grow=WZ.shop.role.startsWith("농부")?GROWS[1]:GROWS[0];WZ.step=1;renderSell()}});',
    'if(ok){WZ.region=WZ.region||rg;WZ.grow=WZ.shop.role.startsWith("농부")?GROWS[1]:GROWS[0];WZ.step=1;renderSell();window.nmSellerNew&&setTimeout(window.nmSellerNew,900)}});')
# 3) first shop creation (full form)
rep('const {id:_omit,...prev}=S.sellers[S.uid]||{};\n  guard(',
    'const {id:_omit,...prev}=S.sellers[S.uid]||{},isNew=!S.sellers[S.uid];\n  guard(')
rep('biz:$("#shBiz").value,updatedAt:Date.now()}),"상점 정보를 저장했습니다")};',
    'biz:$("#shBiz").value,updatedAt:Date.now()}),"상점 정보를 저장했습니다").then(ok=>{if(ok&&isNew&&window.nmSellerNew)setTimeout(window.nmSellerNew,900)})};')
p.write_text(s,encoding="utf-8");print("ok")
