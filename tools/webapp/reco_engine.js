/* 추천 도우미 엔진 (한국어 앱·해외 화면 공통). 쓰임새·예산·보관·조건으로만 고릅니다. 건강 상태로는 고르지 않습니다. */
/* 첫 질문(for)으로 세 갈래: 내가 먹을 것 / 가족·다른 분이 먹을 것 / 선물 */
const RECO_Q=[
 {k:"for",o:["me","others","gift"]},
 {k:"whoO",when:a=>a.for==="others",o:["parents","family","kids","biz"]},
 {k:"whoG",when:a=>a.for==="gift",o:["parents","boss","friend","biz"]},
 {k:"occ",when:a=>a.for==="gift",o:["holiday","thanks","visit"]},
 {k:"src",o:["mtn","farm"]},
 {k:"how",when:a=>a.for!=="gift",o:["namul","soup","tea","infuse","raw"]},
 {k:"taste",when:a=>a.for==="gift",o:["rare","daily","new"]},
 {k:"budget",when:a=>a.for!=="gift",o:["20","50","100","999"]},
 {k:"gbudget",when:a=>a.for==="gift",o:["g5","g15","g30","g99"]},
 {k:"wrap",when:a=>a.for==="gift",o:["yes"]},
 {k:"keep",when:a=>a.for!=="gift",o:["fresh","store"]},
 {k:"prep",when:a=>a.how==="namul"||a.how==="soup",o:["easy","ok"]},
 {k:"size",when:a=>a.for==="me"||(a.for==="others"&&a.whoO!=="biz"),o:["s","m","l"]},
 {k:"auc",when:a=>a.how==="raw"||a.taste==="rare",o:["no","yes"]},
 {k:"must",multi:true,o:["wild","cert","proof","review","season"]},
 {k:"region",o:["강원","경상","전라","충청","제주"]}
];
const RECO_BAND={"20":[0,20000],"50":[20000,50000],"100":[50000,100000],"999":[100000,1e12],"g5":[0,50000],"g15":[50000,150000],"g30":[150000,300000],"g99":[300000,1e12]};
const RECO_NEXT={"20":"50","50":"100","100":"999","999":"999","g5":"g15","g15":"g30","g30":"g99","g99":"g99"};
const RECO_REG={"강원":["강원"],"경상":["경북","경남","경상"],"전라":["전북","전남","전라"],"충청":["충북","충남","충청"],"제주":["제주"]};
const RECO_GIFT=["산양삼","산삼","장뇌삼","천마","송이","능이","하수오","상황","상황버섯","영지","겨우살이","복령","꽃송이버섯"];
const RECO_COMMON=["도라지","더덕","둥굴레","오미자","표고","대추","칡","구기자","결명자","생강","우엉","돼지감자","고사리","곰취","취나물","참나물","느타리"];
const RECO_UNIT_G={"300g":300,"500g":500,"1kg":1000,"근(600g)":600,"5kg":5000};
function recoQuestions(a){return RECO_Q.filter(q=>!q.when||q.when(a))}
function recoSeason(cat,m){m=m||new Date().getMonth()+1;return cat==="산나물"?m>=3&&m<=6:cat==="버섯"?m>=8&&m<=10:cat==="열매"?m>=6&&m<=10:cat==="뿌리 약초"?(m>=10||m<=4):false}
/* ctx: {products, auctions, aucCur(a)->number|null (null = closed), mcat(c), prep(item)->bool, rating(id)->{avg,n}} */
function recoRun(a,ctx){
  const items=[],gift=a.for==="gift",bud=gift?a.gbudget:a.budget;
  ctx.products.forEach(p=>{if(p.status==="판매중"&&p.stock>0&&!p.demo)items.push({kind:"p",x:p,cat:ctx.mcat(p.cat),price:(+p.price||0)+(p.form==="생물"?5000:3500)})});
  if(a.auc==="yes")ctx.auctions.forEach(x=>{const c=ctx.aucCur(x);if(c!=null&&!x.demo)items.push({kind:"a",x,cat:"뿌리 약초",price:c})});
  const proc=i=>i.kind==="p"&&i.x.cat==="가공품",form=i=>i.x.form||"";
  const how={namul:i=>i.cat==="산나물"&&!proc(i),
    soup:i=>["산나물","버섯","뿌리 약초"].includes(i.cat)&&!proc(i)&&i.kind==="p",
    tea:i=>i.cat==="말린 약초·차"||(["건조","덖음·차"].includes(form(i))&&i.cat!=="산나물")||(proc(i)&&/차/.test(form(i))),
    infuse:i=>((i.cat==="열매"||i.cat==="뿌리 약초")&&form(i)==="생물"&&i.kind==="p")||(proc(i)&&/청|잼/.test(form(i))),
    raw:i=>i.kind==="a"||i.cat==="뿌리 약초"||i.cat==="열매"||proc(i)};
  const must={wild:i=>String(i.x.grow||"").startsWith("자연산"),cert:i=>/인증/.test(i.x.grow||""),proof:i=>!!i.x.proofOk,
    review:i=>{if(i.kind!=="p")return false;const r=ctx.rating(i.x.id);return r.n>0&&r.avg>=4},season:i=>recoSeason(i.cat)};
  const fresh=i=>i.kind==="a"||form(i)==="생물";
  const mtn=i=>/^자연산/.test(i.x.grow||"")||["산양삼","장뇌삼","산삼"].includes(i.x.item||i.x.cat||"")||(i.kind==="a"&&!/재배/.test(i.x.grow||""));
  const wrapOk=i=>i.kind==="a"||!!i.x.gift;
  const regOk=i=>{const r=RECO_REG[a.region];return !r||r.some(x=>String(i.x.region||"").startsWith(x))};
  const bandHi=b=>(RECO_BAND[b]||[0,1e12])[1];
  const tries=[{},{region:1},{region:1,must:1},{region:1,must:1,budget:1},{region:1,must:1,budget:1,keep:1}];
  let out=[],relaxed={},strict=null;
  for(const r of tries){
    const hi=bud?(r.budget?bandHi(RECO_NEXT[bud]):bandHi(bud)):1e12;
    out=items.filter(i=>(!a.src||(a.src==="mtn")===mtn(i))&&(!a.how||how[a.how](i))&&i.price<=hi&&(r.keep||!a.keep||(a.keep==="fresh"?fresh(i):!fresh(i)))&&(r.region||regOk(i))&&(r.must||((a.must||[]).every(m=>must[m](i))&&(a.wrap!=="yes"||wrapOk(i)))));
    if(!strict)strict=new Set(out.map(i=>i.x.id));relaxed=r;if(out.length>=3)break}
  if(out.length===strict.size)relaxed={};
  const lo=bud?(RECO_BAND[bud]||[0])[0]:0;
  const elder=a.whoO==="parents"||a.whoG==="parents"||a.whoG==="boss",biz=a.whoO==="biz"||a.whoG==="biz";
  out.forEach(i=>{let s=0;const why=[];const it=i.x.item||i.x.cat||"";
    if(gift){if(!fresh(i)){s+=a.occ==="holiday"?3:2;why.push("keeps")}if(RECO_GIFT.includes(it)){s+=3;why.push("gift")}if(i.x.proofOk)s+=1;if(i.kind==="p"&&i.x.gift){s+=2;why.push("wrap")}}
    else if(elder){if(RECO_GIFT.includes(it))s+=1}
    if(biz&&i.kind==="p"){const g=RECO_UNIT_G[i.x.unit]||0;if(g>=1000){s+=2;why.push("bulk")}if(i.x.stock>=5)s+=1}
    if(a.whoO==="kids"&&(i.cat==="열매"||(proc(i)&&/청|잼/.test(form(i))))){s+=2;why.push("kids")}
    if(a.whoO==="family"&&i.kind==="p"){const g=RECO_UNIT_G[i.x.unit]||0;if(g>=600){s+=1;why.push("size")}}
    if(a.taste==="rare"&&(RECO_GIFT.includes(it)||String(i.x.grow||"").startsWith("자연산")||i.price>=50000)){s+=3;why.push("rare")}
    if(a.taste==="daily"&&["산나물","말린 약초·차"].includes(i.cat)){s+=2}
    if(a.taste==="new"&&!RECO_COMMON.includes(it)){s+=3;why.push("new")}
    if(a.size&&i.kind==="p"){const g=RECO_UNIT_G[i.x.unit]||0;if((a.size==="s"&&g&&g<=500)||(a.size==="m"&&g>=600&&g<=1000)||(a.size==="l"&&g>=1000)){s+=2;if(!why.includes("size"))why.push("size")}}
    if(a.prep==="easy"&&ctx.prep(it)){s-=4}
    if(ctx.prep(it))why.push("prep");
    if(i.price>=lo)s+=1;if(strict.has(i.x.id))s+=6;else why.unshift("wider");
    if(a.src)why.unshift(a.src);
    if(String(i.x.grow||"").startsWith("자연산")){s+=1;why.push("wild")}
    if(/인증/.test(i.x.grow||""))why.push("cert");
    if(i.x.proofOk){s+=1;why.push("proof")}
    if(recoSeason(i.cat)){s+=1;why.push("season")}
    if(i.kind==="p"){const r=ctx.rating(i.x.id);if(r.n){s+=r.avg/2;why.push("review")}}
    if(i.kind==="a")why.push("auction");
    i.score=s;i.why=why});
  out.sort((x,y)=>y.score-x.score||x.price-y.price);
  return {list:out.slice(0,5),relaxed,total:out.length}}
