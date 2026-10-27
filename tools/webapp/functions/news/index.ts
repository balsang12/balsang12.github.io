// 농마니 산야초 소식: 구글 뉴스 RSS(키 불필요)에서 산야초 관련 기사를 1시간마다 새로 받아 걸러서 돌려줍니다.
// 기사 본문은 저장·표시하지 않고 제목·언론사·날짜·원문 링크만 씁니다.
// 운영자가 직접 고른 기사(settings/site.newsPin)와 숨긴 기사(newsHide)는 앱 쪽에서 합칩니다.
import { createClient } from "jsr:@supabase/supabase-js@2";

const QUERIES = ["산나물", "약초 채취", "산삼", "송이버섯", "산양삼", "능이버섯", "더덕", "도라지 수확", "곰취", "산마늘 명이", "두릅", "고사리 채취", "오미자", "표고버섯", "천마", "황기", "헛개", "마가목", "오가피", "구기자", "독버섯", "독초 산나물"];
// 방송(TV)에서 산야초를 다룬 회차
const TV_QUERIES = ["한국기행 산나물", "한국기행 약초", "한국기행 버섯", "6시 내고향 버섯", "6시 내고향 산나물", "6시 내고향 약초", "나는 자연인이다 약초", "인간극장 산골", "생생정보 산나물", "극한직업 약초", "자연의 철학자들"];
const TV_TITLE = /한국기행|6시\s?내고향|나는 자연인이다|자연인|인간극장|생생정보|생방송 오늘|극한직업|자연의 철학자들|다큐|방영/;
// 제목에 산야초 사전의 이름(또는 다른 이름)이 하나라도 있어야 함. 다른 뜻으로 많이 쓰이는 낱말(은행·수영·상황·고삼·오디·명이 등)은 뺐음
const NAMES: string[] = ["갈황색미치광이버섯", "잉글리시라벤더", "붉은사슴뿔버섯", "번데기동충하초", "세인트존스워트", "개나리광대버섯", "독우산광대버섯", "뽕나무겨우살이", "노루궁뎅이버섯", "도둑놈의지팡이", "으름덩굴줄기", "망태말뚝버섯", "독흰갈대버섯", "놋젓가락나물", "미나리아재비", "삿갓외대버섯", "산사나무열매", "저먼캐모마일", "마귀광대버섯", "서양고추나물", "히비스커스차", "산괴불주머니", "마가목열매", "소엽맥문동", "각시둥굴레", "삼지구엽초", "고로쇠나무", "아쉬와간다", "레몬그래스", "꾀꼬리버섯", "왕고들빼기", "아카시아꽃", "레몬그라스", "꾸지뽕열매", "청미래덩굴", "디기탈리스", "까마중열매", "꽃송이버섯", "히비스커스", "산겨릅나무", "갯기름나물", "미치광이풀", "스위트바질", "가시오가피", "노루궁뎅이", "섬쑥부쟁이", "고려엉겅퀴", "광나무열매", "화살나무순", "미국자리공", "레몬글라스", "아슈와간다", "배암차즈기", "스테비아잎", "보리수열매", "누리장나무", "느타리버섯", "파드득나물", "아쉬아간다", "뽕나무버섯", "흰독말풀", "삿갓나물", "약도라지", "로즈메리", "영지버섯", "말굽버섯", "카모마일", "진달래꽃", "자귀나무", "황새냉이", "방풍나물", "아티초크", "퉁퉁마디", "천종산삼", "돌미나리", "맹종죽순", "가시연꽃", "인도인삼", "카바카바", "두메부추", "서양박하", "석이버섯", "잎새버섯", "엄나무순", "곰보배추", "닭의장풀", "동충하초", "때죽나무", "뿌리부추", "스테비아", "가래나무", "구름버섯", "뱀차즈기", "오가피순", "소경불알", "노란다발", "부지갱이", "마카뿌리", "광대나물", "오갈피순", "화살나무", "괴발딱취", "애기똥풀", "은방울꽃", "까치버섯", "화경버섯", "방풍뿌리", "명이나물", "송이버섯", "회화나무", "황벽나무", "얼음새꽃", "쥐똥나무", "상황버섯", "속썩은풀", "토종다래", "표고버섯", "아로니아", "레드비트", "박주가리", "개복숭아", "하늘타리", "버들여뀌", "개암나무", "지종산삼", "싸리버섯", "큰갓버섯", "눈개승마", "눈빛승마", "로즈마리", "컴프리잎", "돌복숭아", "동의나물", "깽깽이풀", "촛대승마", "느릅나무", "생강나무", "도꼬마리", "참죽나물", "붓순나무", "노박덩굴", "드럼스틱", "멍석딸기", "가죽나물", "능이버섯", "고욤나무", "개암버섯", "두충나무", "개옻나무", "쑥부쟁이", "블루베리", "인동덩굴", "환삼덩굴", "헛개열매", "지리강활", "아주까리", "음나무순", "망태버섯", "목이버섯", "주목나무", "비터멜론", "독미나리", "산뽕나무", "위타니아", "측백나무", "겨우살이", "비트루트", "고들빼기", "캐모마일", "으름열매", "백도라지", "황칠나무", "동박나무", "페퍼민트", "돼지감자", "고추냉이", "차가버섯", "모링가잎", "적하수오", "참비름", "음나무", "귀전우", "닥나무", "돈나물", "위령선", "석창포", "음양곽", "식방풍", "곤드레", "뽕나무", "개두릅", "쥐다래", "요힘베", "개똥쑥", "맥문동", "산머루", "초피잎", "상기생", "취오동", "참두릅", "갯방풍", "도토리", "합환피", "레몬밤", "참죽순", "익모초", "사철쑥", "둥굴레", "는쟁이", "밤버섯", "등대풀", "머윗대", "벌나무", "가시연", "토사자", "오갈피", "취나물", "산수유", "도라지", "단너삼", "장뇌삼", "개다래", "구절초", "교고람", "천남성", "땅두릅", "센나잎", "산작약", "돌나물", "산마늘", "참당귀", "갓버섯", "배초향", "자연삼", "으아리", "백굴채", "오배자", "생지황", "은조롱", "비비추", "함박꽃", "백수오", "보리수", "곤달비", "복분자", "참나물", "살구씨", "결명자", "돌단풍", "지구자", "백복령", "병풍쌈", "꾸지뽕", "어성초", "산대추", "백모근", "천화분", "엄나무", "백부자", "씀바귀", "병풍취", "칡뿌리", "백선피", "측백엽", "산사자", "하고초", "인동초", "작설차", "미역취", "얼레지", "산더덕", "시금초", "다래순", "상백피", "질경이", "약모밀", "창이자", "쇠무릎", "사프란", "풀솜대", "덩굴차", "바위솔", "찔레꽃", "삼나물", "옻나무", "비파잎", "어수리", "두릅순", "초룡담", "털머위", "쇠뜨기", "백자인", "금은화", "미나리", "자소엽", "샤프란", "해당화", "민들레", "쓴오이", "알더덕", "엉겅퀴", "하수오", "고로쇠", "오미자", "골담초", "원추리", "센나엽", "산초잎", "해동피", "차조기", "구릿대", "개미취", "명아주", "유근피", "현호색", "모링가", "달개비", "고사리", "궁궁이", "산딸기", "구기자", "컴프리", "조릿대", "피나물", "방아잎", "인진쑥", "여정실", "삼백초", "참시호", "큰조롱", "뚱딴지", "오가피", "붉나무", "독활순", "삼엽채", "산양삼", "토복령", "목련꽃", "느타리", "과루인", "쇠비름", "줄딸기", "마가목", "숙지황", "견우자", "천문동", "투구꽃", "요힘빈", "단풍취", "산부추", "백작약", "다래", "머루", "삼채", "돌배", "살구", "참쑥", "현삼", "창포", "독활", "참옻", "헛개", "매실", "우슬", "생강", "돌외", "작약", "삽주", "강활", "뽕잎", "고욤", "만삼", "함초", "울금", "앵두", "연근", "녹차", "황기", "두릅", "우엉", "지황", "바질", "당귀", "죽순", "대추", "감국", "홍삼", "개암", "더덕", "표고", "칡꽃", "곰취", "여뀌", "모과", "찔레", "약쑥", "복령", "야콘", "송이", "두충", "산삼", "순채", "연잎", "으름", "탱자", "참취", "잔대", "호두", "냉이", "머위", "인삼"];
const nameIn = (t: string) => NAMES.find((n) => t.includes(n)) || "";
// 건강 효능 기사, 엉뚱한 기사 제외
const BLOCK = /효능|효과|치료|예방|당뇨|혈압|혈당|항암|폐암|위암|간암|암 환자|암 예방|다이어트|면역|처방|복용|명약|보약|만병|드라마|배우|가수|아이돌|예능|주가|증시|코인|살인|성폭|마약|대마|광고|이벤트|할인|쿠폰|레시피|만드는\s?법|운세|신상|출시|선보|맛집|메뉴|브랜드|♥|열애|결혼|신랑수업|국화|천만송이|꽃송이|눈송이|물송이|복싱|축구|야구|골프|배구|씨름|마라톤|볼링/;
// 블로그·번역 사이트 등 언론사가 아닌 곳 제외
const BAD_SRC = /vietnam\.vn|브런치|티스토리|블로그|tistory|brunch|blog/i;
const H = { "Content-Type": "application/json; charset=utf-8", "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, apikey, content-type", "Cache-Control": "public, max-age=600" };

