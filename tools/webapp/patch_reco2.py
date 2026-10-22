import pathlib,re
E=pathlib.Path("web/reco_engine.js").read_text(encoding="utf-8")
body=E[E.index("const RECO_Q=["):]
def swap_engine(s):
    i=s.index("const RECO_Q=[");j=s.index("return {list:out.slice(0,5),relaxed,total:out.length}}",i)+len("return {list:out.slice(0,5),relaxed,total:out.length}}")
    # also drop the comment line right before if it is the old one-liner (keep as is)
    return s[:i]+body.rstrip("\n")+s[j:]
def rep(s,a,b,label):
    assert s.count(a)==1,(label,s.count(a));return s.replace(a,b)
# ---- app
p=pathlib.Path("app/index.html");s=p.read_text(encoding="utf-8");s=swap_engine(s)
s=rep(s,'const RECO_KO={src:','''const RECO_KO={for:["누가 드실 건가요?",{me:"🙋 내가 먹을 것",others:"👨‍👩‍👧 가족·다른 분이 드실 것",gift:"🎁 선물할 것"}],
 whoO:["누가 드시나요?",{parents:"부모님·어르신",family:"온 가족이 함께",kids:"아이들",biz:"가게·식당 손님"}],
 whoG:["받는 분은 누구인가요?",{parents:"부모님·어르신",boss:"은사·윗분",friend:"친구·지인",biz:"거래처·회사 (여러 개)"}],
 occ:["어떤 때 드리는 선물인가요?",{holiday:"명절·연말 인사",thanks:"감사·축하",visit:"집들이·방문"}],
 gbudget:["선물 예산은 얼마인가요? (1개 기준, 배송비 포함)",{g5:"5만 원 이하",g15:"5~15만 원",g30:"15~30만 원",g99:"30만 원 이상"}],
 wrap:["선물 포장이 필요하세요?",{yes:"포장해서 보내 주는 상품만"}],
 src:''',"ko labels")
s=rep(s,'const RECO_WHY_KO={mtn:','const RECO_WHY_KO={wrap:"선물 포장 가능",kids:"아이와 함께 먹기 좋은",mtn:',"ko why")
s=rep(s,'${[lab("src").replace(/^\\S+ /,"").split(" — ")[0],lab("who"),lab("how"),lab("budget"),lab("keep")]',
      '${[lab("for"),lab("whoO")||lab("whoG"),lab("occ"),lab("src").split(" — ")[0],lab("how"),lab("budget")||lab("gbudget"),lab("keep")].map(x=>x.replace(/^[^\\p{L}\\p{N}]+/u,""))',"ko header")
s=rep(s,'      ${r.list.length?"":`<p style="margin:0">농부와 심마니에게 직접 구해 달라고 요청할 수 있어요.</p>`}',
'''      ${RC.a.for==="gift"?`<p class="meta" style="margin:0">공무원·교사·언론인 등에게 보낼 땐 선물 한도(평소 15만 원, 설·추석 기간 30만 원)를 확인하세요.</p>`:""}
      ${r.list.length?"":`<p style="margin:0">농부와 심마니에게 직접 구해 달라고 요청할 수 있어요.</p>`}''',"ko gift note")
s=rep(s,'<div class="actions"><button class="btn" type="button" id="rcAgain">다시 고르기</button>',
      '<div class="actions">${RC.a.for==="gift"&&typeof giftLive==="function"&&giftLive()?`<button class="btn gold" type="button" data-gift="all">🎁 선물 코너 보기</button>`:""}<button class="btn" type="button" id="rcAgain">다시 고르기</button>',"ko gift btn")
