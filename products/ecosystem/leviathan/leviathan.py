#!/usr/bin/env python3
"""
leviathan.py — the controller for the Leviathan: ONE MIND, MANY BODIES.

Claude is the only intelligence. The LAN brainstems are interchangeable, no-LLM
executors reached through their `POST /api/agent/<Agent>` route (installed by
FlockEndpoint). This module is a CONTROL PLANE that never thinks and never runs a
server: it reaches into a body, runs one named agent's perform() over the direct
route, and hands back a clean, uniform Result. The surface collapses to the model
the mind already thinks in — one(body) and all(bodies).

Prime directive: a down node, a missing agent, a slow call, a half-reachable
fleet, or a body whose /chat LLM is dead are all NORMAL outcomes returned as data,
never raised. Every call -> one Result. Every fan-out -> a COMPLETE per-node map.
Nothing here touches /chat or a Copilot token, so the shared-token throttle that
serialized the fleet to ~1 op/hour is gone; a fan-out finishes in ~max(node).

Every /api/agent call is flight-recorded by FlockEndpoint (caller='hivemind').

Quickstart:
    import leviathan
    leviathan.up()                              # liveness/degrade board
    leviathan.sh('alpha', 'hostname').out       # one body, shell
    leviathan.sh_all('uptime')                  # whole fleet, parallel
    leviathan.all('Base64', action='encode', text='hi')   # one agent, every body
CLI:
    python leviathan.py up
    python leviathan.py sh all "uptime"
    python leviathan.py one alpha RemoteControl command=hostname
"""
import concurrent.futures
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request

# EXAMPLE roster — replace with your own bodies. Best practice: DON'T hardcode;
# set $HIVEMIND_NODES (JSON) or ~/.hivemind/nodes.json so adding a body is one edit.
# A "body" is any host running a brainstem with FlockEndpoint installed (flock_endpoint.py).
DEFAULT_NODES = {
    "alpha": "10.0.0.11",
    "beta": "10.0.0.12",
    "gamma": "10.0.0.13",
}
PORT = int(os.environ.get("PORT", "7071"))


def _load_roster():
    env = os.environ.get("HIVEMIND_NODES")
    if env:
        try:
            return json.loads(env)
        except Exception:
            pass
    cfg = os.path.expanduser("~/.hivemind/nodes.json")
    if os.path.exists(cfg):
        try:
            return json.load(open(cfg))
        except Exception:
            pass
    return dict(DEFAULT_NODES)


# ----------------------------- Result -----------------------------
class Result:
    """The single, uniform per-body outcome. Never raised. bool(Result)==ok."""
    __slots__ = ("node", "ip", "agent", "ok", "status", "value", "raw", "error", "http", "available", "ms")

    def __init__(self, node, ip, agent, ok, status, value=None, raw=None,
                 error=None, http=None, available=None, ms=0):
        self.node, self.ip, self.agent = node, ip, agent
        self.ok, self.status, self.value = ok, status, value
        self.raw, self.error, self.http, self.available, self.ms = raw, error, http, available, ms

    def __bool__(self):
        return self.ok

    # RemoteControl conveniences (value is the {exit_code,stdout,stderr,host} dict)
    def _rc(self):
        return self.value if (self.agent == "RemoteControl" and isinstance(self.value, dict)) else None

    @property
    def rc(self):
        d = self._rc()
        return d.get("exit_code") if d else None

    @property
    def out(self):
        d = self._rc()
        return d.get("stdout", "") if d else (self.value if isinstance(self.value, str) else "")

    @property
    def err(self):
        d = self._rc()
        return d.get("stderr", "") if d else (self.error or "")

    def as_json(self):
        if isinstance(self.value, (dict, list)):
            return self.value
        try:
            return json.loads(self.value)
        except Exception:
            return self.value

    def summary(self):
        if self.status == "ok":
            v = self.value
            s = v if isinstance(v, str) else json.dumps(v)
            return s.replace("\n", " ")[:80]
        return f"{self.status}: {(self.error or '')[:70]}"

    def to_dict(self):
        return {"node": self.node, "ip": self.ip, "agent": self.agent, "ok": self.ok,
                "status": self.status, "value": self.value, "error": self.error,
                "http": self.http, "available": self.available, "ms": self.ms}

    def __repr__(self):
        return f"Result({self.node}/{self.agent or '-'} {self.status} {self.ms}ms)"


