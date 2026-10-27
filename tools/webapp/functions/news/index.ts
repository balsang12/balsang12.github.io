// 농마니 산야초 소식: 구글 뉴스 RSS(키 불필요)에서 산야초 관련 기사를 1시간마다 새로 받아 걸러서 돌려줍니다.
// 기사 본문은 저장·표시하지 않고 제목·언론사·날짜·원문 링크만 씁니다.
// 운영자가 직접 고른 기사(settings/site.newsPin)와 숨긴 기사(newsHide)는 앱 쪽에서 합칩니다.
import { createClient } from "jsr:@supabase/supabase-js@2";

const QUERIES = ["산나물", "약초 채취", "산삼", "송이버섯", "임산물", "산양삼", "능이버섯", "더덕 수확"];
// 제목에 하나라도 있어야 하는 단어
const MUST = /산나물|나물|약초|산삼|산양삼|장뇌삼|송이|능이|임산물|버섯|더덕|도라지|두릅|고사리|곰취|취나물|산림|채취|심마니|임업|산주|산약초|약용/;
// 건강 효능 기사, 엉뚱한 기사 제외
const BLOCK = /효능|효과|치료|예방|당뇨|혈압|혈당|항암|폐암|위암|간암|암 환자|암 예방|다이어트|면역|처방|복용|명약|보약|만병|드라마|배우|가수|아이돌|예능|주가|증시|코인|살인|성폭|마약|대마|광고|이벤트|할인|쿠폰|레시피|만드는\s?법|운세|신상|출시|선보|맛집|메뉴|브랜드|♥|열애|결혼|신랑수업|국화|천만송이|꽃송이|눈송이|물송이/;
// 블로그·번역 사이트 등 언론사가 아닌 곳 제외
const BAD_SRC = /vietnam\.vn|브런치|티스토리|블로그|tistory|brunch|blog/i;
const H = { "Content-Type": "application/json; charset=utf-8", "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, apikey, content-type", "Cache-Control": "public, max-age=600" };

const ent = (s: string) => s.replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'").replace(/&amp;/g, "&");
const tag = (x: string, n: string) => { const m = x.match(new RegExp("<" + n + "(?:\\s[^>]*)?>([\\s\\S]*?)</" + n + ">")); return m ? ent(m[1]).trim() : ""; };

export function parseRss(xml: string) {
  const out: { t: string; u: string; p: string; d: number }[] = [];
  for (const m of xml.matchAll(/<item>([\s\S]*?)<\/item>/g)) {
    const x = m[1], p = tag(x, "source");
    let t = tag(x, "title").replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();
    if (p && t.endsWith(" - " + p)) t = t.slice(0, -(p.length + 3)).trim();
    const u = tag(x, "link"), d = Date.parse(tag(x, "pubDate")) || 0;
    if (t && /^https:\/\//.test(u)) out.push({ t, u, p, d });
  }
  return out;
}

export function pick(all: { t: string; u: string; p: string; d: number }[]) {
  // 같은 사건을 여러 언론사가 쓴 기사는 하나만: 낱말이 많이 겹치면 같은 기사로 봅니다.
  const words = (t: string) => new Set((t.match(/[가-힣]{2,}|\d[\d,.]*[가-힣%]*/g) || []).map((w) => w.replace(/(은|는|이|가|을|를|에|서|의|로|와|과|도)$/, "")).filter((w) => w.length >= 2));
  const same = (a: Set<string>, b: Set<string>) => { let n = 0; for (const w of a) if (b.has(w)) n++; return n >= 3 || (n >= 2 && n / Math.min(a.size, b.size || 1) > 0.6); };
  const seen = new Set<string>(), kept: Set<string>[] = [], out: typeof all = [], cut = Date.now() - 30 * 864e5;
  for (const x of all.filter((x) => MUST.test(x.t) && !BLOCK.test(x.t) && x.d > cut && !BAD_SRC.test(x.p)).sort((a, b) => b.d - a.d)) {
    const w = words(x.t);
    if (seen.has(x.u) || kept.some((k) => same(w, k))) continue; seen.add(x.u); kept.push(w); out.push(x);
    if (out.length >= 20) break;
  }
  return out;
}

async function fetchAll() {
  const all: { t: string; u: string; p: string; d: number }[] = [];
  let ok = 0;
  for (const q of QUERIES) {
    try {
      const r = await fetch("https://news.google.com/rss/search?hl=ko&gl=KR&ceid=KR:ko&q=" + encodeURIComponent(q + " when:14d"), { headers: { "User-Agent": "Mozilla/5.0 (nongmani news)" } });
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
