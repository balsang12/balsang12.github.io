// Stand-in for vendor/supabase.js in browser tests: same calls, data from window.__D, no network.
(function () {
  var D = window.__D || {};
  var rows = [];
  Object.keys(D).forEach(function (col) { Object.keys(D[col]).forEach(function (id) { rows.push({ col: col, id: id, data: JSON.parse(JSON.stringify(D[col][id])) }); }); });
  window.__rows = rows;
  window.__calls = [];
  var session = window.__SESSION || null;
  function get(o, path) { // "data->>x" / "data->x"
    var m = /^data->>?(.+)$/.exec(path); if (!m) return o[path];
    var v = o.data ? o.data[m[1]] : undefined; return /->>/.test(path) ? (v == null ? null : (typeof v === "object" ? JSON.stringify(v) : String(v))) : v;
  }
  function Builder() { this.f = []; this.ord = null; this.lim = 1e9; this.op = "select"; this.single = false; }
  var B = Builder.prototype;
  B.select = function () { return this; };
  B.eq = function (c, v) { this.f.push(function (r) { return String(get(r, c)) === String(v); }); return this; };
  B.neq = function (c, v) { this.f.push(function (r) { return String(get(r, c)) !== String(v); }); return this; };
  B.is = function (c, v) { this.f.push(function (r) { return get(r, c) == null; }); return this; };
  B.in = function (c, vs) { this.f.push(function (r) { return vs.indexOf(String(get(r, c))) >= 0; }); return this; };
  B.not = function () { return this; };
  B.filter = function (c, op, v) { var want = JSON.parse(v); this.f.push(function (r) { var a = get(r, c) || []; return want.every(function (x) { return a.indexOf(x) >= 0; }); }); return this; };
  ["lt", "lte", "gt", "gte"].forEach(function (k) { B[k] = function (c, v) { this.f.push(function (r) { var x = get(r, c); return k === "lt" ? x < v : k === "lte" ? x <= v : k === "gt" ? x > v : x >= v; }); return this; }; });
  B.order = function (c, o) { this.ord = [c, o && o.ascending === false]; return this; };
  B.limit = function (n) { this.lim = n; return this; };
  B.maybeSingle = function () { this.single = true; return this; };
  B.upsert = function (row) { this.op = "upsert"; this.row = row; return this; };
  B.delete = function () { this.op = "delete"; return this; };
  B.then = function (ok, bad) {
    var self = this;
    return new Promise(function (res) {
      setTimeout(function () {
        var match = rows.filter(function (r) { return self.f.every(function (fn) { return fn(r); }); });
        if (self.op === "upsert") {
          if (!session) return res({ error: { message: "login_required", code: "42501" } });
          window.__calls.push(["upsert", self.row.col, self.row.id, self.row.data]);
          var ex = rows.find(function (r) { return r.col === self.row.col && r.id === self.row.id; });
          if (ex) ex.data = self.row.data; else rows.push({ col: self.row.col, id: self.row.id, data: self.row.data });
          return res({ error: null });
        }
        if (self.op === "delete") {
          if (!session) return res({ error: { message: "login_required", code: "42501" } });
          match.forEach(function (m) { rows.splice(rows.indexOf(m), 1); });
          window.__calls.push(["delete", match.length]);
          return res({ error: null });
        }
        if (self.ord) { var c = self.ord[0], d = self.ord[1]; match.sort(function (a, b) { var x = get(a, c), y = get(b, c); return (x > y ? 1 : x < y ? -1 : 0) * (d ? -1 : 1); }); }
        match = match.slice(0, self.lim).map(function (r) { return { id: r.id, data: JSON.parse(JSON.stringify(r.data)) }; });
        res(self.single ? { data: match[0] || null, error: null } : { data: match, error: null });
      }, 5);
    }).then(ok, bad);
  };
  window.supabase = {
    createClient: function () {
      return {
        auth: {
          getSession: function () { return Promise.resolve({ data: { session: session } }); },
          onAuthStateChange: function () { return { data: { subscription: { unsubscribe: function () {} } } }; },
          signInWithOtp: function (o) { window.__calls.push(["otp", o.email]); return Promise.resolve({ error: null }); },
          signInWithOAuth: function (o) { window.__calls.push(["oauth", o.provider]); return Promise.resolve({ error: { message: "provider not enabled" } }); },
          signOut: function () { return Promise.resolve({}); }
        },
        from: function () { return new Builder(); },
        rpc: function (name, a) {
          window.__calls.push(["rpc", name, a]);
          if (name === "whoami") return Promise.resolve({ data: session ? { id: session.user.id, admin: !!window.__ADMIN, name: "테스터", avatar: "" } : null });
          if (name === "profile_names") return Promise.resolve({ data: a.p_ids.map(function (i) { return { id: i, name: "이름" + i }; }) });
          if (name === "mgr_find") return Promise.resolve({ data: window.__MGR || null });
          if (name === "doc_update") {
            if (!session) return Promise.resolve({ error: { message: "login_required" } });
            var r = rows.find(function (x) { return x.col === a.p_col && x.id === a.p_id; });
            if (!r) return Promise.resolve({ error: { message: "not_found", code: "P0002" } });
            Object.assign(r.data, a.p_patch); (a.p_remove || []).forEach(function (k) { delete r.data[k]; });
            return Promise.resolve({ data: r.data, error: null });
          }
          return Promise.resolve({ data: null });
        },
        channel: function () { return { on: function () { return this; }, subscribe: function () { return this; } }; }
      };
    }
  };
})();
