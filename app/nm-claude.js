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

  var recovering = /type=recovery/.test(location.hash + location.search);
  var sessionReady = sb.auth.getSession().then(function (r) { return r.data.session || null; }).catch(function () { return null; });
  var RET_KEY = "nm_return";
  sessionReady.then(function (s) {
    var ret = null; try { ret = JSON.parse(localStorage.getItem(RET_KEY) || "null"); } catch (e) {}
    if (!s || !ret || recovering) return;
    try { localStorage.removeItem(RET_KEY); } catch (e) {}
    var here = location.origin + location.pathname;
    if (Date.now() - ret.t < 3600000 && ret.url.indexOf(location.origin + "/") === 0 && ret.url.split(/[?#]/)[0] !== here) location.replace(ret.url);
  });
  var who = null; // {id, admin, name, avatar}
  var whoReady = sessionReady.then(function (s) {
    if (!s) return null;
    return sb.rpc("whoami").then(function (r) { who = r.data || { id: s.user.id }; return who; }, function () { who = { id: s.user.id }; return who; });
  });
  // reload once when someone signs in or out in another tab, so the app restarts with the right account
  sb.auth.onAuthStateChange(function (ev) {
    if (ev === "PASSWORD_RECOVERY") { recovering = true; setTimeout(function () { openReset(); }, 50); return; }
    if (recovering) return;
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
    ".nmauth .nm-up{background:none;border:1px solid var(--pine,#2B5B41);color:var(--pine,#2B5B41);font-weight:700}.nmauth details summary{cursor:pointer;font-size:14px;color:var(--muted,#566659)}.nmauth [hidden]{display:none!important}" +
    ".nmauth .nm-or{text-align:center;font-size:13px;color:var(--muted,#566659)}.nmauth .nm-msg:empty{display:none}.nmauth .nm-msg{font-size:14px;color:var(--pine,#2B5B41)}.nmauth .nm-msg.nm-err{color:var(--berry,#A3324A)}";
  var T = {
    ko: { h: "농마니 로그인", p: "로그인하면 주문·입찰·판매를 할 수 있습니다. 처음이면 자동으로 가입됩니다.", kakao: "카카오로 시작하기", or: "또는 이메일로 받은 링크로 로그인", lbl: "이메일 주소", ph: "예: hong@naver.com", send: "로그인 링크 받기", close: "닫기",
      goKakao: "카카오로 이동합니다…", noKakao: "카카오 로그인을 준비 중입니다. 이메일로 로그인해 주세요.", badMail: "이메일 주소를 다시 확인해 주세요.", sending: "보내는 중…",
      rate: "잠시 뒤 다시 시도해 주세요. 메일을 너무 자주 요청했습니다.", fail: "메일을 보내지 못했습니다. 주소를 확인해 주세요.", sent: function (m) { return m + " 으로 로그인 링크를 보냈습니다. 메일함에서 링크를 누르면 로그인됩니다. (스팸함도 확인해 주세요)"; } },
    en: { h: "Sign in to Nongmani", p: "Sign in to bid. New here? An account is created automatically.", kakao: "Continue with Kakao", or: "or get a sign-in link by email", lbl: "Email address", ph: "you@example.com", send: "Email me a sign-in link", close: "Close",
      goKakao: "Opening Kakao…", noKakao: "Kakao sign-in is not ready yet. Please use email.", badMail: "Please check the email address.", sending: "Sending…",
      rate: "Too many requests. Please try again in a minute.", fail: "We could not send the email. Please check the address.", sent: function (m) { return "We sent a sign-in link to " + m + ". Open it to sign in (check spam too)."; } },
    "zh-Hant": { h: "登入農마니", p: "登入後即可出價。首次使用會自動建立帳號。", kakao: "使用 Kakao 登入", or: "或以電子郵件接收登入連結", lbl: "電子郵件", ph: "you@example.com", send: "寄送登入連結", close: "關閉",
      goKakao: "正在前往 Kakao…", noKakao: "Kakao 登入尚未開放，請使用電子郵件。", badMail: "請確認電子郵件地址。", sending: "寄送中…",
      rate: "請求過於頻繁，請稍後再試。", fail: "郵件寄送失敗，請確認地址。", sent: function (m) { return "登入連結已寄至 " + m + "，請點擊郵件中的連結登入（也請查看垃圾郵件）。"; } },
    ja: { h: "ノンマニにログイン", p: "ログインすると入札・注文ができます。初めての方は自動で登録されます。", kakao: "Kakaoでログイン", or: "またはメールで届くリンクでログイン", lbl: "メールアドレス", ph: "you@example.com", send: "ログインリンクを送る", close: "閉じる",
      goKakao: "Kakaoへ移動しています…", noKakao: "Kakaoログインは準備中です。メールでログインしてください。", badMail: "メールアドレスをご確認ください。", sending: "送信中…",
      rate: "リクエストが多すぎます。しばらくしてからお試しください。", fail: "メールを送信できませんでした。アドレスをご確認ください。", sent: function (m) { return m + " にログインリンクを送りました。メール内のリンクを開くとログインできます（迷惑メールフォルダもご確認ください）。"; } },
    "zh-Hans": { h: "登录农마니", p: "登录后即可出价。首次使用会自动创建账号。", kakao: "使用 Kakao 登录", or: "或通过电子邮件接收登录链接", lbl: "电子邮箱", ph: "you@example.com", send: "发送登录链接", close: "关闭",
      goKakao: "正在前往 Kakao…", noKakao: "Kakao 登录尚未开放，请使用电子邮箱。", badMail: "请确认电子邮箱地址。", sending: "发送中…",
      rate: "请求过于频繁，请稍后再试。", fail: "邮件发送失败，请确认地址。", sent: function (m) { return "登录链接已发送至 " + m + "，请点击邮件中的链接登录（也请查看垃圾邮件）。"; } }
  };

  var T2 = {
    ko: { p: "로그인하면 주문·입찰·판매를 할 수 있습니다.", pwH: "이메일과 비밀번호로", pwLbl: "비밀번호", pwPh: "8자 이상", pin: "로그인", up: "처음이에요 · 가입하기", forgot: "비밀번호를 잊으셨나요?", linkH: "비밀번호 없이 이메일 링크로 로그인",
      short: "비밀번호는 8자 이상으로 정해 주세요.", bad: "이메일이나 비밀번호가 맞지 않아요.", unconf: "가입 확인 메일의 링크를 먼저 한 번 눌러 주세요.", exists: "이미 가입된 이메일이에요. 위의 로그인을 눌러 주세요.",
      joined: "가입 신청을 받았습니다. 메일함의 확인 링크를 한 번 누르면 로그인됩니다. (스팸함도 확인해 주세요)", resetSent: function (m) { return m + " 으로 비밀번호를 새로 정하는 링크를 보냈습니다."; }, needMail: "이메일을 먼저 적어 주세요.",
      newH: "새 비밀번호 정하기", newSave: "새 비밀번호 저장", newOk: "비밀번호를 바꿨습니다. 이제 이 비밀번호로 로그인하세요.", wait: "확인 중…", show: "보기" },
    en: { p: "Sign in to order and bid.", pwH: "With email and password", pwLbl: "Password", pwPh: "8+ characters", pin: "Sign in", up: "New here? Create account", forgot: "Forgot your password?", linkH: "Or sign in with an email link (no password)",
      short: "Please use at least 8 characters.", bad: "Email or password is incorrect.", unconf: "Please open the confirmation link in your email first.", exists: "This email already has an account. Please sign in.",
      joined: "Almost done. Open the confirmation link in your email to sign in (check spam too).", resetSent: function (m) { return "We sent a password reset link to " + m + "."; }, needMail: "Please enter your email first.",
      newH: "Set a new password", newSave: "Save new password", newOk: "Password changed. You can sign in with it now.", wait: "Checking…", show: "Show" },
    ja: { p: "ログインすると入札・注文ができます。", pwH: "メールアドレスとパスワードで", pwLbl: "パスワード", pwPh: "8文字以上", pin: "ログイン", up: "はじめての方・新規登録", forgot: "パスワードをお忘れですか？", linkH: "パスワードなしでメールのリンクからログイン",
      short: "パスワードは8文字以上にしてください。", bad: "メールアドレスまたはパスワードが違います。", unconf: "先に登録確認メールのリンクを開いてください。", exists: "このメールアドレスは登録済みです。ログインしてください。",
      joined: "登録を受け付けました。メールの確認リンクを開くとログインできます（迷惑メールもご確認ください）。", resetSent: function (m) { return m + " にパスワード再設定のリンクを送りました。"; }, needMail: "先にメールアドレスを入力してください。",
      newH: "新しいパスワードを設定", newSave: "新しいパスワードを保存", newOk: "パスワードを変更しました。", wait: "確認中…", show: "表示" },
    "zh-Hans": { p: "登录后即可下单和出价。", pwH: "使用邮箱和密码", pwLbl: "密码", pwPh: "至少8位", pin: "登录", up: "首次使用 · 注册", forgot: "忘记密码？", linkH: "或不用密码，通过邮件链接登录",
      short: "密码至少需要8位。", bad: "邮箱或密码不正确。", unconf: "请先点击注册确认邮件中的链接。", exists: "该邮箱已注册，请直接登录。",
      joined: "已收到注册，请点击邮件中的确认链接完成登录（也请查看垃圾邮件）。", resetSent: function (m) { return "已向 " + m + " 发送重设密码的链接。"; }, needMail: "请先填写邮箱。",
      newH: "设置新密码", newSave: "保存新密码", newOk: "密码已修改。", wait: "确认中…", show: "显示" }
  };
  T2["zh-Hant"] = T2["zh-Hans"];
  Object.keys(T2).forEach(function (k) { if (T[k]) Object.keys(T2[k]).forEach(function (x) { T[k][x] = T2[k][x]; }); });
  function L() { return T[window.NM_LANG] || T.ko; }
  function remember() { try { localStorage.setItem(RET_KEY, JSON.stringify({ url: location.href.split("#")[0], t: Date.now() })); } catch (e) {} }
  var el = null, elLang = null;
  function build() {
    if (el && elLang !== (window.NM_LANG || "ko")) { el.remove(); el = null; }
    if (el) return el;
    if (!document.getElementById("nmAuthCss")) { var st = document.createElement("style"); st.id = "nmAuthCss"; st.textContent = css; document.head.appendChild(st); }
    var t = L(); elLang = window.NM_LANG || "ko";
    el = document.createElement("div"); el.className = "nmauth"; el.hidden = true; el.setAttribute("role", "dialog"); el.setAttribute("aria-modal", "true"); el.setAttribute("aria-labelledby", "nmAuthH");
    var lab = 'style="font-size:14px;color:var(--muted,#566659)"';
    el.innerHTML = '<div class="box"><h2 id="nmAuthH"></h2><p id="nmAuthP"></p>' +
      '<div id="nmMain" style="display:flex;flex-direction:column;gap:12px">' +
      '<button type="button" class="nm-kakao" id="nmKakao"></button>' +
      '<div class="nm-or" id="nmPwH"></div>' +
      '<form id="nmPwForm" style="display:flex;flex-direction:column;gap:8px">' +
        '<label for="nmPwMail" id="nmPwMailL" ' + lab + '></label><input id="nmPwMail" type="email" autocomplete="email" inputmode="email" required>' +
        '<label for="nmPw" id="nmPwL" ' + lab + '></label><div style="display:flex;gap:6px"><input id="nmPw" type="password" autocomplete="current-password" minlength="8" required style="flex:1;min-width:0"><button type="button" id="nmPwShow" class="nm-close" style="min-height:48px"></button></div>' +
        '<button class="nm-mail" type="submit" id="nmPwIn"></button>' +
        '<button type="button" class="nm-up" id="nmPwUp"></button>' +
        '<button type="button" class="nm-close" id="nmForgot" style="text-decoration:underline"></button>' +
      '</form>' +
      '<details class="nm-link"><summary id="nmLinkH"></summary>' +
      '<form id="nmMailForm" style="display:flex;flex-direction:column;gap:8px;margin-top:8px"><label for="nmMail" id="nmMailL" ' + lab + '></label><input id="nmMail" type="email" autocomplete="email" inputmode="email" required><button class="nm-mail" type="submit" id="nmSend"></button></form>' +
      '</details></div>' +
      '<form id="nmNewForm" hidden style="display:flex;flex-direction:column;gap:8px"><label for="nmNewPw" id="nmNewL" ' + lab + '></label><input id="nmNewPw" type="password" autocomplete="new-password" minlength="8" required><button class="nm-mail" type="submit" id="nmNewSave"></button></form>' +
      '<div class="nm-msg" id="nmMsg" role="status"></div><button type="button" class="nm-close" id="nmClose"></button></div>';
    [["#nmAuthH", t.h], ["#nmAuthP", t.p], ["#nmKakao", t.kakao], ["#nmPwH", t.pwH], ["#nmPwMailL", t.lbl], ["#nmPwL", t.pwLbl], ["#nmPwShow", t.show], ["#nmPwIn", t.pin], ["#nmPwUp", t.up], ["#nmForgot", t.forgot],
     ["#nmLinkH", t.linkH], ["#nmMailL", t.lbl], ["#nmSend", t.send], ["#nmNewL", t.newH], ["#nmNewSave", t.newSave], ["#nmClose", t.close]].forEach(function (x) { el.querySelector(x[0]).textContent = x[1]; });
    el.querySelector("#nmMail").placeholder = t.ph; el.querySelector("#nmPwMail").placeholder = t.ph; el.querySelector("#nmPw").placeholder = t.pwPh; el.querySelector("#nmNewPw").placeholder = t.pwPh;
    document.body.appendChild(el);
    el.addEventListener("click", function (e) { if (e.target === el) close(); });
    el.querySelector("#nmClose").onclick = close;
    el.querySelector("#nmKakao").onclick = function () {
      say(t.goKakao); remember();
      sb.auth.signInWithOAuth({ provider: "kakao", options: { redirectTo: APP_URL } }).then(function (r) {
        if (r.error) say(t.noKakao, true);
      });
    };
    el.querySelector("#nmMailForm").onsubmit = function (e) {
      e.preventDefault();
      var m = el.querySelector("#nmMail").value.trim();
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(m)) { say(t.badMail, true); return; }
      say(t.sending); remember();
      sb.auth.signInWithOtp({ email: m, options: { emailRedirectTo: APP_URL } }).then(function (r) {
        if (r.error) say(/rate/i.test(r.error.message) ? t.rate : t.fail, true);
        else say(t.sent(m));
      });
    };
    var pwMail = function () { return el.querySelector("#nmPwMail").value.trim(); }, pw = function () { return el.querySelector("#nmPw").value; };
    var okMail = function (m) { return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(m); };
    el.querySelector("#nmPwShow").onclick = function () { var i = el.querySelector("#nmPw"); i.type = i.type === "password" ? "text" : "password"; };
    el.querySelector("#nmPwForm").onsubmit = function (e) {
      e.preventDefault(); var m = pwMail();
      if (!okMail(m)) { say(t.badMail, true); return; }
      say(t.wait); remember();
      sb.auth.signInWithPassword({ email: m, password: pw() }).then(function (r) {
        if (!r.error) { say(""); close(); return; }
        var em = String(r.error.message || "");
        say(/confirm/i.test(em) ? t.unconf : /rate/i.test(em) ? t.rate : t.bad, true);
      });
    };
    el.querySelector("#nmPwUp").onclick = function () {
      var m = pwMail(), p = pw();
      if (!okMail(m)) { say(t.badMail, true); return; }
      if (p.length < 8) { say(t.short, true); return; }
      say(t.wait); remember();
      sb.auth.signUp({ email: m, password: p, options: { emailRedirectTo: APP_URL } }).then(function (r) {
        var em = String((r.error && r.error.message) || "");
        if (r.error) { say(/registered|exists/i.test(em) ? t.exists : /rate/i.test(em) ? t.rate : /password/i.test(em) ? t.short : t.fail, true); return; }
        if (r.data && r.data.session) { close(); return; }
        if (r.data && r.data.user && Array.isArray(r.data.user.identities) && r.data.user.identities.length === 0) { say(t.exists, true); return; }
        say(t.joined);
      });
    };
    el.querySelector("#nmForgot").onclick = function () {
      var m = pwMail(); if (!okMail(m)) { say(t.needMail, true); el.querySelector("#nmPwMail").focus(); return; }
      say(t.sending);
      sb.auth.resetPasswordForEmail(m, { redirectTo: APP_URL }).then(function (r) { if (r.error) say(/rate/i.test(r.error.message) ? t.rate : t.fail, true); else say(t.resetSent(m)); });
    };
    el.querySelector("#nmNewForm").onsubmit = function (e) {
      e.preventDefault(); var p = el.querySelector("#nmNewPw").value;
      if (p.length < 8) { say(t.short, true); return; }
      say(t.wait);
      sb.auth.updateUser({ password: p }).then(function (r) { if (r.error) say(t.fail, true); else { say(t.newOk); setTimeout(function () { location.replace(APP_URL); }, 1200); } });
    };
    if (!build.keyed) { build.keyed = true; document.addEventListener("keydown", function (e) { if (e.key === "Escape" && el && !el.hidden) close(); }); }
    return el;
  }
  function say(t, bad) { var m = el.querySelector("#nmMsg"); m.textContent = t; m.className = "nm-msg" + (bad ? " nm-err" : ""); }
  function open(reason) { build(); document.querySelectorAll("dialog[open]").forEach(function (d) { try { d.close(); } catch (e) {} }); el.hidden = false; say(reason || ""); setTimeout(function () { el.querySelector("#nmPwMail").focus(); }, 30); }
  function openReset() { build(); el.querySelector("#nmMain").hidden = true; el.querySelector("#nmNewForm").hidden = false; el.querySelector("#nmNewForm").style.display = "flex"; el.hidden = false; say(""); }
  function close() { if (el) el.hidden = true; }

  window.nmAuth = Object.freeze({
    open: open, close: close,
    signOut: function () { return sb.auth.signOut().then(function () { location.reload(); }); },
    session: function () { return sessionReady; },
    mgrFind: function (hash) { return sb.rpc("mgr_find", { p_hash: hash }).then(function (r) { return r.data || null; }, function () { return null; }); }
  });
})();
