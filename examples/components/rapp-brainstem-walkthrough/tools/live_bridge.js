/* ═══════════════════════════════════════════════════════════════════════
   LIVE BRIDGE — the vBrainstem tier of the walkthrough.

   Ported from kody-w/vbrainstem's vbrainstem-boot.js (worker lifecycle,
   request dispatch, SSE bridging, downloads), trimmed to what this page
   needs. It lets a trainee sign in with their real GitHub account and run
   the REAL brainstem — brainstem_web.py in Pyodide inside a Web Worker,
   real Copilot completions, real agent execution — while the static
   simulator keeps answering for everyone who hasn't signed in.

   Contract with sim_shim.js (which owns the window.fetch patch):
     window.__VB_LIVE__ = {
       isLive()            live mode on (authed) — route ALL brainstem paths here
       wantsPath(path)     paths that must go live even in sim mode (/login*)
       handles(path)       path is a brainstem route the worker serves
       fetch(vp,input,init) dispatch a virtual request, returns Promise<Response>
       download(vp)        agent-export/workspace download via the worker
       bootFailed          true once the Pyodide boot has failed (fall back to sim)
     }

   Mode flags in localStorage:
     vb_live      '1' once GitHub auth has succeeded → live routing on load
     vb_gh_token  GitHub token mirrored by the worker (same key as vbrainstem)
   ═══════════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var BASE = (function () {
    var p = location.pathname;
    return p.endsWith('/') ? p : p.slice(0, p.lastIndexOf('/') + 1);
  })();

  var ROUTE_PREFIXES = ['/chat', '/health', '/login', '/models', '/voice',
    '/agents', '/diagnostics', '/version', '/debug', '/workspace'];

  function normPath(pathname) {
    var p = pathname;
    if (p.indexOf(BASE) === 0) p = '/' + p.slice(BASE.length);
    return p;
  }
  function handles(pathname) {
    var p = normPath(pathname);
    for (var i = 0; i < ROUTE_PREFIXES.length; i++) {
      if (p === ROUTE_PREFIXES[i] || p.indexOf(ROUTE_PREFIXES[i] + '/') === 0) return true;
    }
    return false;
  }

  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { } }
  function lsDel(k) { try { localStorage.removeItem(k); } catch (e) { } }

  var API = {
    bootFailed: false,
    isLive: function () { return lsGet('vb_live') === '1' && !API.bootFailed; },
    wantsPath: function (pathname) {
      // Any /login traffic is an explicit "go live" signal — the static sim
      // has no accounts. Everything else is gated on isLive().
      return normPath(pathname).indexOf('/login') === 0;
    },
    handles: function (pathname) { return handles(pathname); },
    fetch: null,      // filled below
    download: null,   // filled below
  };
  window.__VB_LIVE__ = API;

  // ── Worker (lazy) ──
  var worker = null;
  var readyResolve, readyReject;
  var ready = new Promise(function (res, rej) { readyResolve = res; readyReject = rej; });
  var pending = new Map();
  var streams = new Map();
  var seq = 0;
  function nextId() { return 'vb' + (++seq); }

  function ensureWorker() {
    if (worker) return ready;
    worker = new Worker(BASE + 'vbrainstem-worker.js');
    worker.onmessage = onWorkerMessage;
    var env = {};
    try { env = JSON.parse(lsGet('vb_env') || '{}'); } catch (e) { env = {}; }
    worker.postMessage({ type: 'init', base: BASE, ghToken: lsGet('vb_gh_token') || null, env: env });
    return ready;
  }

  function onWorkerMessage(event) {
    var msg = event.data || {};
    if (msg.type === 'boot-status') { setChip('⚡ ' + msg.text, '#d29922'); return; }
    if (msg.type === 'ready') {
      if (API.isLive()) setChip('live · running in your browser via Pyodide', '#3fb950', true);
      else setChip(null);
      readyResolve();
      return;
    }
    if (msg.type === 'boot-error') {
      API.bootFailed = true;
      lsDel('vb_live');
      setChip('Live boot failed — back on the static training copy', '#f85149', true);
      readyReject(new Error(msg.error));
      return;
    }
    if (msg.type === 'auth-state') {
      if (msg.ghToken) {
        lsSet('vb_gh_token', msg.ghToken);
      } else {
        lsDel('vb_gh_token');
        // Signed out inside the worker (e.g. /login/switch) — live mode ends.
        if (lsGet('vb_live') === '1') lsDel('vb_live');
      }
      return;
    }
    if (msg.type === 'response') {
      var entry = pending.get(msg.id);
      if (entry) { pending.delete(msg.id); entry(msg); }
      return;
    }
    if (msg.type && msg.type.indexOf('stream-') === 0) {
      var s = streams.get(msg.id);
      if (s) s(msg);
    }
  }

  // ── Status chip (bottom-left, vbrainstem's boot-chip pattern) ──
  var chip = null, chipTimer = null;
  function setChip(text, color, autohide) {
    if (chipTimer) { clearTimeout(chipTimer); chipTimer = null; }
    if (!text) { if (chip) { chip.remove(); chip = null; } return; }
    if (!document.body) {
      document.addEventListener('DOMContentLoaded', function () { setChip(text, color, autohide); }, { once: true });
      return;
    }
    if (!chip) {
      chip = document.createElement('div');
      chip.id = 'vb-boot-chip';
      chip.style.cssText = 'position:fixed;bottom:14px;left:14px;z-index:9989;' +
        'background:#161b22;color:#8b949e;border:1px solid #30363d;border-radius:20px;' +
        'padding:6px 14px;font:12px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;' +
        'display:flex;align-items:center;gap:8px;box-shadow:0 4px 16px rgba(0,0,0,.35)';
      var dot = document.createElement('span');
      dot.id = 'vb-chip-dot';
      dot.style.cssText = 'width:8px;height:8px;border-radius:50%;background:#d29922';
      var label = document.createElement('span');
      label.id = 'vb-chip-text';
      chip.appendChild(dot);
      chip.appendChild(label);
      document.body.appendChild(chip);
    }
    chip.querySelector('#vb-chip-dot').style.background = color || '#d29922';
    chip.querySelector('#vb-chip-text').textContent = text;
    if (autohide) chipTimer = setTimeout(function () { setChip(null); }, 6000);
  }

  // ── Go-live invitation (sim mode only) ──
  // The simulator reports "connected", so the stock UI never asks anyone to
  // sign in. This pill is the door: it opens the stock login overlay, whose
  // /login traffic the router sends here, booting the real brainstem.
  function showInvite() {
    if (API.isLive() || lsGet('vb_gh_token')) return;
    if (!document.body) {
      document.addEventListener('DOMContentLoaded', showInvite, { once: true });
      return;
    }
    if (document.getElementById('vb-live-invite')) return;
    var pill = document.createElement('button');
    pill.id = 'vb-live-invite';
    pill.style.cssText = 'position:fixed;bottom:14px;left:14px;z-index:9989;cursor:pointer;' +
      'background:#161b22;color:#8b949e;border:1px solid #30363d;border-radius:20px;' +
      'padding:6px 14px;font:12px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;' +
      'display:flex;align-items:center;gap:8px;box-shadow:0 4px 16px rgba(0,0,0,.35)';
    pill.innerHTML = '<span style="width:8px;height:8px;border-radius:50%;background:#8b949e"></span>' +
      'training copy — <span style="color:#58a6ff">sign in with GitHub to go live</span>';
    pill.title = 'Runs the real brainstem in your browser (Pyodide) with your GitHub Copilot access';
    pill.onclick = function () {
      if (typeof window.showLoginOverlay === 'function') window.showLoginOverlay();
    };
    document.body.appendChild(pill);
  }
  function hideInvite() {
    var el = document.getElementById('vb-live-invite');
    if (el) el.remove();
  }

  // ── Request plumbing (ported from vbrainstem-boot.js) ──
  function collectHeaders(input, init) {
    var out = {};
    function absorb(h) {
      if (!h) return;
      if (typeof h.forEach === 'function' && h.entries) {
        h.forEach(function (v, k) { out[k.toLowerCase()] = v; });
      } else if (Array.isArray(h)) {
        h.forEach(function (pair) { out[String(pair[0]).toLowerCase()] = pair[1]; });
      } else if (typeof h === 'object') {
        Object.keys(h).forEach(function (k) { out[k.toLowerCase()] = h[k]; });
      }
    }
    if (typeof input === 'object' && input && input.headers) absorb(input.headers);
    if (init && init.headers) absorb(init.headers);
    return out;
  }

  async function extractBody(input, init) {
    var body = init.body != null ? init.body
      : (typeof input === 'object' && input && typeof input.clone === 'function'
        ? await input.clone().text().catch(function () { return null; }) : null);
    var result = { bodyJson: null, form: null, files: null, transfers: [] };
    if (body == null) return result;
    if (typeof FormData !== 'undefined' && body instanceof FormData) {
      result.form = {};
      result.files = {};
      var entries = Array.from(body.entries());
      for (var i = 0; i < entries.length; i++) {
        var k = entries[i][0], v = entries[i][1];
        if (typeof Blob !== 'undefined' && v instanceof Blob) {
          var buf = await v.arrayBuffer();
          result.files[k] = { filename: (v.name || k), bytes: buf };
          result.transfers.push(buf);
        } else {
          result.form[k] = String(v);
        }
      }
      if (!Object.keys(result.files).length) result.files = null;
      return result;
    }
    var text = (typeof body === 'string') ? body : null;
    if (text == null && body && typeof body.text === 'function') text = await body.text();
    if (text != null) {
      try { result.bodyJson = JSON.parse(text); } catch (e) { result.bodyJson = null; }
    }
    return result;
  }

  // Watch auth-deciding responses: the first confirmed sign-in flips the page
  // to live mode and reloads, so every UI surface (models, health, agents)
  // rebuilds against the real brainstem instead of half-sim state.
  function watchAuth(path, json) {
    if (!json || lsGet('vb_live') === '1') return;
    var authedNow =
      (path === '/login/poll' && json.status === 'ok') ||
      (path === '/login/retry' && json.status === 'ok') ||
      (path === '/login/status' && json.authenticated === true) ||
      (path === '/health' && json.status === 'ok' && json.copilot && json.copilot !== 'no_token');
    if (authedNow) {
      lsSet('vb_live', '1');
      setChip('Signed in — restarting live…', '#3fb950');
      hideInvite();
      // Give the stock overlay its "Connected!" beat, then rebuild live.
      setTimeout(function () { location.reload(); }, 1600);
    }
  }

  API.fetch = async function (vp, input, init) {
    init = init || {};
    var method = (init.method || (typeof input === 'object' && input && input.method) || 'GET').toUpperCase();
    var signal = init.signal || (typeof input === 'object' && input && input.signal) || null;
    if (signal && signal.aborted) throw new DOMException('The operation was aborted.', 'AbortError');
    var path = normPath(vp.pathname);
    var query = Object.fromEntries(vp.searchParams ? vp.searchParams.entries() : []);

    var extracted = await extractBody(input, init);
    var headers = collectHeaders(input, init);
    var id = nextId();

    if (method === 'POST' && path === '/chat/stream') {
      return streamFetch(id, path, query, extracted, headers, signal);
    }

    await ensureWorker();
    if (signal && signal.aborted) throw new DOMException('The operation was aborted.', 'AbortError');
    var msg = await new Promise(function (resolve, reject) {
      var onAbort = null;
      if (signal) {
        onAbort = function () {
          pending.delete(id);
          reject(new DOMException('The operation was aborted.', 'AbortError'));
        };
        signal.addEventListener('abort', onAbort, { once: true });
      }
      pending.set(id, function (m) {
        if (signal && onAbort) signal.removeEventListener('abort', onAbort);
        resolve(m);
      });
      worker.postMessage({
        type: 'request', id: id, method: method, path: path, query: query,
        bodyJson: extracted.bodyJson, form: extracted.form, files: extracted.files,
        headers: headers,
      }, extracted.transfers);
    });

    if (msg.download) {
      return new Response(new Blob([msg.download.bytes], { type: msg.download.mimetype }), {
        status: msg.status,
        headers: {
          'Content-Type': msg.download.mimetype,
          'Content-Disposition': 'attachment; filename=' + msg.download.name,
        },
      });
    }
    if (msg.redirect) {
      return new Response(JSON.stringify({ status: 'draft', issue_url: msg.redirect }), {
        status: 200, headers: { 'Content-Type': 'application/json' },
      });
    }
    watchAuth(path, msg.json);
    return new Response(JSON.stringify(msg.json == null ? {} : msg.json), {
      status: msg.status, headers: { 'Content-Type': 'application/json' },
    });
  };

  function streamFetch(id, path, query, extracted, headers, signal) {
    var encoder = new TextEncoder();
    return ensureWorker().then(function () {
      return new Promise(function (resolve, reject) {
        var controllerRef = null, started = false, closed = false;
        if (signal && signal.aborted) {
          reject(new DOMException('The operation was aborted.', 'AbortError'));
          return;
        }
        function abort() {
          worker.postMessage({ type: 'abort', id: id });
          streams.delete(id);
          if (!started) reject(new DOMException('The operation was aborted.', 'AbortError'));
          else if (controllerRef && !closed) {
            closed = true;
            try { controllerRef.error(new DOMException('The operation was aborted.', 'AbortError')); } catch (e) { }
          }
        }
        if (signal) signal.addEventListener('abort', abort, { once: true });

        pending.set(id, function (msg) {
          streams.delete(id);
          resolve(new Response(JSON.stringify(msg.json == null ? {} : msg.json), {
            status: msg.status, headers: { 'Content-Type': 'application/json' },
          }));
        });
        streams.set(id, function (msg) {
          pending.delete(id);
          if (msg.type === 'stream-start') {
            if (started) return;
            started = true;
            var stream = new ReadableStream({
              start: function (controller) { controllerRef = controller; },
              cancel: function () { worker.postMessage({ type: 'abort', id: id }); streams.delete(id); },
            });
            resolve(new Response(stream, {
              status: 200, headers: { 'Content-Type': 'text/event-stream; charset=utf-8' },
            }));
          } else if (msg.type === 'stream-chunk') {
            if (controllerRef && !closed) controllerRef.enqueue(encoder.encode(msg.text));
          } else if (msg.type === 'stream-end') {
            streams.delete(id);
            if (controllerRef && !closed) { closed = true; try { controllerRef.close(); } catch (e) { } }
          } else if (msg.type === 'stream-error') {
            streams.delete(id);
            if (!started) resolve(new Response(JSON.stringify({ error: msg.error }), { status: 500 }));
            else if (controllerRef && !closed) {
              closed = true;
              try { controllerRef.error(new Error(msg.error)); } catch (e) { }
            }
          }
        });
        worker.postMessage({
          type: 'request', id: id, method: 'POST', path: path, query: query,
          bodyJson: extracted.bodyJson, form: extracted.form, files: extracted.files,
          headers: headers,
        }, extracted.transfers);
      });
    });
  }

  API.download = function (vp) {
    var path = normPath(vp.pathname);
    ensureWorker().then(function () {
      var id = nextId();
      return new Promise(function (resolve) {
        pending.set(id, resolve);
        worker.postMessage({ type: 'request', id: id, method: 'GET', path: path, query: {} });
      });
    }).then(function (msg) {
      if (msg.download) {
        var a = document.createElement('a');
        a.href = URL.createObjectURL(new Blob([msg.download.bytes], { type: msg.download.mimetype }));
        a.download = msg.download.name || 'download';
        document.body.appendChild(a);
        a.dispatchEvent(new MouseEvent('click', { bubbles: false }));
        setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 2000);
      } else if (msg.json && msg.json.error) {
        alert(msg.json.error);
      }
    });
  };

  // Live-mode diagnostics report ("🆘 Get Help" submits a <form> to
  // /diagnostics/report) — same interception vbrainstem uses.
  document.addEventListener('submit', function (event) {
    if (!API.isLive()) return;
    var form = event.target;
    var p;
    try { p = new URL(form.action, location.href).pathname; } catch (e) { return; }
    if (!handles(p)) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    var fields = {};
    Array.prototype.forEach.call(form.elements, function (el) {
      if (el.name) fields[el.name] = el.value;
    });
    ensureWorker().then(function () {
      var id = nextId();
      return new Promise(function (resolve) {
        pending.set(id, resolve);
        worker.postMessage({
          type: 'request', id: id, method: (form.method || 'POST').toUpperCase(),
          path: normPath(p), query: {}, form: fields,
          headers: { 'content-type': 'application/x-www-form-urlencoded' },
        });
      });
    }).then(function (msg) {
      var url = msg.redirect || (msg.json && msg.json.issue_url);
      if (url) window.open(url, '_blank', 'noopener');
      else if (msg.json && msg.json.error) alert(msg.json.error);
    });
  }, true);

  // ── Startup ──
  // Returning live user (or one with a mirrored token): boot the real
  // brainstem immediately. Everyone else gets the sim + the go-live pill.
  if (lsGet('vb_live') === '1' || lsGet('vb_gh_token')) {
    ensureWorker();
  } else {
    window.addEventListener('load', showInvite);
  }
})();
