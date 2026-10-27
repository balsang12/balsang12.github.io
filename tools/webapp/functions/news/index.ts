// 농마니 산야초 소식: 네이버 뉴스 검색 결과를 1시간마다 새로 받아 걸러서 돌려줍니다.
// 기사 본문은 저장·표시하지 않고 제목·언론사·날짜·원문 링크만 씁니다.
import { createClient } from "jsr:@supabase/supabase-js@2";

const QUERIES = ["산나물", "약초 채취", "산삼", "송이버섯", "임산물", "산양삼", "능이버섯", "더덕"];
// 제목에 하나라도 있어야 하는 단어
const MUST = /산나물|나물|약초|산삼|산양삼|장뇌삼|송이|능이|임산물|버섯|더덕|도라지|두릅|고사리|곰취|취나물|산림|채취|심마니|임업|산주|산약초|약용/;
// 건강 효능 기사, 엉뚱한 기사 제외
const BLOCK = /효능|효과|치료|예방|당뇨|혈압|혈당|항암|폐암|위암|간암|암 환자|암 예방|다이어트|면역|처방|복용|명약|보약|만병|드라마|배우|가수|아이돌|예능|주가|증시|코인|살인|성폭|마약|대마|광고|이벤트|할인|쿠폰|레시피|만드는\s?법|운세/;
const PRESS: Record<string, string> = {
  "yna.co.kr": "연합뉴스", "yonhapnewstv.co.kr": "연합뉴스TV", "nongmin.com": "농민신문", "newsis.com": "뉴시스", "news1.kr": "뉴스1",
  "kbs.co.kr": "KBS", "imbc.com": "MBC", "sbs.co.kr": "SBS", "ytn.co.kr": "YTN", "jtbc.co.kr": "JTBC", "chosun.com": "조선일보",
  "joongang.co.kr": "중앙일보", "donga.com": "동아일보", "hani.co.kr": "한겨레", "khan.co.kr": "경향신문", "hankookilbo.com": "한국일보",
  "mk.co.kr": "매일경제", "hankyung.com": "한국경제", "sedaily.com": "서울경제", "seoul.co.kr": "서울신문", "kmib.co.kr": "국민일보",
  "segye.com": "세계일보", "munhwa.com": "문화일보", "nocutnews.co.kr": "노컷뉴스", "ohmynews.com": "오마이뉴스", "edaily.co.kr": "이데일리",
  "asiae.co.kr": "아시아경제", "heraldcorp.com": "헤럴드경제", "fnnews.com": "파이낸셜뉴스", "mt.co.kr": "머니투데이", "newspim.com": "뉴스핌",
  "agrinet.co.kr": "한국농어민신문", "aflnews.co.kr": "농수축산신문", "ikpnews.net": "한국농정신문", "farminsight.net": "팜인사이트",
  "imaeil.com": "매일신문", "idaegu.com": "대구신문", "yeongnam.com": "영남일보", "kyongbuk.co.kr": "경북일보", "knnews.co.kr": "경남신문",
  "gnnews.co.kr": "경남일보", "kado.net": "강원도민일보", "kwnews.co.kr": "강원일보", "busan.com": "부산일보", "kookje.co.kr": "국제신문",
  "joongdo.co.kr": "중도일보", "daejonilbo.com": "대전일보", "jjan.kr": "전북일보", "kwangju.co.kr": "광주일보", "jemin.com": "제민일보",
  "kfn.co.kr": "한국산림신문", "forestnews.co.kr": "산림경영신문",
};
const H = { "Content-Type": "application/json; charset=utf-8", "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, apikey, content-type", "Cache-Control": "public, max-age=600" };
const clean = (s: string) => s.replace(/<[^>]+>/g, "").replace(/&quot;/g, '"').replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&#39;|&apos;/g, "'").replace(/\s+/g, " ").trim();
const press = (u: string) => { try { const h = new URL(u).hostname.replace(/^(www|m|news|n)\./, ""); for (const k in PRESS) if (h === k || h.endsWith("." + k)) return PRESS[k]; return h; } catch { return ""; } };

async function fetchNaver(id: string, secret: string) {
  const all: { t: string; u: string; p: string; d: number }[] = [];
  for (const q of QUERIES) {
    const r = await fetch("https://openapi.naver.com/v1/search/news.json?display=30&sort=date&query=" + encodeURIComponent(q), { headers: { "X-Naver-Client-Id": id, "X-Naver-Client-Secret": secret } });
    if (!r.ok) throw new Error("naver " + r.status);
    const j = await r.json();
    for (const it of j.items || []) {
      const t = clean(it.title || ""), u = it.originallink || it.link || "";
      if (!t || !u || !MUST.test(t) || BLOCK.test(t)) continue;
      all.push({ t, u, p: press(u), d: Date.parse(it.pubDate) || 0 });
    }
  }
  const seen = new Set<string>(), out: typeof all = [];
  for (const x of all.sort((a, b) => b.d - a.d)) {
    const k = x.t.replace(/[^가-힣a-zA-Z0-9]/g, "").slice(0, 14);
    if (seen.has(k) || seen.has(x.u)) continue; seen.add(k); seen.add(x.u); out.push(x);
    if (out.length >= 20) break;
  }
  return out;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: H });
  const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
  const { data: row } = await sb.from("news_cache").select("data,fetched_at").eq("id", "main").maybeSingle();
  const age = row ? Date.now() - Date.parse(row.fetched_at) : Infinity;
  if (row && age < 3600e3) return new Response(JSON.stringify({ items: row.data, at: row.fetched_at }), { headers: H });
  const id = Deno.env.get("NAVER_CLIENT_ID"), secret = Deno.env.get("NAVER_CLIENT_SECRET");
  if (!id || !secret) return new Response(JSON.stringify({ items: row?.data || [], status: "no_key" }), { headers: H });
  try {
    const items = await fetchNaver(id, secret);
    const at = new Date().toISOString();
    await sb.from("news_cache").upsert({ id: "main", data: items, fetched_at: at });
    return new Response(JSON.stringify({ items, at }), { headers: H });
  } catch (e) {
    return new Response(JSON.stringify({ items: row?.data || [], at: row?.fetched_at || null, status: "error", error: String(e).slice(0, 120) }), { headers: H });
  }
});
