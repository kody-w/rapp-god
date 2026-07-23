/* ═══════════════════════════════════════════════════════════════════════
   RAPP BRAINSTEM WALKTHROUGH — STATIC SIMULATOR SHIM
   Everything below this <script> block is the stock brainstem index.html,
   byte-identical to the live product. This shim intercepts the network
   calls the page makes (the local brainstem API + the RAR registry CDN)
   and answers them from an in-browser simulation, so the full 14-step
   "First Interview" guided tour runs end-to-end with zero dependencies:
   no server, no Python, no GitHub auth — just this one HTML file.

   Append ?reset to the URL to wipe the simulation and start fresh.
   ═══════════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var SIM_BUILD = '__SIM_BUILD__';
  var SIM_VERSION = '__SIM_VERSION__';
  var SIM_FILES = __SIM_FILES__;
  var SIM_CATALOG = __SIM_CATALOG__;
  var SIM_RAR_FILES = __SIM_RAR_FILES__;
  var INSTALL_URL = 'https://aka.ms/rappinstall';

  window.__RAPP_SIM__ = { build: SIM_BUILD, version: SIM_VERSION };

  // ── Reset hook ──
  try {
    if (new URLSearchParams(location.search).has('reset')) {
      localStorage.clear();
      history.replaceState(null, '', location.pathname);
    }
  } catch (e) { }

  // ── Persistent simulation state ──
  var LSKEY = 'rapp_sim_state_v1';
  function freshState() {
    return {
      files: Object.assign({}, SIM_FILES),
      memory: [],            // [{fact, name, ts}]
      custom: {},            // filename -> {kind, desc, display}
      sid: 'sim-' + Math.random().toString(16).slice(2, 10) + Math.random().toString(16).slice(2, 10),
      model: 'claude-haiku-4.5'
    };
  }
  var S;
  try {
    S = JSON.parse(localStorage.getItem(LSKEY));
    if (!S || typeof S.files !== 'object') S = freshState();
  } catch (e) { S = freshState(); }
  function save() { try { localStorage.setItem(LSKEY, JSON.stringify(S)); } catch (e) { } }
  save();

  // ── Small helpers ──
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  function jres(obj, status) {
    return new Response(JSON.stringify(obj), {
      status: status || 200, headers: { 'Content-Type': 'application/json' }
    });
  }
  function tres(text, status, type) {
    return new Response(text, { status: status || 200, headers: { 'Content-Type': type || 'text/plain' } });
  }
  function hasFile(re) { return Object.keys(S.files).some(function (f) { return re.test(f); }); }
  // Built-ins the canned brain scripts explicitly; anything else in S.files
  // is a hot-loaded guest agent and gets generic (but honest) handling.
  var BUILTIN_FILES = ['basic_agent.py', 'context_memory_agent.py',
    'manage_memory_agent.py', 'hacker_news_agent.py'];
  function agentInfo(filename) {
    var src = S.files[filename] || '';
    var nm = src.match(/self\.name\s*=\s*['"]([\w@\/ .-]+)['"]/);
    var display = (nm && nm[1]) || classNamesFor(filename)[0] || filename;
    var dm = src.match(/["']description["']\s*:\s*["']([^"'\n]{5,300})["']/);
    return { display: display, desc: (dm && dm[1]) || 'No description in its metadata.' };
  }
  function guestAgents() {
    return Object.keys(S.files).filter(function (f) {
      return /_agent\.py$/.test(f) && BUILTIN_FILES.indexOf(f) < 0 && !S.custom[f];
    });
  }
  function classNamesFor(filename) {
    if (filename === 'basic_agent.py') return [];
    var content = S.files[filename] || '';
    var names = [];
    var re = /self\.name\s*=\s*['"]([\w@\/ .-]+)['"]/g, m;
    while ((m = re.exec(content))) { if (names.indexOf(m[1]) < 0) names.push(m[1]); }
    if (!names.length) {
      var base = filename.replace(/_agent\.py$/, '').replace(/\.py$/, '');
      names = [base.split(/[_\-]+/).map(function (w) {
        return w.charAt(0).toUpperCase() + w.slice(1);
      }).join('')];
    }
    return names;
  }

  // ── Generated-agent template (what LearnNew "writes") ──
  function camel(name) {
    return name.replace(/[^A-Za-z0-9 _-]/g, '').split(/[\s_-]+/).filter(Boolean)
      .map(function (w) { return w.charAt(0).toUpperCase() + w.slice(1); }).join('');
  }
  function snake(name) {
    return camel(name).replace(/([a-z0-9])([A-Z])/g, '$1_$2').toLowerCase();
  }
  var QUOTES = [
    '"The people who are crazy enough to think they can change the world are the ones who do."',
    '"A dream deferred is a dream denied — so build it today." ',
    '"You do not rise to the level of your goals. You fall to the level of your systems."',
    '"The best way to predict the future is to invent it."',
    '"Whether you think you can, or you think you can\'t — you\'re right."'
  ];
  function generatedAgentSource(className, description, isQuote) {
    var body = isQuote
      ? ('        import random\n        return random.choice([\n' + QUOTES.map(function (q) {
        return '            ' + JSON.stringify(q) + ',';
      }).join('\n') + '\n        ])\n')
      : ('        return ' + JSON.stringify('Done. (' + className + ' — generated from your description; edit this file to make it real.)') + '\n');
    return '"""\n' + className + ' — generated by LearnNewAgent from a plain-language description.\nOne file = one agent. Edit it, export it, trade it.\n"""\nfrom agents.basic_agent import BasicAgent\n\n\nclass ' + className + '(BasicAgent):\n    def __init__(self):\n        self.name = \'' + className + '\'\n        self.metadata = {\n            "name": self.name,\n            "description": ' + JSON.stringify(description) + ',\n            "parameters": {"type": "object", "properties": {}, "required": []}\n        }\n        super().__init__(name=self.name, metadata=self.metadata)\n\n    def perform(self, **kwargs):\n' + body;
  }

  // ── Canned Hacker News stories ──
  var HN = [
    { title: 'Show HN: I run a personal AI agent server from a folder of .py files', points: 412, comments: 187 },
    { title: 'The best software is a directory of small, readable files', points: 356, comments: 214 },
    { title: 'Ask HN: What did you automate this week?', points: 289, comments: 341 },
    { title: 'Local-first AI: why your assistant should live on your machine', points: 251, comments: 129 },
    { title: 'An agent that writes other agents (and when to trust it)', points: 198, comments: 96 }
  ];

  // ── The canned brain: route a user message to a scripted reply ──
  function think(text) {
    var t = (text || '').trim();
    var lower = t.toLowerCase();
    var logs = null, response;

    // 1) Résumé
    if (/^what can you do/i.test(t)) {
      var bullets = [];
      if (hasFile(/manage_memory_agent\.py$/)) bullets.push('- **Remember you** — ManageMemory saves what matters about you to disk, permanently.');
      if (hasFile(/context_memory_agent\.py$/)) bullets.push('- **Recall it anywhere** — ContextMemory brings what I know into every new conversation.');
      if (hasFile(/hacker_news_agent\.py$/)) bullets.push('- **Fetch Hacker News** — top stories, on demand.');
      if (hasFile(/learn_new_agent\.py$/)) bullets.push('- **Build new agents** — describe one in plain words and LearnNew writes the file.');
      Object.keys(S.custom).forEach(function (f) {
        if (S.files[f]) bullets.push('- **' + S.custom[f].display + '** — ' + S.custom[f].desc);
      });
      guestAgents().forEach(function (f) {
        var info = agentInfo(f);
        bullets.push('- **' + info.display + '** — ' + info.desc + ' *(hot-loaded from `' + f + '`)*');
      });
      bullets.push('- **Hot-load anything** — drop a `*_agent.py` file on this window and it\'s live instantly.');
      response = 'One local brainstem, ready to work. Right now I can:\n\n' + bullets.join('\n') +
        '\n\n**Next step:** tell me who you are — try *"Remember, my name is … and I …"*';
      return { response: response, logs: null };
    }

    // 2) Recall (must outrank the generic "remember" matcher)
    if (/what do you remember/i.test(t)) {
      if (!S.memory.length) {
        return {
          response: 'Nothing yet — my long-term memory is empty. Introduce yourself: *"Remember, my name is … and I …"* and I\'ll keep it.',
          logs: '[ContextMemory] {"status":"success","memories":[]}'
        };
      }
      var known = S.memory.map(function (m) { return '- ' + m.fact; }).join('\n');
      var name = null;
      for (var i = S.memory.length - 1; i >= 0; i--) { if (S.memory[i].name) { name = S.memory[i].name; break; } }
      response = (name ? 'You\'re **' + name + '**. ' : '') +
        'Here\'s what I\'m carrying in long-term memory — this conversation gave me zero hints:\n\n' + known +
        '\n\nThat\'s the loop: you told me once, I kept it on disk, and a brand-new conversation still knows it. **Claim → test → verify.**';
      return {
        response: response,
        logs: '[ContextMemory] ' + JSON.stringify({ status: 'success', memories: S.memory.map(function (m) { return m.fact; }) })
      };
    }

    // 3) Next steps (the starter pill sends a long payload override, so match
    // its distinctive phrasing too, not just the visible label)
    if (/what should i do next|show me what i am missing|ideas for agents i do not have/i.test(t)) {
      response = 'You have the core loop. Here\'s what you\'re **missing** — ten agents you could create just by describing them:\n\n' +
        '1. **MorningBriefing** — calendar, weather, and top HN stories in one card.\n' +
        '2. **FileJanitor** — sweeps your Downloads into dated folders on command.\n' +
        '3. **GitStandup** — reads your last 24h of commits and writes your standup.\n' +
        '4. **MeetingRecap** — paste a transcript, get decisions and action items.\n' +
        '5. **PriceWatch** — checks a product page and remembers the last price.\n' +
        '6. **AgentSmith** — reviews your other agents and suggests fixes.\n' +
        '7. **DailyJournal** — asks you three questions each evening and files the answers.\n' +
        '8. **ApiPoker** — hits any REST endpoint you describe and explains the response.\n' +
        '9. **TeamPack** — bundles your best agents into one file for a teammate.\n' +
        '10. **QuestMaster** — turns any tutorial into quests it walks you through.\n\n' +
        'Every one starts the same way: *"Learn a new agent called … that …"*';
      return { response: response, logs: null };
    }

    // 4) Create a new agent (needs LearnNew installed)
    var wantsCreate = /learn\s+(a\s+)?new\s+agent|new\s+agent\s+called|create\s+(an?\s+)?agent|make\s+(me\s+)?(an?\s+)?agent/i.test(t);
    if (wantsCreate) {
      if (!hasFile(/learn_new_agent\.py$/)) {
        return {
          response: 'I can\'t build agents yet — there\'s no builder in my head. Open the **📖 registry** (book button, top right), search *learn new*, and add **@rapp/learn_new**. Then ask me again.',
          logs: null
        };
      }
      var nm = t.match(/called\s+["'“]?([A-Za-z][\w ]*?)["'”]?(?:\s+(?:that|which|who|to)\b|[.,!?]|$)/i);
      var className = camel((nm && nm[1]) || 'MyFirstAgent');
      var filename = snake(className) + '_agent.py';
      var descM = t.match(/\b(?:that|which|to)\s+(.{10,240}?)[.!?]?$/i);
      var desc = (descM && descM[1]) || ('Created from: ' + t.slice(0, 160));
      var isQuote = /quote|inspir|motivat/i.test(t) || /quote/i.test(className);
      S.files[filename] = generatedAgentSource(className, desc, isQuote);
      S.custom[filename] = { kind: isQuote ? 'quote' : 'generic', desc: desc, display: className };
      save();
      return {
        response: 'Born: **' + className + '**.\n\nI wrote `' + filename + '` into your agents/ folder and hot-loaded it — no restart. Open the **⊕ panel** and it\'s in the list, exportable and tradeable like any other agent.' + (isQuote ? ' Ask me for motivation whenever you want a quote.' : ''),
        logs: '[LearnNewAgent] ' + JSON.stringify({ status: 'created', filename: filename, class: className, description: desc })
      };
    }

    // 5) Quote / motivation (after a quote agent exists)
    var quoteFile = Object.keys(S.custom).filter(function (f) { return S.files[f] && S.custom[f].kind === 'quote'; })[0];
    if (quoteFile && /quote|motivat|inspir/i.test(lower)) {
      var q = QUOTES[Math.floor(Math.random() * QUOTES.length)];
      return {
        response: q + '\n\n— served by your own **' + S.custom[quoteFile].display + '** agent.',
        logs: '[' + S.custom[quoteFile].display + '] ' + JSON.stringify({ status: 'success', quote: q })
      };
    }

    // 6) Hacker News
    if (/hacker.?news|top stories|latest news|\bhn\b/i.test(lower)) {
      if (!hasFile(/hacker_news_agent\.py$/)) {
        return {
          response: 'I can\'t do that right now. The Hacker News agent isn\'t in my agents/ folder anymore, so I have no way to fetch stories — and I\'m not going to invent headlines. Drop `hacker_news_agent.py` back onto this window (or reinstall it from the 📖 registry) and ask me again.',
          logs: null
        };
      }
      var lines = HN.map(function (s, i) {
        return (i + 1) + '. **' + s.title + '** — ' + s.points + ' points, ' + s.comments + ' comments';
      }).join('\n');
      return {
        response: 'Top of Hacker News right now:\n\n' + lines,
        logs: '[HackerNews] ' + JSON.stringify({ stories: HN })
      };
    }

    // 7) Remember / introduce yourself
    if (/\bremember\b|my name is|call me\b/i.test(lower)) {
      var fact = t.replace(/^\s*remember[,:\s]+/i, '').trim() || t;
      var nmatch = t.match(/my name is\s+([A-Za-z][\w'’-]*)/i) || t.match(/call me\s+([A-Za-z][\w'’-]*)/i) || t.match(/\bi'?m\s+([A-Z][\w'’-]*)/);
      var who = nmatch ? nmatch[1] : null;
      S.memory.push({ fact: fact, name: who, ts: new Date().toISOString() });
      save();
      return {
        response: (who ? 'Nice to meet you, **' + who + '**. ' : 'Got it. ') +
          'I judged that worth keeping and filed it in long-term memory — the file on disk, not this chat. Clear the conversation and ask me what I remember: it survives.',
        logs: '[ManageMemory] ' + JSON.stringify({ status: 'success', message: 'Memory stored for default_user.', memory: { fact: fact } })
      };
    }

    // 8) Hot-loaded guest agent — the file is genuinely registered, but the
    // training copy only executes the guided-tour agents. Be honest about
    // that, and point at the two real paths.
    var foldTxt = function (x) { return (x || '').toLowerCase().replace(/[_\-\s]+/g, ' '); };
    var msgFold = ' ' + foldTxt(t) + ' ';
    var guestHit = null, guestScore = 0;
    guestAgents().forEach(function (f) {
      var info = agentInfo(f);
      var words = foldTxt(info.display.replace(/([a-z0-9])([A-Z])/g, '$1 $2'))
        .split(' ').filter(function (w) { return w.length > 3 && w !== 'agent'; });
      var hits = words.filter(function (w) { return msgFold.indexOf(' ' + w) >= 0 || msgFold.indexOf(w + ' ') >= 0; }).length;
      var enough = words.length <= 1 ? hits >= 1 : hits >= 2;
      if (enough && hits > guestScore) { guestScore = hits; guestHit = { file: f, info: info }; }
    });
    if (guestHit) {
      return {
        response: '**' + guestHit.info.display + '** is loaded — I can see it in my head (`' + guestHit.file + '`, hot-loaded when you dropped it):\n\n' +
          '> ' + guestHit.info.desc + '\n\n' +
          'But I\'ll be straight with you: this is the **training copy**, and only the guided-tour agents actually execute here. I\'m not going to fake its output. To run **' + guestHit.info.display + '** for real:\n' +
          '- **Go live in this page** — click *"sign in with GitHub to go live"* (bottom left); your dropped agents run as real Python.\n' +
          '- **Install locally** in one line: **[aka.ms/rappinstall](' + INSTALL_URL + ')**',
        logs: null
      };
    }

    // 9) Fallback — honest about being the training copy
    response = 'Straight answer: this page is the **walkthrough copy** of the brainstem — the real UI wired to a canned brain, so you can train with zero setup. I can act out the guided-tour moves: memory, the agents panel, Hacker News, the registry, and building an agent with LearnNew.\n\n' +
      'Take the tour (the pill in the welcome message above). Want the real thing? Two ways:\n' +
      '- **Go live right here** — click *"sign in with GitHub to go live"* (bottom left) and this exact page becomes a real brainstem running in your browser, powered by your Copilot access.\n' +
      '- **Install locally** in one line: **[aka.ms/rappinstall](' + INSTALL_URL + ')**';
    return { response: response, logs: null };
  }

  function chatResult(body) {
    var out = think(body && body.user_input);
    return {
      response: out.response,
      agent_logs: out.logs || '',
      session_id: S.sid,
      model: S.model,
      requested_model: S.model
    };
  }

  // ── SSE stream builder (mirrors /chat/stream wire format) ──
  function sseResponse(result, signal) {
    var enc = new TextEncoder();
    var stream = new ReadableStream({
      start: function (c) {
        (async function () {
          function push(obj) { c.enqueue(enc.encode('data: ' + JSON.stringify(obj) + '\n\n')); }
          try {
            await sleep(420 + Math.random() * 480);          // "thinking"
            if (result.agent_logs) {
              await sleep(500 + Math.random() * 400);         // "tool round"
              push({ type: 'agent', logs: result.agent_logs });
              await sleep(220);
            }
            var words = result.response.match(/\S+\s*/g) || [result.response];
            var i = 0;
            while (i < words.length) {
              if (signal && signal.aborted) break;
              var n = 1 + Math.floor(Math.random() * 3);
              push({ type: 'delta', text: words.slice(i, i + n).join('') });
              i += n;
              await sleep(12 + Math.random() * 34);
            }
            push(Object.assign({ type: 'done', streamed: true }, result));
          } catch (e) { /* consumer cancelled */ }
          try { c.close(); } catch (e) { }
        })();
      }
    });
    return new Response(stream, { status: 200, headers: { 'Content-Type': 'text/event-stream' } });
  }

  // ── Route table ──
  function readJson(init) {
    try { return JSON.parse((init && init.body) || '{}'); } catch (e) { return {}; }
  }

  async function importAgentFile(init) {
    var fd = init && init.body;
    if (!(fd instanceof FormData)) return jres({ error: 'no file' }, 400);
    var f = fd.get('file');
    if (!f) return jres({ error: 'no file' }, 400);
    var name = (f.name || 'agent.py').split(/[\\/]/).pop();
    // Browsers rename duplicate downloads ("x (1).py") — restore the original.
    name = name.replace(/\s*\(\d+\)(?=\.py$)/, '').replace(/[^\w.\-]/g, '_');
    if (!/\.py$/.test(name)) return jres({ error: 'Only .py agent files are supported.' }, 400);
    var content = await f.text();
    S.files[name] = content;
    save();
    return jres({ status: 'ok', filename: name });
  }

  function routeApi(u, init) {
    var p = u.pathname;
    // Only intercept when the path is one of the brainstem endpoints —
    // same-origin page assets fall through untouched.
    switch (p) {
      case '/health':
        return jres({ status: 'ok', version: SIM_VERSION, copilot: 'ok', model: S.model });
      case '/models':
        return jres({
          current: S.model,
          models: [
            { id: 'claude-haiku-4.5', name: 'Claude Haiku 4.5' },
            { id: 'claude-sonnet-4.5', name: 'Claude Sonnet 4.5' },
            { id: 'gpt-4o', name: 'GPT-4o' },
            { id: 'gpt-4o-mini', name: 'GPT-4o mini' }
          ]
        });
      case '/models/set': {
        var b = readJson(init);
        S.model = (b.model && b.model !== 'auto') ? b.model : 'claude-haiku-4.5';
        save();
        return jres({ status: 'ok', model: S.model });
      }
      case '/voice': return jres({ voice_mode: false });
      case '/voice/toggle': return jres({ voice_mode: false, note: 'Voice is not part of the static walkthrough.' });
      case '/voice/config': return jres((init && init.method === 'POST') ? { status: 'ok' } : {});
      case '/voice/export':
      case '/voice/import': return jres({ error: 'Not available in the static walkthrough.' }, 400);
      case '/login/status': return jres({ pending: false });
      case '/login':
      case '/login/poll':
      case '/login/retry': return jres({ status: 'ok' });
      case '/login/switch': return jres({ error: 'This is the static walkthrough — there\'s no account here to switch. Install the real brainstem to sign in: ' + INSTALL_URL });
      case '/diagnostics/book.json':
        return jres({ generated_by: 'rapp-brainstem-walkthrough static simulator', build: SIM_BUILD, note: 'No live diagnostics — this page runs entirely in your browser.' });
      case '/agents': {
        if (!init || !init.method || init.method === 'GET') {
          var files = Object.keys(S.files).filter(function (f) { return /_agent\.py$/.test(f); }).sort()
            .map(function (f) { return { filename: f, agents: classNamesFor(f) }; });
          return jres({ files: files });
        }
        return null;
      }
      case '/agents/import': return importAgentFile(init);
      case '/chat': {
        var result = chatResult(readJson(init));
        return sleep(650 + Math.random() * 650).then(function () { return jres(result); });
      }
      case '/chat/stream':
        return sseResponse(chatResult(readJson(init)), init && init.signal);
    }
    var em = p.match(/^\/agents\/export\/(.+)$/);
    if (em) {
      var xf = decodeURIComponent(em[1]);
      return S.files[xf] != null ? tres(S.files[xf], 200, 'text/x-python') : jres({ error: 'not found' }, 404);
    }
    var dm = p.match(/^\/agents\/([^\/]+\.py)$/);
    if (dm && init && init.method === 'DELETE') {
      var df = decodeURIComponent(dm[1]);
      if (S.files[df] == null) return jres({ error: 'not found' }, 404);
      delete S.files[df];
      delete S.custom[df];
      save();
      return jres({ status: 'ok' });
    }
    return null;
  }

  function routeRar(u) {
    var m = u.pathname.match(/\/RAR(?:@[^\/]+)?\/(?:[0-9a-f]{7,40}\/)?(.+)$/);
    if (!m) return null;
    var path = decodeURIComponent(m[1]);
    if (path === 'registry.json') {
      return jres({ schema: 'rar-registry/1.0', generated: 'static-walkthrough', agents: SIM_CATALOG });
    }
    if (SIM_RAR_FILES[path] != null) return tres(SIM_RAR_FILES[path], 200, 'text/x-python');
    return jres({ error: 'not in the walkthrough catalog' }, 404);
  }

  // ── fetch interception ──
  // Two tiers: if the live bridge (tools/live_bridge.js) is active — the
  // user signed in with GitHub — brainstem routes go to the REAL brainstem
  // (brainstem_web.py in a Pyodide worker) and the RAR registry is fetched
  // for real. Otherwise the static simulation answers. /login traffic always
  // goes live: signing in IS the upgrade path out of the sim.
  var realFetch = window.fetch.bind(window);
  window.fetch = function (input, init) {
    try {
      var url = (typeof input === 'string') ? input : ((input && input.url) || '');
      var u = new URL(url, location.href);
      var LIVE = window.__VB_LIVE__;
      var hit = null;
      if (u.origin === location.origin || /^127\.0\.0\.1|^localhost$/.test(u.hostname)) {
        if (LIVE && LIVE.handles(u.pathname) && (LIVE.isLive() || LIVE.wantsPath(u.pathname))) {
          return LIVE.fetch(u, input, init);
        }
        hit = routeApi(u, init || (typeof input === 'object' ? input : null));
      } else if (/raw\.githubusercontent\.com|cdn\.jsdelivr\.net/.test(u.hostname)) {
        if (LIVE && LIVE.isLive()) return realFetch(input, init);
        hit = routeRar(u);
      }
      if (hit) return Promise.resolve(hit);
    } catch (e) { /* fall through to the network */ }
    return realFetch(input, init);
  };

  // ── window.open interception: Export downloads the simulated file ──
  var realOpen = window.open ? window.open.bind(window) : null;
  window.open = function (url, target, features) {
    try {
      var LIVE = window.__VB_LIVE__;
      if (LIVE && LIVE.isLive() && typeof url === 'string') {
        var lu = new URL(url, location.href);
        if (lu.origin === location.origin && LIVE.handles(lu.pathname)) {
          LIVE.download(lu);
          return null;
        }
      }
      if (typeof url === 'string' && url.indexOf('/agents/export/') !== -1) {
        var name = decodeURIComponent(url.split('/agents/export/')[1].split(/[?#]/)[0]);
        if (S.files[name] != null) {
          var blob = new Blob([S.files[name]], { type: 'text/x-python' });
          var a = document.createElement('a');
          a.href = URL.createObjectURL(blob);
          a.download = name;
          document.body.appendChild(a);
          // Non-bubbling click: a bubbled one would reach the document-level
          // outside-click handler and close the agents panel — the real
          // window.open() never does that.
          a.dispatchEvent(new MouseEvent('click', { bubbles: false }));
          a.remove();
          setTimeout(function () { URL.revokeObjectURL(a.href); }, 4000);
          return null;
        }
      }
    } catch (e) { }
    return realOpen ? realOpen(url, target, features) : null;
  };

  // ── Auto-start the tour ──
  // This page exists to run the 14-step guide, so enter it immediately —
  // no hunting for the invite pill. Guards keep it polite: it auto-starts
  // at most ONCE per browser (exiting via ✕ clears rapp_tour_step but not
  // rapp_tour_done, so without our own flag a reload would trap the user
  // back in the tour), a finished tour never restarts, and a mid-flight
  // tour is left to the stock resume logic. ?reset clears everything.
  window.addEventListener('load', function () {
    setTimeout(function () {
      try {
        if (localStorage.getItem('rapp_tour_done')) return;
        if (localStorage.getItem('rapp_sim_tour_auto')) return;
        if (localStorage.getItem('rapp_tour_step') !== null) return;
        if (typeof window.startTour !== 'function') return;
        localStorage.setItem('rapp_sim_tour_auto', '1');
        window.startTour();
      } catch (e) { }
    }, 700);
  });
})();
