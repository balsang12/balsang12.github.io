/* 농마니: the app was written for claude.ai's window.claude.use("db"|"user").
   This file provides the same calls on top of Supabase, so the app code stays the same.
   Data lives in public.docs (col, id, data); access rules are enforced in the database. */
(function () {
  "use strict";
  var SB_URL = "https://vxgydzjyzhjxvqaeludh.supabase.co";
  var SB_KEY = "sb_publishable_4MyQuV4WbsSnyIdE_s8XIQ_cfRlY6tz";
  var APP_URL = location.origin + location.pathname.replace(/[^/]*$/, "");

  var sb = window.supabase.createClient(SB_URL, SB_KEY, {
    auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true, flowType: "pkce" },
    realtime: { params: { eventsPerSecond: 5 } }
  });
  window.nmSupabase = sb;

  var sessionReady = sb.auth.getSession().then(function (r) { return r.data.session || null; }).catch(function () { return null; });
  var who = null; // {id, admin, name, avatar}
  var whoReady = sessionReady.then(function (s) {
    if (!s) return null;
    return sb.rpc("whoami").then(function (r) { who = r.data || { id: s.user.id }; return who; }, function () { who = { id: s.user.id }; return who; });
  });
  // reload once when someone signs in or out in another tab, so the app restarts with the right account
  sb.auth.onAuthStateChange(function (ev) {
    if (ev === "SIGNED_OUT" || ev === "SIGNED_IN") {
      sessionReady.then(function (s) {
        var had = !!s;
        if ((ev === "SIGNED_IN" && !had) || (ev === "SIGNED_OUT" && had)) location.reload();
      });
    }
  });

  /* ---------- errors in the shape the app expects ---------- */
  function mkErr(code, msg) { var e = new Error(msg); e.code = code; e.msg = msg; e.mine = true; return e; }
  function mapErr(e) {
    var m = (e && (e.message || e.details || "")) + "";
    if (/login_required/.test(m) || (!who && /row-level security|permission denied/i.test(m))) return mkErr("login", "로그인이 필요합니다");
    if (/not_yours|admin_only|row-level security|permission denied|42501/i.test(m) || (e && e.code === "42501")) return mkErr("denied", "이 작업을 할 권한이 없습니다");
    if (/not_found|P0002/.test(m) || (e && e.code === "P0002")) return mkErr("not_found", "대상을 찾을 수 없습니다. 새로고침 후 다시 시도해 주세요");
    if (/fetch|network|Failed to fetch/i.test(m)) return mkErr("unavailable", "인터넷 연결을 확인해 주세요");
    return mkErr("unavailable", "저장하지 못했습니다. 잠시 뒤 다시 시도해 주세요");
  }

  /* ---------- paths ---------- */
  function splitDoc(path) {
    var p = String(path).split("/");
    if (p.length % 2) throw new TypeError("document path needs an even number of segments: " + path);
    return { col: p.slice(0, -1).join("/"), id: p[p.length - 1] };
  }
  function newId() {
    var a = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789", s = "", r = new Uint8Array(20);
    crypto.getRandomValues(r); for (var i = 0; i < 20; i++) s += a[r[i] % 62]; return s;
  }
  function clean(o) { return JSON.parse(JSON.stringify(o == null ? {} : o)); }

  /* ---------- snapshots ---------- */
  function docSnap(id, data) {
    var frozen = data ? Object.freeze(data) : undefined;
    return { id: id, exists: !!data, data: function () { return frozen; }, metadata: { fromCache: false, hasPendingWrites: false } };
  }
  function querySnap(rows, prev) {
    var docs = rows.map(function (r) { return docSnap(r.id, r.data); });
    var prevIds = prev ? prev.map(function (d) { return d.id; }) : [];
    return {
      docs: docs, size: docs.length, empty: !docs.length, metadata: { fromCache: false, hasPendingWrites: false },
      docChanges: function () {
        return docs.map(function (d, i) { return { type: prevIds.indexOf(d.id) < 0 ? "added" : "modified", doc: d, oldIndex: prevIds.indexOf(d.id), newIndex: i }; });
      }
    };
  }

  /* ---------- live updates: one realtime channel, listeners per collection ---------- */
  var listeners = {}; // col -> Set of refresh functions
  var channel = null;
  function ensureChannel() {
    if (channel) return;
    channel = sb.channel("nm-docs")
      .on("postgres_changes", { event: "*", schema: "public", table: "docs" }, function (p) {
        var col = (p.new && p.new.col) || (p.old && p.old.col);
        bump(col);
      })
      .subscribe();
  }
  function bump(col) {
    var set = listeners[col]; if (!set) return;
    set.forEach(function (fn) { fn(); });
  }
  // safety net when the realtime socket drops: refresh visible listeners every 45 s
  setInterval(function () {
    if (document.visibilityState !== "visible") return;
    Object.keys(listeners).forEach(bump);
  }, 45000);

  /* ---------- queries ---------- */
  function Query(col, f) {
    this.col = col; this.f = f || { where: [], order: null, lim: 1000 };
  }
  Query.prototype._with = function (k, v) {
    var f = { where: this.f.where.slice(), order: this.f.order, lim: this.f.lim };
    if (k === "where") f.where.push(v); else f[k] = v;
    return new Query(this.col, f);
  };
  Query.prototype.where = function (field, op, value) { return this._with("where", [field, op, value]); };
  Query.prototype.orderBy = function (field, dir) { return this._with("order", [field, dir || "asc"]); };
  Query.prototype.limit = function (n) { return this._with("lim", Math.max(1, Math.min(1000, n | 0))); };
  Query.prototype._fetch = function () {
    var q = sb.from("docs").select("id,data").eq("col", this.col);
    this.f.where.forEach(function (w) {
      var f = w[0], op = w[1], v = w[2], txt = "data->>" + f, js = "data->" + f;
      if (op === "==") q = (v === null ? q.is(js, null) : q.eq(txt, String(v)));
      else if (op === "!=") q = q.neq(txt, String(v));
      else if (op === "array-contains") q = q.filter(js, "cs", JSON.stringify([v]));
      else if (op === "in") q = q.in(txt, v.map(String));
      else if (op === "not-in") q = q.not(txt, "in", "(" + v.map(function (x) { return '"' + String(x).replace(/"/g, '\\"') + '"'; }).join(",") + ")");
      else if (op === "<") q = q.lt(js, v); else if (op === "<=") q = q.lte(js, v);
      else if (op === ">") q = q.gt(js, v); else if (op === ">=") q = q.gte(js, v);
    });
    q = this.f.order ? q.order("data->" + this.f.order[0], { ascending: this.f.order[1] !== "desc" }) : q.order("id", { ascending: true });
    return q.limit(this.f.lim).then(function (r) { if (r.error) throw mapErr(r.error); return r.data || []; });
  };
  Query.prototype.get = function () { return this._fetch().then(function (rows) { return querySnap(rows); }); };
  Query.prototype.onSnapshot = function (next, error) {
    var self = this, alive = true, prev = null, timer = null, busy = false, again = false;
    function run() {
      if (!alive) return;
      if (busy) { again = true; return; }
      busy = true;
      self._fetch().then(function (rows) {
        if (!alive) return;
        var snap = querySnap(rows, prev); prev = snap.docs;
        try { next(snap); } catch (e) { setTimeout(function () { throw e; }); }
      }, function (e) { if (alive && error) { try { error(e); } catch (x) {} } })
        .then(function () { busy = false; if (again) { again = false; schedule(); } });
    }
    function schedule() { clearTimeout(timer); timer = setTimeout(run, 250); }
    (listeners[self.col] = listeners[self.col] || new Set()).add(schedule);
    ensureChannel();
    sessionReady.then(run);
    return function () { alive = false; clearTimeout(timer); var s = listeners[self.col]; if (s) s.delete(schedule); };
  };

  function Collection(col) { Query.call(this, col); this.path = col; }
  Collection.prototype = Object.create(Query.prototype);
  Collection.prototype.doc = function (id) { return new DocRef(this.col, id == null ? newId() : String(id)); };
  Collection.prototype.add = function (data) { var ref = this.doc(); return ref.set(data).then(function () { return ref; }); };

  /* ---------- documents ---------- */
  function DocRef(col, id) { this.col = col; this.id = id; this.path = col + "/" + id; }
  DocRef.prototype.get = function () {
    var id = this.id;
    return sb.from("docs").select("id,data").eq("col", this.col).eq("id", id).maybeSingle()
      .then(function (r) { if (r.error) throw mapErr(r.error); return docSnap(id, r.data ? r.data.data : undefined); });
  };
  DocRef.prototype.set = function (data) {
    var col = this.col;
    return sb.from("docs").upsert({ col: col, id: this.id, data: clean(data) }, { onConflict: "col,id" })
      .then(function (r) { if (r.error) throw mapErr(r.error); bump(col); });
  };
  DocRef.prototype.update = function (patch) {
    var col = this.col, p = clean(patch), remove = [];
    Object.keys(patch || {}).forEach(function (k) { if (patch[k] === undefined) remove.push(k); });
    return sb.rpc("doc_update", { p_col: col, p_id: this.id, p_patch: p, p_remove: remove })
      .then(function (r) { if (r.error) throw mapErr(r.error); bump(col); });
  };
  DocRef.prototype.delete = function () {
    var col = this.col;
    return sb.from("docs").delete().eq("col", col).eq("id", this.id)
      .then(function (r) { if (r.error) throw mapErr(r.error); bump(col); });
  };
  DocRef.prototype.collection = function (sub) { return new Collection(this.path + "/" + sub); };
  DocRef.prototype.onSnapshot = function (next, error) {
    return Query.prototype._docListener.call({ col: this.col }, this.id, next, error);
  };
  Query.prototype._docListener = function (id, next, error) {
    var col = this.col, alive = true, timer = null;
    function run() {
      if (!alive) return;
      new DocRef(col, id).get().then(function (s) { if (alive) next(s); }, function (e) { if (alive && error) error(e); });
    }
    function schedule() { clearTimeout(timer); timer = setTimeout(run, 250); }
    (listeners[col] = listeners[col] || new Set()).add(schedule);
    ensureChannel(); sessionReady.then(run);
    return function () { alive = false; var s = listeners[col]; if (s) s.delete(schedule); };
  };
  DocRef.prototype.acquire = function () { return Promise.resolve({ acquired: true }); };

  var db = Object.freeze({
    doc: function (path) { var p = splitDoc(path); return new DocRef(p.col, p.id); },
    collection: function (path) {
      if (String(path).split("/").length % 2 === 0) throw new TypeError("collection path needs an odd number of segments: " + path);
      return new Collection(String(path));
    }
  });

  /* ---------- who is viewing ---------- */
  var user = Object.freeze({
    id: function () { return whoReady.then(function (w) { return w ? w.id : null; }); },
    me: function () { return whoReady.then(function (w) { return w ? { id: w.id, name: w.name || "", avatarUrl: w.avatar || "" } : { id: null, name: "", avatarUrl: "" }; }); },
    isOwner: function () { return whoReady.then(function (w) { return !!(w && w.admin); }); },
    canEdit: function () { return whoReady.then(function (w) { return !!(w && w.admin); }); },
    can: function (what) { return whoReady.then(function (w) { return what === "data.write" ? !!w : null; }); },
    profiles: function (ids) {
      ids = (ids || []).filter(Boolean).slice(0, 200);
      if (!ids.length) return Promise.resolve({});
      return sb.rpc("profile_names", { p_ids: ids }).then(function (r) {
        var out = {}; (r.data || []).forEach(function (x) { out[x.id] = { id: x.id, name: x.name || "" }; }); return out;
      }, function () { return {}; });
    },
    search: function () { return Promise.resolve([]); }
  });

  window.claude = Object.freeze({
    use: function (name) {
      if (name === "db") return Promise.resolve(db);
      if (name === "user") return Promise.resolve(user);
      return Promise.resolve(null); // sample, assets, etc. are not offered on the public site
    }
  });

  /* ---------- sign in ---------- */
  var css = ".nmauth{position:fixed;inset:0;z-index:9999;background:rgba(10,20,14,.55);display:grid;place-items:center;padding:16px}" +
    ".nmauth[hidden]{display:none}.nmauth .box{background:var(--surface,#fff);color:var(--ink,#15201A);border-radius:18px;max-width:380px;width:100%;padding:22px 20px;display:flex;flex-direction:column;gap:12px;font:16px/1.6 var(--body,system-ui,sans-serif);box-shadow:0 10px 40px rgba(0,0,0,.25)}" +
    ".nmauth h2{margin:0;font:700 22px/1.3 var(--display,serif);color:var(--pine,#2B5B41)}.nmauth p{margin:0;color:var(--muted,#566659);font-size:15px}" +
    ".nmauth button,.nmauth input{font:inherit;border-radius:12px;padding:13px 14px;min-height:48px}" +
    ".nmauth .nm-kakao{background:#FEE500;color:#191600;border:0;font-weight:700}.nmauth .nm-mail{background:var(--pine,#2B5B41);color:var(--pine-ink,#fff);border:0;font-weight:700}" +
    ".nmauth input{border:1px solid var(--line,#D3DCCD);background:var(--bg,#F4F6F1);color:inherit}.nmauth .nm-close{background:none;border:0;color:var(--muted,#566659);min-height:40px}" +
    ".nmauth .nm-or{text-align:center;font-size:13px;color:var(--muted,#566659)}.nmauth .nm-msg:empty{display:none}.nmauth .nm-msg{font-size:14px;color:var(--pine,#2B5B41)}.nmauth .nm-msg.nm-err{color:var(--berry,#A3324A)}";
  var el = null;
  function build() {
    if (el) return el;
    var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
    el = document.createElement("div"); el.className = "nmauth"; el.hidden = true; el.setAttribute("role", "dialog"); el.setAttribute("aria-modal", "true"); el.setAttribute("aria-labelledby", "nmAuthH");
    el.innerHTML = '<div class="box"><h2 id="nmAuthH">농마니 로그인</h2><p>로그인하면 주문·입찰·판매를 할 수 있습니다. 처음이면 자동으로 가입됩니다.</p>' +
      '<button type="button" class="nm-kakao" id="nmKakao">카카오로 시작하기</button>' +
      '<div class="nm-or">또는 이메일로 받은 링크로 로그인</div>' +
      '<form id="nmMailForm" style="display:flex;flex-direction:column;gap:8px"><label for="nmMail" style="font-size:14px;color:var(--muted,#566659)">이메일 주소</label><input id="nmMail" type="email" autocomplete="email" inputmode="email" placeholder="예: hong@naver.com" required><button class="nm-mail" type="submit">로그인 링크 받기</button></form>' +
      '<div class="nm-msg" id="nmMsg" role="status"></div><button type="button" class="nm-close" id="nmClose">닫기</button></div>';
    document.body.appendChild(el);
    el.addEventListener("click", function (e) { if (e.target === el) close(); });
    el.querySelector("#nmClose").onclick = close;
    el.querySelector("#nmKakao").onclick = function () {
      say("카카오로 이동합니다…");
      sb.auth.signInWithOAuth({ provider: "kakao", options: { redirectTo: APP_URL } }).then(function (r) {
        if (r.error) say("카카오 로그인을 준비 중입니다. 이메일로 로그인해 주세요.", true);
      });
    };
    el.querySelector("#nmMailForm").onsubmit = function (e) {
      e.preventDefault();
      var m = el.querySelector("#nmMail").value.trim();
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(m)) { say("이메일 주소를 다시 확인해 주세요.", true); return; }
      say("보내는 중…");
      sb.auth.signInWithOtp({ email: m, options: { emailRedirectTo: APP_URL } }).then(function (r) {
        if (r.error) say(/rate/i.test(r.error.message) ? "잠시 뒤 다시 시도해 주세요. 메일을 너무 자주 요청했습니다." : "메일을 보내지 못했습니다. 주소를 확인해 주세요.", true);
        else say(m + " 으로 로그인 링크를 보냈습니다. 메일함에서 링크를 누르면 로그인됩니다. (스팸함도 확인해 주세요)");
      });
    };
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !el.hidden) close(); });
    return el;
  }
  function say(t, bad) { var m = el.querySelector("#nmMsg"); m.textContent = t; m.className = "nm-msg" + (bad ? " nm-err" : ""); }
  function open(reason) { build(); el.hidden = false; say(reason || ""); setTimeout(function () { el.querySelector("#nmKakao").focus(); }, 30); }
  function close() { if (el) el.hidden = true; }

  window.nmAuth = Object.freeze({
    open: open, close: close,
    signOut: function () { return sb.auth.signOut().then(function () { location.reload(); }); },
    session: function () { return sessionReady; },
    mgrFind: function (hash) { return sb.rpc("mgr_find", { p_hash: hash }).then(function (r) { return r.data || null; }, function () { return null; }); }
  });
})();