const ent = (s: string) => s.replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'").replace(/&amp;/g, "&");
const tag = (x: string, n: string) => { const m = x.match(new RegExp("<" + n + "(?:\\s[^>]*)?>([\\s\\S]*?)</" + n + ">")); return m ? ent(m[1]).trim() : ""; };

type It = { t: string; u: string; p: string; d: number; n?: string; tv?: boolean };
export function parseRss(xml: string) {
  const out: It[] = [];
  for (const m of xml.matchAll(/<item>([\s\S]*?)<\/item>/g)) {
    const x = m[1], p = tag(x, "source");
    let t = tag(x, "title").replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();
    if (p && t.endsWith(" - " + p)) t = t.slice(0, -(p.length + 3)).trim();
    const u = tag(x, "link"), d = Date.parse(tag(x, "pubDate")) || 0;
    if (t && /^https:\/\//.test(u)) out.push({ t, u, p, d });
  }
  return out;
}

export function pick(all: It[]) {
  // 같은 사건을 여러 언론사가 쓴 기사는 하나만: 낱말이 많이 겹치면 같은 기사로 봅니다.
  const words = (t: string) => new Set((t.match(/[가-힣]{2,}|\d[\d,.]*[가-힣%]*/g) || []).map((w) => w.replace(/(은|는|이|가|을|를|에|서|의|로|와|과|도)$/, "")).filter((w) => w.length >= 2));
  const same = (a: Set<string>, b: Set<string>) => { let n = 0; for (const w of a) if (b.has(w)) n++; return n >= 3 || (n >= 2 && n / Math.min(a.size, b.size || 1) > 0.6); };
  const seen = new Set<string>(), kept: Set<string>[] = [], out: typeof all = [], cut = Date.now() - 35 * 864e5;
  for (const x of all.map((x) => ({ ...x, n: nameIn(x.t) })).filter((x) => x.n && !BLOCK.test(x.t) && x.d > cut && !BAD_SRC.test(x.p)).sort((a, b) => b.d - a.d)) {
    const w = words(x.t);
    if (seen.has(x.u) || kept.some((k) => same(w, k))) continue; seen.add(x.u); kept.push(w);
    out.push({ ...x, tv: TV_TITLE.test(x.t) });
  }
  // 최신 24개 + 그 밖의 방송 기사 최대 3개까지 덧붙이고, 방송 기사 하나는 위쪽 3번째 안에 보이게
  const top = out.slice(0, 24);
  for (const x of out.slice(24)) if (x.tv && top.filter((y) => y.tv).length < 3) top.push(x);
  const i = top.findIndex((x) => x.tv);
  if (i > 2) top.splice(2, 0, top.splice(i, 1)[0]);
  return top;
}

async function fetchAll() {
  const all: It[] = [];
  let ok = 0;
  for (const q of [...QUERIES, ...TV_QUERIES]) {
    try {
      const r = await fetch("https://news.google.com/rss/search?hl=ko&gl=KR&ceid=KR:ko&q=" + encodeURIComponent(q + (TV_QUERIES.includes(q) ? " when:30d" : " when:14d")), { headers: { "User-Agent": "Mozilla/5.0 (nongmani news)" } });
      if (!r.ok) continue; ok++;
      all.push(...parseRss(await r.text()));
    } catch (_) { /* 한 검색어가 실패해도 나머지로 */ }
  }
  if (!ok) throw new Error("rss unavailable");
  return pick(all);
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: H });
  const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
  const { data: row } = await sb.from("news_cache").select("data,fetched_at").eq("id", "main").maybeSingle();
  const age = row ? Date.now() - Date.parse(row.fetched_at) : Infinity;
  if (row && age < 3600e3) return new Response(JSON.stringify({ items: row.data, at: row.fetched_at }), { headers: H });
  try {
    const items = await fetchAll();
    const at = new Date().toISOString();
    await sb.from("news_cache").upsert({ id: "main", data: items, fetched_at: at });
    return new Response(JSON.stringify({ items, at }), { headers: H });
  } catch (e) {
    return new Response(JSON.stringify({ items: row?.data || [], at: row?.fetched_at || null, status: "error", error: String(e).slice(0, 120) }), { headers: H });
  }
});