# ----------------------------- Flock -----------------------------
class Flock:
    """Fan-out aggregate. HARD INVARIANT: exactly one Result per requested node."""
    def __init__(self, results):
        self.results = results  # dict[node -> Result]

    @property
    def ok(self):
        return bool(self.results) and all(r.ok for r in self.results.values())
    all_ok = ok

    @property
    def any(self):
        return any(r.ok for r in self.results.values())
    any_ok = any

    @property
    def alive(self):
        return [r for r in self.results.values() if r.ok]

    @property
    def fails(self):
        return [r for r in self.results.values() if not r.ok]

    @property
    def values(self):
        return {n: r.value for n, r in self.results.items() if r.ok}

    @property
    def errors(self):
        return {n: r.error for n, r in self.results.items() if not r.ok}

    @property
    def counts(self):
        c = {}
        for r in self.results.values():
            c[r.status] = c.get(r.status, 0) + 1
        return c

    def raise_for_status(self):
        if not self.ok:
            raise HivemindError(f"fleet not ok: {self.counts}", self)
        return self

    def __iter__(self):
        return iter(self.results.values())

    def __getitem__(self, k):
        return self.results[k]

    def __len__(self):
        return len(self.results)

    def __bool__(self):
        return self.ok

    def to_dict(self):
        return {n: r.to_dict() for n, r in self.results.items()}

    def summary(self):
        w = max((len(n) for n in self.results), default=4)
        lines = []
        for n, r in self.results.items():
            mark = "✓" if r.ok else "✗"
            lines.append(f"  {mark} {n:<{w}}  {r.status:<12} {str(r.ms)+'ms':>7}  {r.summary()}")
        head = f"Flock[{len(self)}]  ok={sum(r.ok for r in self.results.values())}/{len(self)}  {self.counts}"
        return head + "\n" + "\n".join(lines)

    __repr__ = summary


class HivemindError(Exception):
    def __init__(self, msg, flock=None):
        super().__init__(msg)
        self.flock = flock


# ----------------------------- pool -----------------------------
_POOL = None


def pool(max_workers=None):
    global _POOL
    if _POOL is None:
        _POOL = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers or max(8, len(DEFAULT_NODES)), thread_name_prefix="leviathan")
    return _POOL