p.write_text(s,encoding="utf-8")
# ---- global
p=pathlib.Path("web/app/global.html");s=p.read_text(encoding="utf-8");s=swap_engine(s)
s=rep(s,'  q:{src:["What are you looking for?"','''  q:{for:["Who is it for?",{me:"🙋 For me",others:"👨‍👩‍👧 For family or others",gift:"🎁 A gift"}],
   whoO:["Who will eat it?",{parents:"Parents or elders",family:"The whole family",kids:"Children",biz:"Customers at my shop or restaurant"}],
   whoG:["Who is the gift for?",{parents:"Parents or elders",boss:"A teacher or senior",friend:"A friend",biz:"Clients or a company (several)"}],
   occ:["What is the occasion?",{holiday:"Holidays or year-end",thanks:"Thanks or congratulations",visit:"Housewarming or a visit"}],
   gbudget:["Gift budget (per gift, incl. delivery)",{g5:"Up to ₩50,000",g15:"₩50,000–150,000",g30:"₩150,000–300,000",g99:"Over ₩300,000"}],
   wrap:["Need gift wrapping?",{yes:"Only items the seller gift-wraps"}],
   src:["What are you looking for?"''',"en")
s=rep(s,'  q:{src:["何をお探しですか？"','''  q:{for:["どなたが召し上がりますか？",{me:"🙋 自分で食べる",others:"👨‍👩‍👧 家族・ほかの方が食べる",gift:"🎁 ギフト"}],
   whoO:["どなた向けですか？",{parents:"両親・目上の方",family:"家族みんなで",kids:"子ども",biz:"お店・飲食店のお客様"}],
   whoG:["贈る相手は？",{parents:"両親・目上の方",boss:"恩師・上司",friend:"友人・知人",biz:"取引先・会社（複数）"}],
   occ:["どんな機会の贈り物ですか？",{holiday:"お正月・年末・名節",thanks:"お礼・お祝い",visit:"新築祝い・訪問"}],
   gbudget:["ギフトの予算は？（1個あたり・送料込み）",{g5:"5万ウォン以下",g15:"5〜15万ウォン",g30:"15〜30万ウォン",g99:"30万ウォン以上"}],
   wrap:["ギフト包装は必要ですか？",{yes:"包装して送ってくれる商品だけ"}],
   src:["何をお探しですか？"''',"ja")
s=rep(s,'  q:{src:["您在找什么？"','''  q:{for:["给谁吃？",{me:"🙋 自己吃",others:"👨‍👩‍👧 家人或别人吃",gift:"🎁 送礼"}],
   whoO:["谁来吃？",{parents:"父母或长辈",family:"全家一起",kids:"孩子",biz:"店里或餐厅的客人"}],
   whoG:["送给谁？",{parents:"父母或长辈",boss:"老师或上级",friend:"朋友",biz:"客户或公司（多份）"}],
   occ:["什么场合的礼物？",{holiday:"节日或年末",thanks:"答谢或祝贺",visit:"乔迁或拜访"}],
   gbudget:["礼物预算？（每份，含运费）",{g5:"5万韩元以下",g15:"5万–15万韩元",g30:"15万–30万韩元",g99:"30万韩元以上"}],
   wrap:["需要礼品包装吗？",{yes:"只看卖家可以包装的"}],
   src:["您在找什么？"''',"zh")
s=rep(s,'  why:{mtn:"From the mountains"','  why:{wrap:"Gift wrap",kids:"Good with children",mtn:"From the mountains"',"en why")
s=rep(s,'  why:{mtn:"山で採れたもの"','  why:{wrap:"ギフト包装可",kids:"子どもと一緒に",mtn:"山で採れたもの"',"ja why")
s=rep(s,'  why:{mtn:"山里采的"','  why:{wrap:"可礼品包装",kids:"适合和孩子一起吃",mtn:"山里采的"',"zh why")
s=rep(s,'${[lab("who"),lab("how"),lab("budget"),lab("keep")]','${[lab("for"),lab("whoO")||lab("whoG"),lab("occ"),lab("how"),lab("budget")||lab("gbudget"),lab("keep")].map(x=>x.replace(/^[^\\p{L}\\p{N}]+/u,""))',"g header")
p.write_text(s,encoding="utf-8")
print("ok")
