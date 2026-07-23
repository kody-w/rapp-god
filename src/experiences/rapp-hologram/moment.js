/* (c) 2026 Kody Wildfeuer - PolyForm Noncommercial 1.0.0, see /LICENSE - noncommercial use only - "Holographic Moments" is a trademark. */
/* Holographic Moments — one engine, three modes (feed / create / play). Legacy Moments still decode,
   but all playback now runs through the shared universal Lantern cartridge player with no CDN assets. */
(function () {
  "use strict";
  var W = window, D = document;
  var Bridge = W.HologramBridge;
  var playerFrame = D.getElementById("player");
  var playerPort = null, playerReady = null;

  var BIOMES = {
    savanna: { sky: "#9fc6e8", floor: "#35562a" },
    canyon: { sky: "#e6c089", floor: "#6b4a26" },
    forest: { sky: "#123244", floor: "#142436" },
    volcanic: { sky: "#3a1414", floor: "#2a1414" },
    void: { sky: "#05060a", floor: "#0a0a12" }
  };
  function setBiome(b) {
    var P = BIOMES[b] || BIOMES.savanna;
    D.body.style.background = "linear-gradient(180deg," + P.sky + " 0%," + P.floor + " 100%)";
  }

  function ensurePlayer() {
    if (!playerFrame) return Promise.reject(new Error("player iframe missing"));
    if (playerPort) return Promise.resolve(playerPort);
    if (playerReady) return playerReady;
    playerReady = new Promise(function (resolve, reject) {
      var ch = new MessageChannel();
      var done = false;
      ch.port1.onmessage = function (ev) {
        if (!ev.data || !ev.data.type) return;
        if (ev.data.type === "ready" && !done) { done = true; playerPort = ch.port1; resolve(playerPort); }
      };
      var start = function () {
        try { playerFrame.contentWindow.postMessage({ type: "hologram-init" }, "*", [ch.port2]); }
        catch (e) { reject(e); }
      };
      if (playerFrame.contentDocument && playerFrame.contentDocument.readyState === "complete") start();
      else playerFrame.addEventListener("load", function onload() { playerFrame.dataset.ready = "1"; playerFrame.removeEventListener("load", onload); start(); }, { once: true });
      setTimeout(function () { if (!done) reject(new Error("player init timeout")); }, 4000);
    });
    return playerReady;
  }
  async function loadPlayerCart(m) {
    var cart = await Bridge.normalizePlayable(m);
    var port = await ensurePlayer();
    port.postMessage({ type: "load-cartridge", cart: cart });
    return cart;
  }

  // ---- Moment format ----
  function clampF(f) { return { at: f.at | 0, s: +f.s, l: +f.l, p: +f.p, g: +f.g, h: +f.h, x: +f.x, z: +f.z }; }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function lerpF(a, b, t) { return { s: lerp(a.s, b.s, t), l: lerp(a.l, b.l, t), p: lerp(a.p, b.p, t), g: lerp(a.g, b.g, t), h: lerp(a.h, b.h, t), x: lerp(a.x, b.x, t), z: lerp(a.z, b.z, t) }; }
  function expand(moment) {
    var k = (moment.k || []).map(clampF).sort(function (a, b) { return a.at - b.at; });
    if (!k.length) k = [{ at: 0, s: .35, l: .4, p: 0, g: .45, h: 140, x: 0, z: 0 }];
    if (k.length === 1) k = [Object.assign({}, k[0], { at: 0 }), Object.assign({}, k[0], { at: 99 })];
    var out = [];
    for (var i = 0; i < 100; i++) {
      var lo = k[0], hi = k[k.length - 1];
      for (var j = 0; j < k.length; j++) { if (k[j].at <= i) lo = k[j]; if (k[j].at >= i) { hi = k[j]; break; } }
      var t = hi.at === lo.at ? 0 : (i - lo.at) / (hi.at - lo.at);
      out.push(lerpF(lo, hi, t));
    }
    return out;
  }
  function encode(m) { return btoa(unescape(encodeURIComponent(JSON.stringify(m)))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, ""); }
  function decode(s) { try { s = s.replace(/-/g, "+").replace(/_/g, "/"); return JSON.parse(decodeURIComponent(escape(atob(s)))); } catch (e) { return null; } }
  function isLegacy(m) { return Bridge && Bridge.isLegacyMoment(m); }
  function isCart(m) { return Bridge && Bridge.isCartridge(m); }
  function titleOf(m) { return m ? (m.title || m.t || "untitled") : "untitled"; }
  function authorOf(m) { return m ? (m.author || m.a || "@anon") : "@anon"; }
  function biomeOf(m) {
    if (!m) return "savanna";
    if (m.b && BIOMES[m.b]) return m.b;
    if (m.born && m.born.from && BIOMES[m.born.from]) return m.born.from;
    return "savanna";
  }

  // BROWSER SIGNING — a per-browser ECDSA P-256 key (persisted in localStorage) signs each Moment on
  // Share, so authorship is cryptographically PROVABLE on a public repo and the market's distinct-signer
  // counts can't be gamed (a copy can't forge your key). Sign/verify use the canonical body (all fields
  // except sig/pub, top-level keys sorted) — exactly what market.html verifies.
  var KEY = null;
  function _body(m) { var b = {}; Object.keys(m).sort().forEach(function (k) { if (k !== "sig" && k !== "pub") b[k] = m[k]; }); return new TextEncoder().encode(JSON.stringify(b)); }
  async function getKey() {
    if (KEY) return KEY;
    try {
      var stored = localStorage.getItem("holo:key");
      if (stored) { var j = JSON.parse(stored); KEY = { priv: await crypto.subtle.importKey("jwk", j.priv, { name: "ECDSA", namedCurve: "P-256" }, true, ["sign"]), pub: j.pub }; }
      else {
        var kp = await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]);
        var priv = await crypto.subtle.exportKey("jwk", kp.privateKey), pub = await crypto.subtle.exportKey("jwk", kp.publicKey);
        localStorage.setItem("holo:key", JSON.stringify({ priv: priv, pub: pub })); KEY = { priv: kp.privateKey, pub: pub };
      }
    } catch (e) { KEY = null; }
    return KEY;
  }
  async function signMoment(m) {
    var k = await getKey(); if (!k) return m;
    if (W.Rappid && !m.sig_suite) m.sig_suite = W.Rappid.SIG_SUITE;   // crypto-agility (covered by the signature)
    var sig = await crypto.subtle.sign({ name: "ECDSA", hash: "SHA-256" }, k.priv, _body(m));
    m.sig = Array.from(new Uint8Array(sig)).map(function (b) { return b.toString(16).padStart(2, "0"); }).join("");
    m.pub = k.pub; return m;
  }

  // OWNERSHIP TRANSFER — a Moment's rappid is a deed. The current owner signs over the rights to a recipient
  // key (a human or an agent). Resolution walks the signed, hash-linked transfer chain from the ledger.
  var _hx = function (buf) { return Array.from(new Uint8Array(buf)).map(function (b) { return b.toString(16).padStart(2, "0"); }).join(""); };
  async function signTransfer(m, toPubX, prevHash) {
    var k = await getKey(); if (!k || !W.Ownership || !W.Rappid) return null;
    var t = W.Ownership.newTransfer(W.Rappid.ofMoment(m.pk), k.pub.x, toPubX, prevHash, Date.now());
    var sig = await crypto.subtle.sign({ name: "ECDSA", hash: "SHA-256" }, k.priv, new TextEncoder().encode(W.Ownership.transferBody(t)));
    t.sig = _hx(sig); t.pub = k.pub; t.sig_suite = W.Rappid.SIG_SUITE; return t;
  }
  async function verifyTransfer(t) {
    if (!t || !t.sig || !t.pub || t.pub.x !== t.from || W.Ownership.transferHash(t) !== t.hash) return false;
    try {
      var key = await crypto.subtle.importKey("jwk", t.pub, { name: "ECDSA", namedCurve: "P-256" }, false, ["verify"]);
      var sb = new Uint8Array(t.sig.match(/.{2}/g).map(function (h) { return parseInt(h, 16); }));
      return await crypto.subtle.verify({ name: "ECDSA", hash: "SHA-256" }, key, sb, new TextEncoder().encode(W.Ownership.transferBody(t)));
    } catch (e) { return false; }
  }
  async function resolveOwner(m) {
    if (!W.Rappid || !W.Ownership) return { owner: null };
    var rid = W.Rappid.ofMoment(m.pk), mint = (m.pub && m.pub.x) || m.signer || null;
    if (!mint) return { owner: null, ownerRappid: null, transfers: 0, tip: rid };
    var all = [];
    try { var txt = await (await fetch("lineage/transfers.jsonl?_=" + Math.floor(perf() * 1000))).text();
      all = txt.trim().split("\n").filter(Boolean).map(JSON.parse).filter(function (t) { return t.rappid === rid; }); } catch (e) {}
    var ok = []; for (var i = 0; i < all.length; i++) if (await verifyTransfer(all[i])) ok.push(all[i]);
    return W.Ownership.deedChain(rid, mint, ok);
  }
  async function transferMoment() {
    var m = S.moment; if (!m || !m.pk) { toast("only a spacetime Moment can be deeded"); return; }
    var k = await getKey(), d = await resolveOwner(m);
    if (!k || !d.owner) { toast("this Moment isn't owned yet — plant/sign it first"); return; }
    if (d.owner !== k.pub.x) { toast("you are not the current owner of this Moment"); return; }
    var to = prompt("🤝 Transfer this Moment\n\nPaste the recipient's zookeeper key (their pub.x). A human or an agent — any key is an identity."); if (!to) return;
    var t = await signTransfer(m, to.trim(), d.tip); if (!t) { toast("couldn't sign the transfer"); return; }
    var blob = new Blob([JSON.stringify(t)], { type: "application/json" }), a = D.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = m.pk.replace(/[^\w·.-]/g, "_") + ".deed.json"; a.click();
    toast("deed signed → " + to.slice(0, 10) + "… · publish it to the commons to record the transfer");
  }
  W.signTransfer = signTransfer; W.verifyTransfer = verifyTransfer; W.resolveOwner = resolveOwner; W.transferMoment = transferMoment;
  async function openDeed() {
    var m = S.moment; if (!m || !m.pk) { toast("not a deedable Moment"); return; }
    $("bio").className = ""; $("biohdr").innerHTML = "Deed"; $("biosub").innerHTML = "resolving ownership…"; $("biobody").innerHTML = "";
    var rid = W.Rappid.ofMoment(m.pk), d = await resolveOwner(m), k = await getKey(), mine = (k && d.owner === k.pub.x);
    $("biohdr").innerHTML = "Deed · <b style='color:var(--pb)'>" + esc(rid.slice(0, 30)) + "…</b>";
    $("biosub").innerHTML = d.owner ? ("owned by <b>" + esc((d.ownerRappid || "").replace("rappid:keeper:", "").slice(0, 18)) + "…</b>" + (mine ? ' <span style="color:var(--pa)">(you)</span>' : "") + " · " + d.transfers + " transfer" + (d.transfers === 1 ? "" : "s")) : "unowned — plant & sign it to claim it";
    var rows = (d.history || []).map(function (h) {
      return '<div class="bch"><span class="bi">' + (h.event === "mint" ? "✦" : "🤝") + '</span><div><div class="bk">' + (h.event === "mint" ? "minted / claimed by " + esc((h.owner || "").slice(0, 12)) + "…" : "transferred → " + esc((h.to || "").slice(0, 12)) + "…") + '</div><div class="bd">' + (h.ts ? new Date(h.ts).toISOString().slice(0, 19) + "Z" : "genesis") + (h.hash ? " · " + h.hash : "") + '</div></div></div>';
    }).join("");
    if (mine) rows += '<div style="padding:14px 0"><button onclick="transferMoment()" style="width:100%;background:linear-gradient(90deg,var(--pa),var(--pb));color:#05121a;border:0;border-radius:10px;padding:11px;font-weight:800;cursor:pointer">🤝 Transfer ownership</button></div>';
    $("biobody").innerHTML = rows || '<div class="bm">no deed history</div>';
  }
  W.openDeed = openDeed;
  async function verifyMoment(m) {
    if (!m.sig || !m.pub) return false;
    try {
      var key = await crypto.subtle.importKey("jwk", m.pub, { name: "ECDSA", namedCurve: "P-256" }, false, ["verify"]);
      var sig = Uint8Array.from(m.sig.match(/.{1,2}/g).map(function (h) { return parseInt(h, 16); }));
      return await crypto.subtle.verify({ name: "ECDSA", hash: "SHA-256" }, key, sig, _body(m));
    } catch (e) { return false; }
  }
  W.signMoment = signMoment; W.verifyMoment = verifyMoment;

  // .egg — export a Moment as a portable, re-uploadable file. Lossless: keyframes + title + biome +
  // signature are all preserved, so a re-imported .egg displays exactly as it was, still provably owned.
  function exportEgg(m) {
    m = m || S.moment; if (!m) return;
    var egg = { format: "holographic-moment-egg/1.0", moment: m, exported: new Date().toISOString() };
    var blob = new Blob([JSON.stringify(egg, null, 2)], { type: "application/json" });
    var url = URL.createObjectURL(blob), a = D.createElement("a");
    a.href = url; a.download = (m.t || "moment").replace(/[^a-z0-9]+/gi, "_").replace(/^_+|_+$/g, "").toLowerCase() + ".egg";
    D.body.appendChild(a); a.click(); a.remove(); setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    toast("exported " + a.download);
  }
  function importEgg(file) {
    if (!file) return;
    var r = new FileReader();
    r.onload = function () {
      try {
        var j = JSON.parse(r.result), m = (j && j.moment) ? j.moment : j;
        if (m && Array.isArray(m.k)) {
          reconcileIntoZoo(m).then(function (res) {
            openPlay(res.organism || m);
            if (res.kind === "planted") { toast("planted “" + (m.t || "moment") + "” in your zoo"); return; }
            var t = res.tally, bits = [];
            if (t.refined) bits.push(t.refined + " new frame" + (t.refined > 1 ? "s" : ""));
            if (t.redundant) bits.push(t.redundant + " unchanged");
            if (t.resisted) bits.push("resisted " + t.resisted);
            toast((res.alive ? "✦ " : "⚠ ") + (m.t || "companion") + " absorbed your seed — " + (bits.join(", ") || "nothing changed") + " · gen " + res.gen);
          });
        }
        else toast("not a valid .egg");
      } catch (e) { toast("couldn't read that .egg"); }
    };
    r.readAsText(file);
  }
  W.exportEgg = function () { exportEgg(S.moment); };
  (function () { var el = D.getElementById("eggfile"); if (el) el.addEventListener("change", function (e) { importEgg(e.target.files[0]); e.target.value = ""; }); })();

  // MY ZOO — your menagerie. Every companion you plant or replant joins your local collection,
  // keyed by your signing key (your key IS your identity as a zookeeper).
  function loadZoo() { try { return JSON.parse(localStorage.getItem("holo:zoo") || "[]"); } catch (e) { return []; } }
  function saveZoo(z) { try { localStorage.setItem("holo:zoo", JSON.stringify(z.slice(-300))); } catch (e) {} }
  function zooKey(m) { return (m.t || "") + "|" + (m.sig || "").slice(0, 16); }
  function lineageId() { return "org-" + Math.random().toString(36).slice(2, 10) + Date.now().toString(36); }
  function hState(m) { return W.Homeostasis.homeostasis({ k: m.k, gen: m._gen, stress: m._stress }); }
  function addToZoo(m) {
    if (!m) return; var z = loadZoo(); var copy = JSON.parse(JSON.stringify(m));
    if (!copy._id) copy._id = lineageId();                 // lineage id ties an organism's generations together (not signed: _ prefix)
    if (copy._gen == null) copy._gen = (copy.k || []).length;
    if (copy._stress == null) copy._stress = 0;
    z = z.filter(function (x) { return x._id === copy._id ? false : zooKey(x) !== zooKey(copy); });
    z.push(copy); saveZoo(z); return copy;
  }
  // RECONCILE an incoming organism (a seed) into your zoo via homeostasis — it lives on, grows, or resists.
  async function reconcileIntoZoo(m) {
    var H = W.Homeostasis, z = loadZoo();
    var host = z.find(function (x) { return (m._id && x._id === m._id) || (x.t === m.t && (x.a || "") === (m.a || "")); });
    if (!host) { var added = addToZoo(m); return { kind: "planted", organism: added }; }
    var work = { k: host.k.slice(), gen: host._gen != null ? host._gen : host.k.length, stress: host._stress || 0 };
    var tally = { refined: 0, redundant: 0, resisted: 0 };
    (m.k || []).forEach(function (f) { var r = H.reconcile(work, f); tally[r.kind]++; work = r.organism; });
    host.k = work.k; host._gen = work.gen; host._stress = work.stress;
    await signMoment(host);                                 // re-sign the surviving generation — still provably yours
    saveZoo(z);
    var st = H.homeostasis(work);
    return { kind: "reconciled", tally: tally, alive: st.alive, gen: st.generation, vitality: st.vitality, organism: host };
  }
  async function renderZoo() {
    var k = await getKey(); var fp = (k && k.pub && k.pub.x) ? k.pub.x.slice(0, 16) : "—";
    var z = loadZoo();
    $("zookeeper").innerHTML = "zookeeper <b style='color:var(--ink)'>" + esc(fp) + "…</b> &nbsp;·&nbsp; " + z.length + " companion" + (z.length === 1 ? "" : "s") + " in your care &nbsp;·&nbsp; <a onclick=\"openKeeper()\" style='color:var(--pb);cursor:pointer'>visit your public zoo →</a>";
    var g = $("zoogrid");
    if (!z.length) { g.innerHTML = '<div class="empty">Your menagerie is empty. <a onclick="go(\'create\')">🌱 Plant your first companion →</a></div>'; return; }
    g.innerHTML = z.slice().reverse().map(function (m) {
      var h = hState(m), pct = Math.round(h.vitality * 100);
      var badge = h.alive ? "✦ homeostasis · gen " + h.generation : "⚠ homeostasis failing";
      var bar = '<div class="vit"><i style="width:' + pct + '%;background:' + (h.alive ? "var(--pa)" : "var(--pc)") + '"></i></div>';
      return '<div class="card" data-m="' + encode(m) + '"><div class="thumb" style="' + thumbStyle(m) + '"><span class="tag">' + (m.sig ? "✓ yours" : "unsigned") + '</span><span class="play beat">♥</span></div>' +
        '<div class="meta"><div class="ti">' + esc(m.t) + '</div><div class="au">' + esc(m.a || "@you") + " · " + (m.b || "savanna") + '</div>' + bar +
        '<div class="hs" style="color:' + (h.alive ? "var(--mut)" : "var(--pc)") + '">' + badge + '</div></div></div>';
    }).join("");
    document.querySelectorAll("#zoogrid .card").forEach(function (c) { c.onclick = function () { openPlay(decode(c.dataset.m)); }; });
  }
  W.addToZoo = addToZoo; W.reconcileIntoZoo = reconcileIntoZoo;

  // KINDRED — "organisms more similar to mine than others." Loads the static warehouse and ranks it
  // entirely in the browser by fingerprint distance (Simon Willison free-data-warehouse pattern).
  async function openKindred(m) {
    m = m || S.moment; if (!m) return;
    go("kindred");
    $("kinof").textContent = m.t || "your companion";
    $("kinsub").textContent = "scoring the warehouse…";
    var wh; try { wh = await (await fetch("warehouse.json?_=" + Math.floor(perf() * 1000))).json(); }
    catch (e) { $("kinsub").textContent = "warehouse unavailable — build it with build_warehouse.js"; return; }
    var pool = (wh.organisms || []).filter(function (o) { return !(o.t === m.t && (o.a || "") === (m.a || "")); });
    var ranked = W.Fingerprint.rank(m, pool).slice(0, 24);
    $("kinsub").innerHTML = "scored " + (wh.organisms || []).length + " organisms · most similar first · " + (wh.dims || 0) + "-D fingerprint, ranked in your browser";
    $("zoogrid2").innerHTML = ranked.map(function (o) {
      var pct = Math.round(o.score * 100), mm = decode(o.token);
      return '<a class="card" href="./?m=' + o.token + '"><div class="thumb" style="' + thumbStyle(mm) + '"><span class="tag">' + pct + '% alike</span><span class="play beat">♥</span></div>' +
        '<div class="meta"><div class="ti">' + esc(o.t) + '</div><div class="au">' + esc(o.a) + ' · ' + (o.b || "savanna") + (o.drop ? ' · drop' : '') + '</div><div class="vit"><i style="width:' + pct + '%;background:var(--pb)"></i></div></div></a>';
    }).join("") || '<div style="grid-column:1/-1;color:var(--mut);padding:30px;text-align:center">No other organisms in the warehouse yet.</div>';
  }
  W.openKindred = openKindred;

  // WILD — catch the one organism that your exact place + moment mints (Pokémon-GO style). The spacetime
  // coordinate is its primary key; sign it and you OWN that moment as a living holographic companion.
  function mintWild() {
    if (!W.Organism) return;
    function mint(loc) {
      var org = W.Organism.organismFromStamp(Date.now(), loc);
      signMoment(org).then(function () { addToZoo(org); openPlay(org);
        toast((loc ? "🌍 caught a wild organism — here & now" : "◷ minted this exact moment") + " · " + org.pk); });
    }
    if (navigator.geolocation) {
      toast("scanning your spacetime…");
      navigator.geolocation.getCurrentPosition(
        function (p) { mint({ lat: p.coords.latitude, lng: p.coords.longitude }); },
        function () { mint(null); }, { timeout: 8000, maximumAge: 60000 });
    } else mint(null);
  }
  W.mintWild = mintWild;

  // DIAL — summon an organism anywhere by its address (pk). The coordinate regenerates the hologram; no fetch.
  function dial(addr) {
    if (!W.Organism) return;
    addr = (addr == null) ? prompt("📡 Dial an organism by its address:\n\n  sky·<utc-ms>\n  <geohash>·<utc-ms>") : addr;
    if (!addr) return;
    var org = W.Organism.fromPk(addr);
    if (!org) { toast("couldn't dial “" + addr + "”"); return; }
    history.replaceState(0, 0, location.pathname + "?dial=" + encodeURIComponent(org.pk));
    openPlay(org, false); toast("📡 summoned " + org.pk);
  }
  W.dial = dial;

  // BIOGRAPHY — git-as-harness in the browser: fetch the static .bio.json the brainstem CLI deposited and
  // render the organism's life-story (born, frames grown over UTC time, re-signings, birth-proof status).
  async function openBio(pk) {
    pk = pk || (S.moment && S.moment.pk); if (!pk) { toast("this organism has no spacetime address"); return; }
    $("bio").className = ""; $("biobody").innerHTML = '<div class="bm">reading the git ledger…</div>';
    var safe = pk.replace(/[^\w·.-]/g, "_"), bio;
    try { bio = await (await fetch("lineage/" + encodeURIComponent(safe) + ".bio.json?_=" + Math.floor(perf() * 1000))).json(); }
    catch (e) { $("biohdr").innerHTML = "Biography"; $("biosub").innerHTML = ""; $("biobody").innerHTML = '<div class="bm">No biography committed yet — the brainstem writes it on the next tick.<br><span style="opacity:.6">node hologram/zoo_bio.js ' + esc(pk) + '</span></div>'; return; }
    var icon = { birth: "◷", grow: "✦", "genesis-add": "⚠", resign: "✎", injury: "⚠", stress: "✖" };
    $("biohdr").innerHTML = "Biography · <b>" + esc(bio.pk) + "</b>";
    $("biosub").innerHTML = (bio.grownFrames || 0) + " frames grown over " + bio.revisions + " revisions · " +
      (bio.breakAt ? '<span style="color:var(--pc)">⚠ birth-proof broke @' + bio.breakAt + '</span>' : '<span style="color:var(--pa)">birth-proof ✓ everywhere</span>') +
      (bio.ownedBy ? " · owned by " + esc(bio.ownedBy) + "…" : "");
    $("biobody").innerHTML = bio.chapters.map(function (c) {
      var d = new Date(c.ct * 1000).toISOString().replace("T", " ").slice(0, 19);
      var label = c.kind === "birth" ? "born into the repo (" + c.frames + " frames)" :
        c.kind === "grow" ? "grew a frame at " + (typeof c.at === "number" ? c.at.toFixed(1) : c.at) + (c.u ? " · UTC " + new Date(c.u).toISOString().slice(11, 23) : "") :
        c.kind === "resign" ? "ownership re-signed (" + esc(c.signer || "") + "…)" :
        c.kind === "stress" ? "homeostasis stress → " + c.stress :
        c.kind === "injury" ? "injury: " + c.field + " @" + c.at : c.kind;
      return '<div class="bch' + (c.anomaly ? ' anom' : '') + '"><span class="bi">' + (icon[c.kind] || "•") + '</span><div><div class="bk">' + label + '</div><div class="bd">' + d + ' UTC · ' + c.sha + '</div></div></div>';
    }).join("") || '<div class="bm">no chapters yet</div>';
  }
  W.openBio = openBio;
  W.closeBio = function () { $("bio").className = "hide"; };

  // GROWTH DIFF — git-as-harness capability 2: what this creature became, physics-classified.
  async function openGrew(pk) {
    pk = pk || (S.moment && S.moment.pk); if (!pk) return;
    $("bio").className = ""; $("biohdr").innerHTML = "Recent growth"; $("biosub").innerHTML = ""; $("biobody").innerHTML = '<div class="bm">reading the diff…</div>';
    var safe = pk.replace(/[^\w·.-]/g, "_"), g;
    try { g = await (await fetch("lineage/" + encodeURIComponent(safe) + ".grew.json?_=" + Math.floor(perf() * 1000))).json(); }
    catch (e) { $("biobody").innerHTML = '<div class="bm">No growth diff committed yet.</div>'; return; }
    $("biohdr").innerHTML = "How <b>" + esc(pk) + "</b> grew";
    $("biosub").innerHTML = "+" + g.framesAdded + " frames · coarsest gap " + g.coarsestBefore + "→" + g.coarsestAfter + " · " +
      (g.lossless ? '<span style="color:var(--pa)">lossless ✓</span>' : '<span style="color:var(--pc)">lossy ✕</span>') +
      (g.corruptFrames ? ' · <span style="color:var(--pc)">' + g.corruptFrames + ' web-tears</span>' : '') +
      " · genesis " + (g.genesisMutated ? '<span style="color:var(--pc)">mutated</span>' : 'intact ✓');
    $("biobody").innerHTML = (g.frames || []).map(function (f) {
      return '<div class="bch"><span class="bi">✦</span><div><div class="bk">deepened at ' + (typeof f.at === "number" ? f.at.toFixed(1) : f.at) + '</div><div class="bd">UTC ' + (f.u ? new Date(f.u).toISOString().slice(11, 23) : "") + '</div></div></div>';
    }).join("") || '<div class="bm">no new frames in this window</div>';
  }
  W.openGrew = openGrew;

  // TIME-TRAVEL — git-as-harness capability 3 (read side): reconstruct an organism AS OF a past instant
  // from the static .vitals.json (genesis from its pk + grown frames whose recordedCt <= that tick).
  async function dialAt(pk, atMs) {
    if (!W.Organism) return; pk = pk || (S.moment && S.moment.pk); if (!pk) return;
    var safe = pk.replace(/[^\w·.-]/g, "_"), v;
    try { v = await (await fetch("lineage/" + encodeURIComponent(safe) + ".vitals.json?_=" + Math.floor(perf() * 1000))).json(); }
    catch (e) { toast("no time-travel record yet for this organism"); return; }
    var tick = v.ticks.filter(function (t) { return t.ct * 1000 <= atMs; }).pop() || v.ticks[0];
    var base = W.Organism.fromPk(pk); if (!base) return;
    var grown = v.frames.filter(function (f) { return f.u != null && f.recordedCt <= tick.ct; });
    base.k = base.k.concat(grown).sort(function (a, b) { return a.at - b.at; });
    openPlay(base, false);
    toast("⏳ as of " + new Date(tick.ct * 1000).toISOString().slice(0, 19) + "Z · gen " + tick.gen + " · " + (tick.alive ? "alive" : "⚠ dead"));
  }
  W.dialAt = dialAt;

  // LINEAGE — git-as-harness capability 4 (read side): the family tree (forks = species, merges = hybrids).
  async function openLineage(pk) {
    pk = pk || (S.moment && S.moment.pk); if (!pk) return;
    $("bio").className = ""; $("biohdr").innerHTML = "Lineage · <b>" + esc(pk) + "</b>"; $("biosub").innerHTML = ""; $("biobody").innerHTML = '<div class="bm">reading the family tree…</div>';
    var safe = pk.replace(/[^\w·.-]/g, "_"), ln;
    try { ln = await (await fetch("lineage/" + encodeURIComponent(safe) + ".lineage.json?_=" + Math.floor(perf() * 1000))).json(); }
    catch (e) { $("biobody").innerHTML = '<div class="bm">A single unbranched lineage — this organism has not speciated. Its only ancestor is its birth coordinate <b style="color:var(--pb)">' + esc(pk) + '</b>.</div>'; return; }
    $("biosub").innerHTML = ((ln.branches || []).length) + " branch(es) · " + ((ln.merges || []).length) + " hybridization(s) · ancestor " + (ln.ancestor || "—");
    var rows = (ln.branches || []).map(function (b) { return '<div class="bch"><span class="bi">🜃</span><div><div class="bk">' + esc(b.name) + '</div><div class="bd">tip ' + (b.tip || "") + '</div></div></div>'; }).join("");
    rows += (ln.merges || []).map(function (mg) { return '<div class="bch' + (mg.survived ? '' : ' anom') + '"><span class="bi">' + (mg.survived ? "⚭" : "✖") + '</span><div><div class="bk">' + (mg.survived ? "hybridized " : "sterile cross ") + esc(mg.with || "") + '</div><div class="bd">+' + (mg.inherited || 0) + ' / -' + (mg.rejected || 0) + '</div></div></div>'; }).join("");
    $("biobody").innerHTML = rows || '<div class="bm">single lineage</div>';
  }
  W.openLineage = openLineage;

  // SOCIAL LAYER — visit a zookeeper's menagerie by their key. A keeper's identity is their signing-key
  // fingerprint; their public companions are the warehouse organisms they signed. Serverless, no accounts.
  async function openKeeper(fp) {
    var mine = false;
    if (!fp) { var k = await getKey(); fp = (k && k.pub && k.pub.x) ? k.pub.x.slice(0, 16) : null; mine = true; }
    if (!fp) { toast("no zookeeper key"); return; }
    go("keeper"); history.replaceState(0, 0, location.pathname + "?keeper=" + encodeURIComponent(fp));
    $("keephdr").innerHTML = (mine ? "Your public zoo" : "Zookeeper") + " · <b style='color:var(--pb)'>" + esc(fp) + "…</b>";
    $("keepsub").textContent = "reading the public warehouse…";
    var wh; try { wh = await (await fetch("warehouse.json?_=" + Math.floor(perf() * 1000))).json(); }
    catch (e) { $("keepsub").textContent = "the public warehouse is unavailable"; return; }
    var theirs = (wh.organisms || []).filter(function (o) { return o.signer === fp; });
    var biomes = {}; theirs.forEach(function (o) { biomes[o.b] = (biomes[o.b] || 0) + 1; });
    var top = Object.keys(biomes).sort(function (a, b) { return biomes[b] - biomes[a]; })[0];
    $("keepsub").innerHTML = theirs.length + " companion" + (theirs.length === 1 ? "" : "s") + " in the public zoo" + (top ? " · mostly " + top : "") +
      (mine ? ' · <span style="color:var(--pa)">this is you — share this link</span>' : '');
    $("keepgrid").innerHTML = theirs.map(function (o) { var mm = decode(o.token);
      return '<a class="card" href="./?m=' + o.token + '"><div class="thumb" style="' + thumbStyle(mm) + '"><span class="tag">✓ ' + esc(o.b) + '</span><span class="play beat">♥</span></div><div class="meta"><div class="ti">' + esc(o.t) + '</div><div class="au">' + esc(o.a) + '</div></div></a>';
    }).join("") || '<div class="kmt">No public companions yet' + (mine ? ' — once one of yours reaches the commons it appears here for visitors.' : '.') + '</div>';
  }
  W.openKeeper = openKeeper;

  // ---- playback state ----
  var S = { mode: "feed", moment: null, cart: null, frames: null, pf: 0, playing: true, dur: 14, t0: perf() };
  function perf() { return W.performance.now() / 1000; }
  function applyFrame() {
    if (S.mode === "create" && draft) previewDraft();
  }
  async function loadMoment(m) {
    S.moment = m;
    S.frames = isLegacy(m) ? expand(m) : null;
    S.pf = 0;
    setBiome(biomeOf(m));
    try { S.cart = await loadPlayerCart(m); }
    catch (e) { toast("couldn't load hologram"); }
    return S.cart;
  }

  function setScanHint(on) { var h = D.getElementById("scanhint"); if (h) h.className = on ? "" : "hide"; }
  W.setScanHint = setScanHint;
  W.camState = function () { return { player: "lantern", ready: !!playerPort, pf: Math.round(S.pf), playing: true }; };
  W.scanState = W.camState;   // back-compat alias
  W.resetCam = function () {};

  // ---- UI helpers ----
  function $(id) { return D.getElementById(id); }
  function show(id) { $(id).classList.remove("hide"); } function hide(id) { $(id).classList.add("hide"); }
  W.hide = hide;
  function toast(msg) { var t = D.createElement("div"); t.className = "toast"; t.textContent = msg; D.body.appendChild(t); setTimeout(function () { t.remove(); }, 1800); }

  function go(mode) {
    S.mode = mode;
    ["feed", "create", "pc", "ptitle", "share", "mint", "zoo", "scanhint", "kindred", "keeper"].forEach(hide);
    $("navRemix").style.display = "none"; $("navShare").style.display = "none"; $("navMint").style.display = "none"; $("navEgg").style.display = "none"; $("navPip").style.display = "none"; $("navKindred").style.display = "none"; $("navBio").style.display = "none"; $("navDeed").style.display = "none"; if ($("bio")) $("bio").className = "hide";
    if (mode === "feed") { history.replaceState(0, 0, location.pathname); show("feed"); renderFeed(); }
    if (mode === "zoo") { history.replaceState(0, 0, location.pathname + "?zoo"); show("zoo"); renderZoo(); }
    if (mode === "kindred") { show("kindred"); }
    if (mode === "keeper") { show("keeper"); }
    if (mode === "create") { show("create"); initCreate(); }
    if (mode === "play") { show("ptitle"); }
  }
  W.go = go;

  // ---- FEED ----
  var SEED = [
    { v: 1, t: "Birth of a Star", a: "@nova", b: "void", k: [{ at: 0, s: .1, l: 0, p: 0, g: 0, h: 50, x: 0, z: 0 }, { at: 60, s: .5, l: 0, p: 0, g: 1, h: 45, x: 0, z: 0 }, { at: 99, s: .9, l: 0, p: .3, g: 1, h: 30, x: 0, z: 0 }] },
    { v: 1, t: "The Bloom", a: "@flora", b: "forest", k: [{ at: 0, s: .2, l: .1, p: 0, g: .3, h: 300, x: 0, z: 0 }, { at: 50, s: .6, l: .2, p: .9, g: .7, h: 320, x: 0, z: 0 }, { at: 99, s: .5, l: .2, p: .5, g: .9, h: 180, x: 0, z: 0 }] },
    { v: 1, t: "Wanderer", a: "@roam", b: "savanna", k: [{ at: 0, s: .4, l: .9, p: .1, g: .4, h: 130, x: -.8, z: -.6 }, { at: 50, s: .45, l: 1, p: .1, g: .5, h: 140, x: .7, z: .3 }, { at: 99, s: .4, l: .9, p: .1, g: .4, h: 150, x: -.5, z: .8 }] },
    { v: 1, t: "Rage", a: "@ferox", b: "volcanic", k: [{ at: 0, s: .5, l: .4, p: 0, g: .3, h: 0, x: 0, z: 0 }, { at: 99, s: .8, l: .5, p: 1, g: 1, h: 10, x: 0, z: 0 }] },
    { v: 1, t: "Tides", a: "@blue", b: "forest", k: [{ at: 0, s: .6, l: .3, p: .2, g: .5, h: 200, x: 0, z: -.5 }, { at: 33, s: .4, l: .3, p: .2, g: .8, h: 190, x: 0, z: .5 }, { at: 66, s: .6, l: .3, p: .2, g: .5, h: 210, x: 0, z: -.5 }, { at: 99, s: .4, l: .3, p: .2, g: .8, h: 190, x: 0, z: .5 }] }
  ];
  function thumbStyle(m) {
    var colors;
    if (isCart(m)) {
      var pal = (((m || {}).genome || {}).layers || []).filter(function (l) { return l.role === "surface"; })[0];
      colors = (pal && pal.palette) || ["#4488ff", "#2255cc"];
    } else {
      var h0 = m.k[0].h, h1 = m.k[m.k.length - 1].h;
      colors = ["hsl(" + h0 + ",65%,45%)", "hsl(" + h1 + ",70%,32%)"];
    }
    return "background:radial-gradient(circle at 50% 38%,rgba(255,255,255,.18),transparent 36%),linear-gradient(135deg," + colors[0] + "," + colors[Math.min(colors.length - 1, 3)] + ")";
  }
  function renderFeed() {
    var g = $("grid"); g.innerHTML = "";
    var all = SEED.concat(W.__EXTRA_MOMENTS__ || []);
    all.forEach(function (m) {
      var card = D.createElement("div"); card.className = "card";
      card.innerHTML = '<div class="thumb" style="' + thumbStyle(m) + '"><span class="tag">lantern</span><span class="play">▶</span></div>' +
        '<div class="meta"><div class="ti">' + esc(titleOf(m)) + '</div><div class="au">' + esc(authorOf(m)) + ' · ' + biomeOf(m) + '</div></div>';
      card.onclick = function () { openPlay(m); };
      g.appendChild(card);
    });
  }
  function esc(s) { return (s || "").replace(/[<>&"]/g, function (c) { return { "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;" }[c]; }); }

  // ---- PLAY ----
  async function openPlay(m, push) {
    go("play"); await loadMoment(m);
    $("ptitle").innerHTML = esc(titleOf(m)) + ' <span class="au">' + esc(authorOf(m)) + "</span>";
    if (push !== false) history.replaceState(0, 0, location.pathname + "?m=" + encode(m));
    if (isLegacy(m)) verifyMoment(m).then(function (ok) {   // show a provable-authorship badge when the signature verifies
      if (ok && m.pub) $("ptitle").innerHTML += ' <span class="au" style="color:var(--pa)">✓ signed ' + (m.pub.x || "").slice(0, 10) + '…</span>';
    });
    if (isLegacy(m)) {
      $("navShare").style.display = "";
      $("navRemix").style.display = "";
      $("navMint").style.display = "";
      $("navEgg").style.display = "";
      $("navKindred").style.display = "";
      $("navBio").style.display = "";
      $("navDeed").style.display = "";
    } else {
      $("navShare").style.display = "";
    }
    if (m.born != null && W.Organism && isLegacy(m)) {     // a spacetime-born organism: show its exact instant + verify the binding
      var bound = W.Organism.verifyCoordinate(m), when = new Date(m.born).toISOString().replace("T", " ").replace(".000Z", " UTC").replace("Z", " UTC");
      var where = (m.loc && m.loc.place) ? " · " + esc(m.loc.place) : (m.loc ? " · " + m.loc.lat + "," + m.loc.lng : "");
      var rid = W.Rappid ? W.Rappid.ofMoment(m.pk) : "";
      $("ptitle").innerHTML += '<br><span class="au" style="color:' + (bound ? "var(--pb)" : "var(--pc)") + '">' + (bound ? "◷ born " : "⚠ unverified ") + when + where + (rid ? " · ⧈ " + esc(rid.slice(0, 24)) + "…" : " · pk " + esc(m.pk || "")) + "</span>";
      if (W.Ownership) resolveOwner(m).then(function (d) { if (d && d.owner) $("ptitle").innerHTML += ' <span class="au" style="color:var(--pa)">· owned by ' + esc((d.ownerRappid || "").replace("rappid:keeper:", "").slice(0, 14)) + '…' + (d.transfers ? " (" + d.transfers + "↦)" : "") + '</span>'; });
    }
  }
  W.togglePlay = function () {};
  W.restart = function () {};
  W.scrubAt = function () {};
  function updatePC() {}
  W.remix = function () { if (S.moment) { go("create"); loadIntoCreate(S.moment); } };

  // PICTURE-IN-PICTURE — float the live hologram in an always-on-top OS window so it keeps playing
  // while you work in other apps. Captures the WebGL canvas to a stream and PiPs it (no fullscreen).
  async function pipHologram() {
    toast("picture-in-picture isn't available for the embedded Lantern player");
  }
  W.pipHologram = pipHologram;

  // ---- CREATE ----
  var draft = null, selKey = 0;
  var SL = ["S", "L", "P", "G", "H", "X", "Z"];
  function readSliders() {
    return { s: $("rS").value / 100, l: $("rL").value / 100, p: $("rP").value / 100, g: $("rG").value / 100, h: +$("rH").value, x: $("rX").value / 100, z: $("rZ").value / 100 };
  }
  function writeSliders(f) { $("rS").value = f.s * 100; $("rL").value = f.l * 100; $("rP").value = f.p * 100; $("rG").value = f.g * 100; $("rH").value = f.h; $("rX").value = f.x * 100; $("rZ").value = f.z * 100; updateSliderLabels(); }
  function updateSliderLabels() { $("vS").textContent = Math.round($("rS").value); $("vL").textContent = Math.round($("rL").value); $("vP").textContent = Math.round($("rP").value); $("vG").textContent = Math.round($("rG").value); $("vH").textContent = Math.round($("rH").value) + "°"; $("vX").textContent = Math.round($("rX").value); $("vZ").textContent = Math.round($("rZ").value); }
  function previewDraft() {
    draft.k.sort(function (a, b) { return a.at - b.at; });
    S.frames = expand(draft);
    setBiome($("cBiome").value);
    loadMoment(draft);
  }
  function curFrameFromSlider() {
    var f = readSliders(); f.at = draft.k[selKey].at; draft.k[selKey] = clampF(f); previewDraft();
    // live-apply at the selected keyframe's frame
    S.pf = f.at; applyFrame(f.at, true);
  }
  function renderKeys() {
    var el = $("keys"); el.innerHTML = "";
    draft.k.forEach(function (k, i) {
      var b = D.createElement("div"); b.className = "kf" + (i === selKey ? " on" : ""); b.textContent = "f" + k.at;
      b.onclick = function () { selKey = i; writeSliders(draft.k[i]); S.pf = draft.k[i].at; applyFrame(draft.k[i].at, true); renderKeys(); };
      el.appendChild(b);
    });
  }
  function initCreate() {
    if (!draft) draft = { v: 1, t: "untitled", a: "@anon", b: "savanna", k: [{ at: 0, s: .35, l: .4, p: 0, g: .45, h: 140, x: 0, z: 0 }, { at: 99, s: .7, l: .6, p: .4, g: .8, h: 40, x: 0, z: 0 }] };
    selKey = 0; S.mode = "create"; writeSliders(draft.k[0]); previewDraft(); renderKeys();
  }
  function loadIntoCreate(m) { draft = JSON.parse(JSON.stringify(m)); $("cTitle").value = m.t || "untitled"; $("cAuthor").value = m.a || "@anon"; $("cBiome").value = m.b || "savanna"; selKey = 0; writeSliders(draft.k[0]); previewDraft(); renderKeys(); }
  W.addKey = function () {
    var at = Math.round(S.pf); if (draft.k.some(function (k) { return k.at === at; })) at = Math.min(99, at + 5);
    var f = readSliders(); f.at = at; draft.k.push(clampF(f)); draft.k.sort(function (a, b) { return a.at - b.at; });
    selKey = draft.k.findIndex(function (k) { return k.at === at; }); previewDraft(); renderKeys(); toast("keyframe at f" + at);
  };
  W.finishMoment = function () {
    draft.t = $("cTitle").value || "untitled"; draft.a = $("cAuthor").value || "@anon"; draft.b = $("cBiome").value;
    openShare(draft);
  };
  ["rS", "rL", "rP", "rG", "rH", "rX", "rZ"].forEach(function (id) { D.addEventListener("input", function (e) { if (e.target.id === id && S.mode === "create") curFrameFromSlider(); }); });
  $("cBiome").addEventListener("change", function () { if (S.mode === "create") { draft.b = $("cBiome").value; setBiome(draft.b); } });

  // ---- SHARE ----
  var shareMoment = null;
  async function openShare(m) {
    shareMoment = m || S.moment; if (!shareMoment) return;
    if (isLegacy(shareMoment)) {
      await signMoment(shareMoment);                        // sign with the browser key — provable authorship
      addToZoo(shareMoment);                                // it joins your menagerie
    }
    var url = location.origin + location.pathname + "?m=" + encode(shareMoment);
    $("surl").value = url;
    var box = $("qrbox"); box.innerHTML = "";
    try { new QRCode(box, { text: url, width: 168, height: 168, correctLevel: QRCode.CorrectLevel.H }); }
    catch (e) { box.textContent = "(scan via the link below)"; }
    var fp = (shareMoment.pub && shareMoment.pub.x) ? shareMoment.pub.x.slice(0, 16) : "";
    var h = D.querySelector("#sheet h3"); if (h) h.innerHTML = isCart(shareMoment) ? "Your Lantern Cartridge" : ("Your Holographic Moment" + (fp ? "<span style='display:block;color:var(--pa);font-size:12px;font-weight:600;margin-top:5px'>✓ signed by your key · " + fp + "…</span>" : ""));
    show("share");
  }
  W.openShare = function () { openShare(S.moment); };

  // EDITIONS — mint a signed LIMITED RUN of a Moment. Each edition is a distinct signed token
  // (numbered n/N + a unique nonce) with its OWN URL + QR — provable scarcity out of infinite supply.
  function _nonce() { var a = new Uint8Array(8); crypto.getRandomValues(a); return Array.from(a).map(function (b) { return b.toString(16).padStart(2, "0"); }).join(""); }
  async function mintEditions(m, n) {
    var base = { v: m.v || 1, t: m.t, a: m.a, b: m.b, k: m.k }, out = [];
    for (var i = 1; i <= n; i++) {
      var ed = JSON.parse(JSON.stringify(base));
      ed.ed = { n: i, of: n, id: _nonce() }; ed.t = m.t + " · #" + i + "/" + n;
      await signMoment(ed); out.push(ed);
    }
    return out;
  }
  async function openMint(n) {
    if (!S.moment) return; n = n || 50;
    S.editionBase = S.moment;
    $("mintTitle").textContent = (S.moment.t || "Moment");
    $("mintSub").textContent = "running the press · " + n + " editions…";
    show("mint"); S.mode = "mint";
    var eds = await mintEditions(S.moment, n); S.editions = eds;
    $("mintSub").textContent = "press run of " + n + " · each a signed 1-of-1" + (eds[0] && eds[0].pub ? " · printed by key " + eds[0].pub.x.slice(0, 12) + "…" : "");
    var grid = $("mintgrid"); grid.innerHTML = "";
    eds.forEach(function (ed) {
      var url = location.origin + location.pathname + "?m=" + encode(ed);
      var card = D.createElement("div"); card.className = "edcard";
      var qz = D.createElement("div"); qz.className = "qz";
      try { new QRCode(qz, { text: url, width: 110, height: 110, correctLevel: QRCode.CorrectLevel.M }); } catch (e) { qz.textContent = "QR"; }
      card.appendChild(qz);
      var en = D.createElement("div"); en.className = "en"; en.textContent = "EDITION " + ed.ed.n + " / " + ed.ed.of;
      var ev = D.createElement("div"); ev.className = "ev"; ev.textContent = "✓ signed · " + ed.ed.id.slice(0, 8);
      card.appendChild(en); card.appendChild(ev);
      card.onclick = function () { location.href = url; };
      grid.appendChild(card);
    });
    history.replaceState(0, 0, location.pathname + "?mint=" + encode(S.editionBase) + "&n=" + n);
  }
  W.openMint = function () { openMint(50); };
  W.copyMintSheet = function () { var u = location.origin + location.pathname + "?mint=" + encode(S.editionBase || S.moment) + "&n=" + (S.editions ? S.editions.length : 50); try { navigator.clipboard.writeText(u); } catch (e) {} toast("mint sheet link copied"); };
  W.copyUrl = function () { $("surl").select(); try { D.execCommand("copy"); } catch (e) {} navigator.clipboard && navigator.clipboard.writeText($("surl").value); toast("link copied"); };
  W.playShared = function () { hide("share"); openPlay(shareMoment); };

  // ---- boot ----
  W.addEventListener("resize", function () {});
  function boot() {
    var q = new URLSearchParams(location.search);
    setBiome("savanna");
    // optionally augment the feed from a committed manifest
    fetch("moments.json").then(function (r) { return r.json(); }).then(function (j) { W.__EXTRA_MOMENTS__ = j.moments || j; if (S.mode === "feed") renderFeed(); }).catch(function () {});
    if (q.get("mint")) { var mm = decode(q.get("mint")); if (mm && isLegacy(mm)) { S.moment = mm; S.frames = expand(mm); setBiome(mm.b || "savanna"); openMint(parseInt(q.get("n"), 10) || 50); return; } }
    if (q.get("m")) { var m = decode(q.get("m")); if (m) { openPlay(m, false); return; } }
    if (q.get("dial")) { var dorg = W.Organism && W.Organism.fromPk(q.get("dial")); if (dorg) { openPlay(dorg, false); if (q.has("bio")) setTimeout(function () { openBio(dorg.pk); }, 350); if (q.has("grew")) setTimeout(function () { openGrew(dorg.pk); }, 350); if (q.get("at")) setTimeout(function () { dialAt(dorg.pk, parseInt(q.get("at"), 10)); }, 100); if (q.has("lineage")) setTimeout(function () { openLineage(dorg.pk); }, 350); return; } }
    if (q.get("keeper")) { openKeeper(q.get("keeper")); return; }
    if (q.has("zoo")) { go("zoo"); return; }
    if (q.has("create")) { go("create"); return; }
    go("feed");
  }
  boot();
})();