# ----------------------------- Leviathan -----------------------------
class Leviathan:
    def __init__(self, nodes=None, *, port=PORT, timeout=30, max_workers=None):
        self.nodes = dict(nodes) if nodes else _load_roster()
        self.port = port
        self.timeout = timeout
        self.max_workers = max_workers

    # roster ----
    def resolve(self, node):
        return self.nodes.get(node, node)

    def pick(self, *names):
        sub = {n: self.nodes[n] for n in names if n in self.nodes}
        return Leviathan(sub or {n: n for n in names}, port=self.port, timeout=self.timeout)

    # the atom ----
    def one(self, node, agent, *, timeout=None, raw=False, **args):
        ip = self.resolve(node)
        to = self.timeout if timeout is None else timeout
        url = f"http://{ip}:{self.port}/api/agent/{agent}"
        data = json.dumps(args or {}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=to) as r:
                body = r.read().decode("utf-8", "replace")
            return self._ok(node, ip, agent, body, int((time.time() - t0) * 1000), raw)
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8", "replace")
            except Exception:
                body = ""
            return self._http_err(node, ip, agent, e.code, body, int((time.time() - t0) * 1000))
        except (socket.timeout, TimeoutError):
            return Result(node, ip, agent, False, "timeout", error=f"timeout after {to}s", ms=int((time.time() - t0) * 1000))
        except urllib.error.URLError as e:
            if isinstance(e.reason, (socket.timeout, TimeoutError)):
                return Result(node, ip, agent, False, "timeout", error=f"timeout after {to}s", ms=int((time.time() - t0) * 1000))
            return Result(node, ip, agent, False, "down", error=str(e.reason), ms=int((time.time() - t0) * 1000))
        except Exception as e:
            return Result(node, ip, agent, False, "error", error=str(e), ms=int((time.time() - t0) * 1000))

    def _ok(self, node, ip, agent, body, ms, raw):
        try:
            env = json.loads(body)
        except Exception:
            return Result(node, ip, agent, False, "bad_response", raw=body[:500], http=200,
                          error="2xx but not JSON (FlockEndpoint not installed?)", ms=ms)
        if not isinstance(env, dict):
            return Result(node, ip, agent, False, "bad_response", raw=env, http=200, error="2xx non-dict", ms=ms)
        if env.get("ok"):
            inner = env.get("result")
            value = inner
            if not raw and isinstance(inner, str):
                s = inner.strip()
                if s[:1] in "{[":  # only decode structured payloads; leave plain strings ("aGk=", "4142") alone
                    try:
                        value = json.loads(inner)
                    except Exception:
                        value = inner
            return Result(node, ip, agent, True, "ok", value=value, raw=env, http=200, ms=ms)
        return Result(node, ip, agent, False, "error", raw=env, http=200, error=env.get("error"), ms=ms)

    def _http_err(self, node, ip, agent, code, body, ms):
        env = None
        try:
            env = json.loads(body)
        except Exception:
            pass
        if code == 404 and isinstance(env, dict) and "available" in env:
            return Result(node, ip, agent, False, "missing", raw=env, http=404,
                          error=env.get("error") or "agent not found", available=env.get("available"), ms=ms)
        if code == 500 and isinstance(env, dict):
            return Result(node, ip, agent, False, "error", raw=env, http=500,
                          error=env.get("error") or "perform() raised", ms=ms)
        return Result(node, ip, agent, False, "bad_response", raw=body[:300], http=code, error=f"HTTP {code}", ms=ms)

    # fan-out engine ----
    def _fan(self, thunks, deadline):
        results = {n: Result(n, self.resolve(n), "", False, "down", error="no response")
                   for n in thunks}
        p = pool(self.max_workers)
        futs = {p.submit(fn): n for n, fn in thunks.items()}
        done, notdone = concurrent.futures.wait(futs, timeout=deadline)
        for f in done:
            n = futs[f]
            try:
                results[n] = f.result()
            except Exception as e:
                results[n] = Result(n, self.resolve(n), "", False, "error", error=str(e))
        for f in notdone:
            n = futs[f]
            results[n] = Result(n, self.resolve(n), "", False, "timeout", error="gather deadline elapsed")
        return Flock(results)

    def all(self, agent, *, nodes=None, timeout=None, raw=False, **args):
        targets = nodes or list(self.nodes)
        to = self.timeout if timeout is None else timeout
        thunks = {n: (lambda n=n: self.one(n, agent, timeout=to, raw=raw, **args)) for n in targets}
        return self._fan(thunks, to + 5)
    fan = all

    def scatter(self, calls, *, timeout=None):
        """calls: iterable of (node, agent, args_dict). DIFFERENT calls to DIFFERENT bodies, one wave."""
        to = self.timeout if timeout is None else timeout
        thunks = {}
        for i, c in enumerate(calls):
            node, agent, args = (c + ({},))[:3] if isinstance(c, tuple) else (c["node"], c["agent"], c.get("args", {}))
            key = node if node not in thunks else f"{node}#{i}"
            thunks[key] = (lambda node=node, agent=agent, args=args: self.one(node, agent, timeout=to, **(args or {})))
        return self._fan(thunks, to + 5)

    # shell ----
    def sh(self, node, command, *, timeout=60):
        return self.one(node, "RemoteControl", timeout=timeout, command=command)

    def sh_all(self, command, *, nodes=None, timeout=60):
        targets = nodes or list(self.nodes)
        thunks = {n: (lambda n=n: self.sh(n, command, timeout=timeout)) for n in targets}
        return self._fan(thunks, timeout + 5)

    # observability ----
    def _health(self, node, timeout=5):
        ip = self.resolve(node)
        t0 = time.time()
        try:
            with urllib.request.urlopen(f"http://{ip}:{self.port}/health", timeout=timeout) as r:
                h = json.loads(r.read())
            llm = "up" if h.get("copilot") == "✓" else "down"
            val = {"alive": True, "llm": llm, "version": h.get("version"),
                   "model": h.get("model"), "n_agents": len(h.get("agents", [])), "agents": h.get("agents", [])}
            return Result(node, ip, "", True, "ok", value=val, raw=h, http=200, ms=int((time.time() - t0) * 1000))
        except Exception as e:
            st = "timeout" if isinstance(e, (socket.timeout, TimeoutError)) else "down"
            return Result(node, ip, "", False, st, error=str(e), ms=int((time.time() - t0) * 1000))

    def up(self, *, nodes=None, timeout=5):
        targets = nodes or list(self.nodes)
        thunks = {n: (lambda n=n: self._health(n, timeout)) for n in targets}
        return self._fan(thunks, timeout + 3)
    health = up

    def agents(self, node, *, timeout=10):
        ip = self.resolve(node)
        t0 = time.time()
        try:
            with urllib.request.urlopen(f"http://{ip}:{self.port}/agents", timeout=timeout) as r:
                d = json.loads(r.read())
            m = {f.get("filename"): f.get("agents", []) for f in d.get("files", [])}
            return Result(node, ip, "", True, "ok", value=m, raw=d, http=200, ms=int((time.time() - t0) * 1000))
        except Exception as e:
            return Result(node, ip, "", False, "down", error=str(e), ms=int((time.time() - t0) * 1000))

    def who(self, agent, *, nodes=None):
        targets = nodes or list(self.nodes)
        thunks = {n: (lambda n=n: self.agents(n)) for n in targets}
        fl = self._fan(thunks, 12)
        holders = []
        for n, r in fl.results.items():
            if r.ok and any(agent in names for names in r.value.values()):
                holders.append(n)
        return holders

    def route(self, agent, *, strategy="all", timeout=None, **args):
        holders = self.who(agent)
        if not holders:
            return Flock({}) if strategy == "all" else Result("-", "-", agent, False, "missing", error="no live holder")
        if strategy == "all":
            return self.all(agent, nodes=holders, timeout=timeout, **args)
        for n in holders:  # any/first with failover
            r = self.one(n, agent, timeout=timeout, **args)
            if r.ok or r.status not in ("down", "timeout"):
                return r
        return r

    # rollout ----
    def deploy(self, src, *, nodes=None, name=None, syntax_check=True, timeout=60):
        if os.path.exists(src):
            code = open(src, "rb").read()
            fname = name or os.path.basename(src)
        else:
            code = src.encode() if isinstance(src, str) else src
            fname = name or "dropped_agent.py"
        if not fname.endswith("_agent.py"):
            fname = fname.replace(".py", "") + "_agent.py"
        if syntax_check:
            try:
                compile(code, fname, "exec")
            except SyntaxError as e:
                return Flock({n: Result(n, self.resolve(n), "", False, "error", error=f"local syntax error: {e}")
                              for n in (nodes or self.nodes)})
        targets = nodes or list(self.nodes)
        thunks = {n: (lambda n=n: self._import(n, fname, code, timeout)) for n in targets}
        return self._fan(thunks, timeout + 5)

    def _import(self, node, fname, code, timeout):
        ip = self.resolve(node)
        boundary = "----leviathan7f3b"
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{fname}\"\r\n"
                f"Content-Type: text/x-python\r\n\r\n").encode() + code + f"\r\n--{boundary}--\r\n".encode()
        req = urllib.request.Request(f"http://{ip}:{self.port}/agents/import", data=body,
                                     headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST")
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read())
            return Result(node, ip, "import", True, "ok", value=d.get("message"), raw=d, http=200, ms=int((time.time() - t0) * 1000))
        except Exception as e:
            return Result(node, ip, "import", False, "down", error=str(e), ms=int((time.time() - t0) * 1000))

    def forget(self, filename, *, nodes=None):
        targets = nodes or list(self.nodes)
        def _del(n):
            ip = self.resolve(n)
            try:
                urllib.request.urlopen(urllib.request.Request(
                    f"http://{ip}:{self.port}/agents/{filename}", method="DELETE"), timeout=10)
                return Result(n, ip, "forget", True, "ok", value=filename)
            except Exception as e:
                return Result(n, ip, "forget", False, "down", error=str(e))
        return self._fan({n: (lambda n=n: _del(n)) for n in targets}, 15)

    # forge — the foundry, re-homed: manufacture vetted capability FLEET-WIDE ----
    def forge(self, name, code, *, test_args=None, expect=None, description="", nodes=None, pack=None):
        """Install an agent fleet-wide (compile-checked), test it DETERMINISTICALLY on each
        body (call it, assert `expect` is in the output), KEEP where it passes, PRUNE where it
        fails, and CURATE survivors to the pack. No LLM anywhere. Returns a verdict dict."""
        pack = pack or os.path.expanduser("~/.brainstem/foundry_pack.jsonl")
        targets = nodes or list(self.nodes)
        fname = name if name.endswith("_agent.py") else f"{name.lower()}_agent.py"
        rollout = self.deploy(code, name=fname, nodes=targets)
        installed = [n for n, r in rollout.results.items() if r.ok]
        if not installed:
            return {"agent": name, "verdict": "install_fail", "kept_on": [], "pruned_on": [],
                    "fname": fname, "rollout": rollout}
        passed = []
        test = None
        if test_args is not None and expect is not None:
            test = self.all(name, nodes=installed, **test_args)
            for n in installed:
                r = test.results.get(n)
                if not r or not r.ok:
                    continue
                s = r.value if isinstance(r.value, str) else (json.dumps(r.value) if r.value is not None else "")
                if expect in s:
                    passed.append(n)
        else:
            passed = list(installed)  # no test -> keep if it installed/loaded
        failed = [n for n in installed if n not in passed]
        if failed:
            self.forget(fname, nodes=failed)
        verdict = "kept" if passed else "pruned"
        if passed:
            import datetime
            with open(pack, "a") as f:
                f.write(json.dumps({
                    "at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "agent": name, "file": fname, "description": description,
                    "nodes": passed, "fleet_wide": len(passed) == len(targets),
                    "test": (f"{test_args} -> contains '{expect}'  ✓" if expect is not None else "loaded"),
                }) + "\n")
        return {"agent": name, "verdict": verdict, "kept_on": passed, "pruned_on": failed,
                "fname": fname, "rollout": rollout, "test": test}

    def forge_batch(self, specs, *, nodes=None):
        """Forge many specs fleet-wide. Dedups against a single up-front fleet agent-snapshot
        (skips capabilities already everywhere). Returns a list of verdict dicts."""
        targets = nodes or list(self.nodes)
        snap = self._fan({n: (lambda n=n: self.agents(n)) for n in targets}, 12)
        have = {n: (set(a for names in (r.value or {}).values() for a in names) if r.ok else set())
                for n, r in snap.results.items()}
        out = []
        for sp in specs:
            name = sp["name"]
            on = [n for n in targets if name in have.get(n, set())]
            if set(on) >= set(targets):
                out.append({"agent": name, "verdict": "skipped", "kept_on": on, "pruned_on": []})
                continue
            res = self.forge(name, sp["code"], test_args=sp.get("test_args"), expect=sp.get("expect"),
                             description=sp.get("description", ""), nodes=targets)
            for n in res.get("kept_on", []):
                have.setdefault(n, set()).add(name)
            out.append(res)
        return out


# ----------------------------- module singleton + bindings -----------------------------
leviathan = Leviathan()
one = leviathan.one
all_ = leviathan.all
fan = leviathan.all
scatter = leviathan.scatter
sh = leviathan.sh
sh_all = leviathan.sh_all
up = leviathan.up
health = leviathan.up
agents = leviathan.agents
who = leviathan.who
route = leviathan.route
deploy = leviathan.deploy
forget = leviathan.forget
forge = leviathan.forge
forge_batch = leviathan.forge_batch
pick = leviathan.pick


# ----------------------------- CLI -----------------------------
def _kv(items):
    args = {}
    for it in items:
        if "=" in it:
            k, v = it.split("=", 1)
            try:
                v = json.loads(v)
            except Exception:
                pass
            args[k] = v
    return args


def _main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__); return
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    verb = argv[0]
    out = None
    if verb == "nodes":
        out = leviathan.nodes
    elif verb == "up" or verb == "health":
        out = leviathan.up()
    elif verb == "one":
        out = leviathan.one(argv[1], argv[2], **_kv(argv[3:]))
    elif verb == "sh":
        target, cmd = argv[1], argv[2]
        out = leviathan.sh_all(cmd) if target == "all" else leviathan.sh(target, cmd)
    elif verb in ("all", "fan", "run"):
        out = leviathan.all(argv[1], **_kv(argv[2:]))
    elif verb == "who":
        out = leviathan.who(argv[1])
    elif verb == "route":
        out = leviathan.route(argv[1], **_kv(argv[2:]))
    elif verb == "agents":
        out = leviathan.agents(argv[1])
    elif verb == "deploy":
        out = leviathan.deploy(argv[1])
    elif verb == "forget":
        out = leviathan.forget(argv[1])
    elif verb == "forge":
        specs = json.load(open(os.path.expanduser(argv[1]))) if len(argv) > 1 else []
        out = leviathan.forge_batch(specs)
        print("\n".join(f"  {v['verdict']:<12} {v['agent']}  kept_on={v.get('kept_on', [])}" for v in out))
        return
    else:
        print(__doc__); return
    if as_json:
        print(json.dumps(out.to_dict() if hasattr(out, "to_dict") else out, indent=2, default=str))
    elif isinstance(out, (Result, Flock)):
        print(out.summary() if hasattr(out, "summary") else repr(out))
    else:
        print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    _main(sys.argv[1:])
