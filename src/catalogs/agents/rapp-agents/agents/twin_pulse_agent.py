#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""twin_pulse_agent.py — the DOG->GOD assimilator (rapp-twin-pulse/1.0).

A single-file RAPP agent (BasicAgent contract) that implements the *client half*
of the pulse defined in ``04-SPEC-rapp-twin-pulse.md`` §3-§4:

  * subscribe to a DOG feed.json (the public, SHA-chained stream of twin bones),
  * verify the RFC 8785 (JCS) SHA-256 chain + parent_sha linkage (and any
    OPTIONAL Ed25519 signature) frame by frame,
  * assimilate verified bones into a local GOD state dir
    (``~/.brainstem/twin_pulse/<twin_id>/``) — public bones the DOG wins,
    private on-device fields the local GOD always wins (§3.1),
  * advance the echo snapshot ONLY on a successful assimilation (§3, §5),
  * reject tampered frames to a quarantine/ dir with a logged security event
    (§4) — never merged into the living GOD,
  * report drift: local head vs DOG head (§6), with rollback protection (§8.2),
  * survive full network loss by serving the last echo (§5).

The cryptographic core (JCS canonicalization + SHA-256 identity + the pure
stdlib Ed25519 verify) is ported byte-for-byte from the DOG's reference
``scripts/pulse_lib.py`` so a frame this agent accepts is exactly a frame the
broadcast surface signed. The canonical form is the contract.

STDLIB ONLY. No third-party imports are required to load or to self-test. Drop
this file into a brainstem's ``agents/`` directory and it hot-loads.

Actions (perform(action=...)):
  subscribe(feed_url[, twin_id])   register a DOG feed for a twin
  assimilate([feed_url])           pull the feed and merge verified frames
  status([feed_url])               drift report (local head vs DOG head); offline-safe
  echo                             return the last surviving echo snapshot
  quarantine_list                  list rejected/quarantined frames + events
  selftest                         stdlib-only self-test against the REAL branch feed

Self-test (perform(action='selftest')) proves, against the real main-branch
feed:
  (a) full-chain verify passes (JCS golden vector + per-frame sha256 + parent
      chain + Ed25519 signatures) and head_sha == feed head_sha,
  (b) a locally-mutated frame is rejected + quarantined + logged,
  (c) the echo survives a simulated network failure (a fetch to an unreachable
      URL still serves the last echo, exit 0),
  plus bones-op semantics (set/delete/merge/patch + post-apply hash reject +
  private-field precedence).
"""

import copy
import hashlib
import json
import os
import re
import socket
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

# --- BasicAgent contract (canonical base in agents/basic_agent.py) ----------
# Triple fallback so the file loads inside a brainstem, from the repo root, or
# fully standalone (python3 twin_pulse_agent.py) without any sibling present.
try:
    from basic_agent import BasicAgent
except ModuleNotFoundError:
    try:
        from agents.basic_agent import BasicAgent
    except ModuleNotFoundError:
        class BasicAgent(object):
            """Minimal standalone shim of the RAPP BasicAgent contract."""

            def __init__(self, name=None, metadata=None):
                if name is not None:
                    self.name = name
                elif not hasattr(self, "name"):
                    self.name = "BasicAgent"
                if metadata is not None:
                    self.metadata = metadata
                elif not hasattr(self, "metadata"):
                    self.metadata = {
                        "name": self.name,
                        "description": "Base agent -- override this.",
                        "parameters": {"type": "object", "properties": {},
                                       "required": []},
                    }

            def perform(self, **kwargs):
                return "Not implemented."

            def system_context(self):
                return None

            def to_tool(self):
                return {
                    "type": "function",
                    "function": {
                        "name": self.name,
                        "description": self.metadata.get("description", ""),
                        "parameters": self.metadata.get(
                            "parameters", {"type": "object", "properties": {}}),
                    },
                }


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@rapp/twin_pulse_agent",
    "version": "1.0.0",
    "display_name": "TwinPulse",
    "description": (
        "The DOG->GOD assimilator. Subscribes to a twin's public pulse "
        "(feed.json), verifies the JCS SHA-256 chain + parent linkage + "
        "optional Ed25519 signature, assimilates verified bones into a local "
        "GOD (local wins private fields), advances the echo, and quarantines "
        "tampered frames. Implements rapp-twin-pulse/1.0 §3-§4."
    ),
    "author": "RAPP",
    "tags": ["twin", "pulse", "dog", "god", "assimilate", "sha256", "shield"],
    "category": "core",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic_agent"],
}

# ===========================================================================
# Wire constants (the contract). Fixed by 04-SPEC / ORDER 1; MUST NOT drift.
# ===========================================================================
SPEC = "rapp-frame/2.0"
FRAME_KIND = "twin.pulse"
FEED_KIND = "twin.pulse.feed"
KERNEL_VERSION = "0.6.0"
N = 64  # feed window: newest N frames in feed.json; frames/ keeps all.

# Default DOG feed and the self-test feed. ORDER 1's PR merged into main and the
# twin-pulse-1.0 branch was deleted post-merge, so both now point at main.
DEFAULT_FEED_URL = "https://raw.githubusercontent.com/kody-w/twin/main/feed.json"
SELFTEST_FEED_URL = (
    "https://raw.githubusercontent.com/kody-w/twin/main/feed.json")

# Pinned trust anchor: the committed pulse pubkey shipped with the twin
# (keys/pulse.ed25519.pub). Pinning the key with the agent — rather than
# fetching it over the same channel as the data — is the "pinned checkpoint"
# analog for authorship (§3.0/§8.3). Overridable via param/env for other twins.
PINNED_PUBKEY_HEX = (
    "ad6b67b41c694c5b87c9249bf97aec767a17a3915b5080807ad1bfe488ec2cdd")

# JCS golden vector (from the DOG's scripts/testdata). Asserting our
# canonicalize() reproduces this exact sha proves byte-identical JCS output
# cross-runtime, without embedding the fragile escaped string.
GOLDEN_INPUT = {
    "": "empty-key",
    "arr": [1, 2, 3, -4, 0],
    "big": 12345678901234567890,
    "bool": [True, False, None],
    "esc": "quote:\" backslash:\\ slash:/ tab:\t nl:\n ctrl:\u0001 unicode:\u20ac",
    "nested": {"Z": 3, "a": 1, "b": 2},
    "\u00e9": "unicode-key",
}
GOLDEN_SHA256 = (
    "94321f276f952854f1d4a785109ac7504e340578e3e767b6ea1166012df385e6")

# Private partition (§3.1): the DOG cannot carry these by construction; if a
# bones-delta ever names one, the local GOD wins and the op is skipped (never
# rejected — the rest of the frame still assimilates).
PRIVATE_PREFIXES = ("private/", "vault/", "secrets/", ".private")

# Env overrides.
ENV_FEED = "TWIN_PULSE_FEED_URL"       # override the feed URL (a.k.a. FRAME_HEADS)
ENV_FEED_ALT = "FRAME_HEADS"
ENV_HOME = "TWIN_PULSE_HOME"           # override ~/.brainstem
ENV_PUBKEY = "TWIN_PULSE_PUBKEY"       # override the pinned pubkey hex

FETCH_TIMEOUT = 12       # seconds per mirror
OFFLINE_TIMEOUT = 4      # short timeout for status/echo so offline fails fast

_MISSING = object()


# ===========================================================================
# 1. RFC 8785 (JCS) canonicalization  -- ported verbatim from pulse_lib.
#    The canonical form is the contract; a single differing byte forks the chain.
# ===========================================================================
_STRING_ESCAPES = {
    '"': '\\"',
    '\\': '\\\\',
    '\b': '\\b',
    '\t': '\\t',
    '\n': '\\n',
    '\f': '\\f',
    '\r': '\\r',
}


def _ser_string(s):
    out = ['"']
    for ch in s:
        esc = _STRING_ESCAPES.get(ch)
        if esc is not None:
            out.append(esc)
        elif ch < '\x20':
            out.append('\\u%04x' % ord(ch))
        else:
            out.append(ch)
    out.append('"')
    return ''.join(out)


def _ser(o):
    # bool is an int subclass — trap True/False before the int branch.
    if o is None:
        return 'null'
    if o is True:
        return 'true'
    if o is False:
        return 'false'
    if isinstance(o, str):
        return _ser_string(o)
    if isinstance(o, bool):  # unreachable — defensive
        return 'true' if o else 'false'
    if isinstance(o, int):
        return str(o)
    if isinstance(o, float):
        raise ValueError(
            "JCS: bare float not allowed in a bones payload (%r) — use an "
            "integer or a string so no runtime can reformat it." % o)
    if isinstance(o, dict):
        parts = []
        for k in sorted(o.keys(), key=lambda s: s.encode('utf-16-be')):
            if not isinstance(k, str):
                raise TypeError("JCS: object keys must be strings")
            parts.append(_ser_string(k) + ':' + _ser(o[k]))
        return '{' + ','.join(parts) + '}'
    if isinstance(o, (list, tuple)):
        return '[' + ','.join(_ser(v) for v in o) + ']'
    raise TypeError("JCS: unsupported type %s" % type(o).__name__)


def canonicalize(obj):
    """RFC 8785 canonical UTF-8 bytes of ``obj`` (no BOM, no trailing NL)."""
    return _ser(obj).encode('utf-8')


def payload_sha256(payload):
    """Lowercase-hex SHA-256 over JCS(payload) — the frame identity."""
    return hashlib.sha256(canonicalize(payload)).hexdigest()


# ===========================================================================
# 2. Ed25519 (RFC 8032) — pure stdlib, ported verbatim from pulse_lib.
#    OPTIONAL authorship proof only; identity is sha-based (§8.3).
# ===========================================================================
_b = 256
_q = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493


def _H(m):
    return hashlib.sha512(m).digest()


def _inv(x):
    return pow(x, _q - 2, _q)


_d = (-121665 * _inv(121666)) % _q
_I = pow(2, (_q - 1) // 4, _q)


def _xrecover(y):
    xx = (y * y - 1) * _inv(_d * y * y + 1) % _q
    x = pow(xx, (_q + 3) // 8, _q)
    if (x * x - xx) % _q != 0:
        x = (x * _I) % _q
    if x % 2 != 0:
        x = _q - x
    return x


_By = (4 * _inv(5)) % _q
_Bx = _xrecover(_By)
_B = (_Bx % _q, _By % _q)


def _edwards_add(P, Q):
    x1, y1 = P
    x2, y2 = Q
    dd = _d * x1 * x2 * y1 * y2
    x3 = (x1 * y2 + x2 * y1) * _inv(1 + dd) % _q
    y3 = (y1 * y2 + x1 * x2) * _inv(1 - dd) % _q
    return (x3 % _q, y3 % _q)


def _scalarmult(P, e):
    Q = (0, 1)
    while e > 0:
        if e & 1:
            Q = _edwards_add(Q, P)
        P = _edwards_add(P, P)
        e >>= 1
    return Q


def _encodeint(y):
    return int(y).to_bytes(_b // 8, 'little')


def _encodepoint(P):
    x, y = P
    val = (y % _q) | ((x & 1) << (_b - 1))
    return val.to_bytes(_b // 8, 'little')


def _bit(h, i):
    return (h[i // 8] >> (i % 8)) & 1


def _clamp(h):
    a = bytearray(h[:32])
    a[0] &= 248
    a[31] &= 127
    a[31] |= 64
    return int.from_bytes(a, 'little')


def _Hint(m):
    return int.from_bytes(_H(m), 'little')


def _isoncurve(P):
    x, y = P
    return (-x * x + y * y - 1 - _d * x * x * y * y) % _q == 0


def _decodepoint(s):
    y = int.from_bytes(s, 'little') & ((1 << (_b - 1)) - 1)
    x = _xrecover(y)
    if (x & 1) != _bit(s, _b - 1):
        x = _q - x
    P = (x, y)
    if not _isoncurve(P):
        raise ValueError("Ed25519: decoded point is not on the curve")
    return P


def ed25519_publickey(seed):
    if len(seed) != 32:
        raise ValueError("Ed25519 seed must be 32 bytes")
    h = _H(seed)
    a = _clamp(h)
    return _encodepoint(_scalarmult(_B, a))


def ed25519_sign(seed, msg):
    if len(seed) != 32:
        raise ValueError("Ed25519 seed must be 32 bytes")
    h = _H(seed)
    a = _clamp(h)
    pk = _encodepoint(_scalarmult(_B, a))
    r = _Hint(h[32:64] + msg)
    R = _scalarmult(_B, r)
    S = (r + _Hint(_encodepoint(R) + pk + msg) * a) % _L
    return _encodepoint(R) + _encodeint(S)


def ed25519_verify(pubkey, msg, sig):
    """True iff ``sig`` is a valid Ed25519 signature. Never raises."""
    try:
        if len(sig) != 64 or len(pubkey) != 32:
            return False
        R = _decodepoint(sig[:32])
        A = _decodepoint(pubkey)
        S = int.from_bytes(sig[32:], 'little')
        if S >= _L:
            return False
        h = _Hint(sig[:32] + pubkey + msg)
        return _scalarmult(_B, S) == _edwards_add(R, _scalarmult(A, h))
    except Exception:
        return False


def verify_frame_sig(frame, pubkey):
    """True if the sig is absent (valid — sig is optional) or a valid Ed25519
    signature over the frame's sha256 (ASCII hex) under ``pubkey``."""
    sig = frame.get('sig')
    if sig is None:
        return True
    if not isinstance(sig, dict) or sig.get('alg') != 'ed25519':
        return False
    try:
        sig_bytes = bytes.fromhex(sig['sig'])
    except Exception:
        return False
    return ed25519_verify(pubkey, frame['sha256'].encode('ascii'), sig_bytes)


# ===========================================================================
# 3. Bones op semantics (§2.2.1) — assimilation MUST be byte-reproducible.
# ===========================================================================
def _json_merge_patch(target, patch):
    """RFC 7386 JSON Merge Patch."""
    if not isinstance(patch, dict):
        return patch
    if not isinstance(target, dict):
        target = {}
    out = dict(target)
    for k, v in patch.items():
        if v is None:
            out.pop(k, None)
        else:
            out[k] = _json_merge_patch(out.get(k), v)
    return out


def _jptr_tokens(pointer):
    """RFC 6901 JSON Pointer -> token list."""
    if pointer in ("", None):
        return []
    if not pointer.startswith('/'):
        raise ValueError("bad JSON pointer: %r" % pointer)
    return [t.replace('~1', '/').replace('~0', '~')
            for t in pointer.split('/')[1:]]


def _jptr_get(doc, toks):
    cur = doc
    for t in toks:
        if isinstance(cur, list):
            cur = cur[int(t)]
        elif isinstance(cur, dict):
            cur = cur[t]
        else:
            raise ValueError("JSON pointer walks into scalar")
    return cur


def _jptr_container(doc, toks):
    """Return (container, last_token) for add/remove/replace."""
    cur = doc
    for t in toks[:-1]:
        if isinstance(cur, list):
            cur = cur[int(t)]
        elif isinstance(cur, dict):
            cur = cur[t]
        else:
            raise ValueError("JSON pointer walks into scalar")
    return cur, toks[-1]


def _apply_json_patch(doc, ops):
    """RFC 6902 JSON Patch (add/remove/replace/move/copy/test)."""
    if not isinstance(ops, list):
        raise ValueError("RFC 6902 patch must be an array of ops")
    for op in ops:
        kind = op.get('op')
        toks = _jptr_tokens(op.get('path'))
        if kind == 'test':
            if _jptr_get(doc, toks) != op.get('value'):
                raise ValueError("RFC 6902 test failed at %s" % op.get('path'))
            continue
        if kind in ('add', 'replace'):
            _patch_add(doc, toks, op.get('value'), replace=(kind == 'replace'))
        elif kind == 'remove':
            _patch_remove(doc, toks)
        elif kind in ('move', 'copy'):
            src = _jptr_tokens(op.get('from'))
            val = copy.deepcopy(_jptr_get(doc, src))
            if kind == 'move':
                _patch_remove(doc, src)
            _patch_add(doc, toks, val, replace=False)
        else:
            raise ValueError("unsupported RFC 6902 op %r" % kind)
    return doc


def _patch_add(doc, toks, value, replace):
    if not toks:
        raise ValueError("cannot add/replace whole document root")
    container, key = _jptr_container(doc, toks)
    if isinstance(container, list):
        if key == '-':
            container.append(value)
        else:
            idx = int(key)
            if replace:
                container[idx] = value
            else:
                container.insert(idx, value)
    elif isinstance(container, dict):
        container[key] = value
    else:
        raise ValueError("cannot add into scalar")


def _patch_remove(doc, toks):
    container, key = _jptr_container(doc, toks)
    if isinstance(container, list):
        del container[int(key)]
    elif isinstance(container, dict):
        del container[key]
    else:
        raise ValueError("cannot remove from scalar")


def _apply_unified_diff(src_text, diff_text):
    """Apply a (hash-anchored) unified diff to text. Lines split on '\\n'."""
    src = src_text.split('\n')
    out = []
    i = 0
    dl = diff_text.split('\n')
    k = 0
    hunk_re = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')
    saw_hunk = False
    while k < len(dl):
        m = hunk_re.match(dl[k])
        if not m:
            k += 1
            continue
        saw_hunk = True
        start_idx = int(m.group(1)) - 1
        if start_idx < 0:
            start_idx = 0
        while i < start_idx and i < len(src):
            out.append(src[i])
            i += 1
        k += 1
        while k < len(dl) and not hunk_re.match(dl[k]):
            h = dl[k]
            if h.startswith('\\'):        # "\ No newline at end of file"
                pass
            elif h.startswith(' '):
                out.append(h[1:])
                i += 1
            elif h.startswith('-'):
                i += 1
            elif h.startswith('+'):
                out.append(h[1:])
            k += 1
    if not saw_hunk:
        raise ValueError("no unified-diff hunks found")
    while i < len(src):
        out.append(src[i])
        i += 1
    return '\n'.join(out)


def _is_json_target(path, cur_value):
    if path.endswith('.json'):
        return True
    if cur_value is not _MISSING and not isinstance(cur_value, str):
        return True
    return False


def _content_hash(path, value):
    """Deterministic post-apply file hash (§2.2.1). JSON targets hash their
    JCS bytes; text targets hash their UTF-8 bytes."""
    if value is None:
        return hashlib.sha256(b'').hexdigest()
    if isinstance(value, str) and not path.endswith('.json'):
        return hashlib.sha256(value.encode('utf-8')).hexdigest()
    return hashlib.sha256(canonicalize(value)).hexdigest()


class OpReject(Exception):
    """Raised when a bones op is malformed or fails its post-apply hash."""


def apply_bones_op(state, path, op):
    """Apply one bones op to the in-memory public state map (path -> value).

    Returns the new value for ``path`` (or _MISSING for delete). Raises
    OpReject on a bad op or a post-apply hash mismatch (§2.2.1)."""
    kind = op.get('op')
    cur = state.get(path, _MISSING)
    if kind == 'set':
        new = op['value']
    elif kind == 'delete':
        new = _MISSING
    elif kind == 'merge':
        base = cur if cur is not _MISSING else {}
        if base is None:
            base = {}
        try:
            new = _json_merge_patch(base, op['value'])
        except Exception as e:
            raise OpReject("merge failed at %s: %s" % (path, e))
    elif kind == 'patch':
        try:
            if _is_json_target(path, cur):
                base = copy.deepcopy(cur) if cur is not _MISSING else None
                new = _apply_json_patch(base, op['diff'])
            else:
                base = cur if cur is not _MISSING else ''
                if not isinstance(base, str):
                    base = ''
                new = _apply_unified_diff(base, op['diff'])
        except OpReject:
            raise
        except Exception as e:
            raise OpReject("patch failed at %s: %s" % (path, e))
    else:
        raise OpReject("unsupported op %r at %s" % (kind, path))

    # Post-apply hash check: any op MAY carry an expected hash; patch/merge
    # MUST (spec). On mismatch, reject the frame like a bad frame (§2.2.1).
    expected = op.get('hash')
    if expected is not None and kind != 'delete':
        got = _content_hash(path, new)
        if got != expected:
            raise OpReject(
                "post-apply hash mismatch at %s: expected %s got %s"
                % (path, expected, got))
    return new


# ===========================================================================
# 4. The hydra — fetch feed.json / frames via raw -> jsdelivr -> raw.githack.
# ===========================================================================
_RAW_RE = re.compile(
    r'^https?://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)$')


def hydra_urls(url):
    """Return [primary, mirror, mirror] for a raw.githubusercontent URL, or
    just [url] for anything else (file://, arbitrary host)."""
    m = _RAW_RE.match(url)
    if not m:
        return [url]
    owner, repo, ref, path = m.groups()
    return [
        url,
        "https://cdn.jsdelivr.net/gh/%s/%s@%s/%s" % (owner, repo, ref, path),
        "https://raw.githack.com/%s/%s/%s/%s" % (owner, repo, ref, path),
    ]


def fetch_bytes(url, timeout=FETCH_TIMEOUT):
    """Fetch via the hydra. Returns (data_bytes, source_url). Raises
    OfflineError if every mirror fails."""
    errors = []
    for u in hydra_urls(url):
        try:
            req = urllib.request.Request(
                u, headers={"User-Agent": "twin-pulse-agent/1.0",
                            "Accept": "application/json, */*"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read(), u
        except (urllib.error.URLError, urllib.error.HTTPError,
                socket.timeout, OSError, ValueError) as e:
            errors.append("%s: %s" % (u, e))
    raise OfflineError("all mirrors failed: " + " | ".join(errors))


class OfflineError(Exception):
    """No mirror reachable — degrade to the echo (§5)."""


def fetch_json(url, timeout=FETCH_TIMEOUT):
    data, src = fetch_bytes(url, timeout=timeout)
    return json.loads(data.decode('utf-8')), src


def _base_url(feed_url):
    """Directory URL of the feed (for frames/<seq>.json backfill)."""
    return feed_url.rsplit('/', 1)[0]


def _frame_url(base_url, seq):
    return "%s/frames/%d.json" % (base_url, seq)


# ===========================================================================
# 5. The GOD — local state store on device.
# ===========================================================================
def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safe_id(twin_id):
    return re.sub(r'[^A-Za-z0-9._@-]+', '_', twin_id or "unknown-twin")


def _home_root(state_root=None):
    if state_root:
        return os.path.abspath(os.path.expanduser(state_root))
    env = os.environ.get(ENV_HOME)
    if env:
        return os.path.abspath(os.path.expanduser(env))
    return os.path.join(os.path.expanduser("~"), ".brainstem")


def _is_private_path(path):
    return any(path == p.rstrip('/') or path.startswith(p)
               for p in PRIVATE_PREFIXES)


class God(object):
    """The Grail Object on Device: the living local twin's state dir."""

    def __init__(self, twin_id, state_root=None):
        self.twin_id = twin_id
        self.root = _home_root(state_root)
        self.dir = os.path.join(self.root, "twin_pulse", _safe_id(twin_id))
        self.bones_dir = os.path.join(self.dir, "bones")
        self.private_dir = os.path.join(self.dir, "private")
        self.frames_dir = os.path.join(self.dir, "frames")
        self.quarantine_dir = os.path.join(self.dir, "quarantine")
        self.state_path = os.path.join(self.dir, "state.json")
        self.echo_path = os.path.join(self.dir, "echo.json")
        self.security_log = os.path.join(self.dir, "security.log")
        for d in (self.bones_dir, self.private_dir, self.frames_dir,
                  self.quarantine_dir):
            os.makedirs(d, exist_ok=True)

    # --- state -----------------------------------------------------------
    def load_state(self):
        if os.path.exists(self.state_path):
            with open(self.state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "twin_id": self.twin_id,
            "last_assimilated_sha": None,
            "head_seq": None,
            "highest_seq": -1,
            "highest_sha": None,
            "feed_url": None,
            "updated": None,
        }

    def save_state(self, state):
        state["updated"] = _now_iso()
        _dump_json(self.state_path, state)
        self._update_global_pointer(state)

    def _update_global_pointer(self, state):
        # ~/.brainstem/.twin_pulse_state.json: twin_id -> pointer (ORDER step).
        ptr_path = os.path.join(self.root, ".twin_pulse_state.json")
        ptr = {}
        if os.path.exists(ptr_path):
            try:
                with open(ptr_path, "r", encoding="utf-8") as f:
                    ptr = json.load(f)
            except Exception:
                ptr = {}
        ptr[self.twin_id] = {
            "dir": self.dir,
            "last_assimilated_sha": state.get("last_assimilated_sha"),
            "head_seq": state.get("head_seq"),
            "feed_url": state.get("feed_url"),
            "updated": state.get("updated"),
        }
        try:
            os.makedirs(self.root, exist_ok=True)
            _dump_json(ptr_path, ptr)
        except Exception:
            pass

    # --- public bones projection ----------------------------------------
    def load_public_state(self):
        state = {}
        for root, _dirs, files in os.walk(self.bones_dir):
            for fn in sorted(files):
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, self.bones_dir).replace(os.sep, '/')
                with open(full, "r", encoding="utf-8") as f:
                    raw = f.read()
                state[rel] = json.loads(raw) if fn.endswith('.json') else raw
        return state

    def persist_public_state(self, state):
        # Rewrite the bones/ projection to match the in-memory state exactly.
        existing = {}
        for root, _dirs, files in os.walk(self.bones_dir):
            for fn in files:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, self.bones_dir).replace(os.sep, '/')
                existing[rel] = full
        for rel, full in existing.items():
            if rel not in state:
                try:
                    os.remove(full)
                except OSError:
                    pass
        for rel, value in state.items():
            full = os.path.join(self.bones_dir, rel)
            os.makedirs(os.path.dirname(full) or self.bones_dir, exist_ok=True)
            with open(full, "w", encoding="utf-8") as f:
                if rel.endswith('.json') or not isinstance(value, str):
                    json.dump(value, f, ensure_ascii=False, indent=2)
                    f.write("\n")
                else:
                    f.write(value)

    def load_private_state(self):
        state = {}
        for root, _dirs, files in os.walk(self.private_dir):
            for fn in sorted(files):
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, self.private_dir).replace(os.sep, '/')
                with open(full, "r", encoding="utf-8") as f:
                    raw = f.read()
                state["private/" + rel] = (
                    json.loads(raw) if fn.endswith('.json') else raw)
        return state

    # --- echo ------------------------------------------------------------
    def snapshot_echo(self, public_state, frame):
        echo = {
            "twin_id": self.twin_id,
            "head_sha": frame["sha256"],
            "head_seq": frame["seq"],
            "ts": frame.get("ts"),
            "assimilated_at": _now_iso(),
            "bones": public_state,
        }
        _dump_json(self.echo_path, echo)
        return echo

    def load_echo(self):
        if os.path.exists(self.echo_path):
            with open(self.echo_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    # --- quarantine + security log --------------------------------------
    def quarantine(self, frame, reason):
        seq = frame.get("seq")
        sha = (frame.get("sha256") or "nosha")[:8]
        base = "%s-%s" % (seq, sha)
        fpath = os.path.join(self.quarantine_dir, base + ".json")
        epath = os.path.join(self.quarantine_dir, base + ".event.json")
        _dump_json(fpath, frame)
        event = {
            "ts": _now_iso(),
            "event": "quarantine",
            "severity": "security",
            "twin_id": self.twin_id,
            "seq": seq,
            "declared_sha256": frame.get("sha256"),
            "recomputed_sha256": _safe_recompute(frame),
            "parent_sha": frame.get("parent_sha"),
            "reason": reason,
            "frame_file": fpath,
        }
        _dump_json(epath, event)
        self.log_event(event)
        return fpath, event

    def log_event(self, event):
        with open(self.security_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def list_quarantine(self):
        out = []
        if os.path.isdir(self.quarantine_dir):
            for fn in sorted(os.listdir(self.quarantine_dir)):
                if fn.endswith(".event.json"):
                    with open(os.path.join(self.quarantine_dir, fn),
                              "r", encoding="utf-8") as f:
                        out.append(json.load(f))
        return out

    def recent_events(self, limit=50):
        if not os.path.exists(self.security_log):
            return []
        with open(self.security_log, "r", encoding="utf-8") as f:
            lines = [ln for ln in f.read().splitlines() if ln.strip()]
        out = []
        for ln in lines[-limit:]:
            try:
                out.append(json.loads(ln))
            except Exception:
                pass
        return out


def _dump_json(path, obj):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _safe_recompute(frame):
    try:
        return payload_sha256(frame["payload"])
    except Exception:
        return None


# ===========================================================================
# 6. Assimilation algorithm (§3).
# ===========================================================================
def _resolve_pubkey(pubkey_hex=None):
    hexval = (pubkey_hex or os.environ.get(ENV_PUBKEY) or PINNED_PUBKEY_HEX)
    try:
        return bytes.fromhex(hexval.strip())
    except Exception:
        return None


def _verify_frame(frame, running_head, pubkey):
    """Return (ok, reason). Checks hash, parent linkage, and optional sig."""
    if not isinstance(frame, dict) or "payload" not in frame:
        return False, "malformed frame"
    if frame.get("spec") != SPEC:
        return False, "spec != %s" % SPEC
    if frame.get("kind") != FRAME_KIND:
        return False, "kind != %s" % FRAME_KIND
    try:
        recomputed = payload_sha256(frame["payload"])
    except Exception as e:
        return False, "payload not canonicalizable: %s" % e
    if recomputed != frame.get("sha256"):
        return False, ("sha256 mismatch: declared %s != recomputed %s"
                       % (frame.get("sha256"), recomputed))
    if frame.get("parent_sha") != running_head:
        return False, ("fork: parent_sha %s does not link to running head %s"
                       % (frame.get("parent_sha"), running_head))
    if frame.get("sig") is not None:
        if pubkey is None or not verify_frame_sig(frame, pubkey):
            return False, "signature invalid"
    return True, None


def _backfill_chain(base_url, from_seq, expected_child_parent, pubkey,
                    timeout=FETCH_TIMEOUT, floor_seq=0):
    """Walk frames/<seq>.json downward from ``from_seq`` collecting verified
    frames until we reach genesis (parent_sha == null) or ``expected_child_parent``
    is satisfied. Returns (ordered_frames_ascending, ok, reason)."""
    collected = []
    need = expected_child_parent
    seq = from_seq
    while seq >= floor_seq and need is not None:
        try:
            frame, _src = fetch_json(_frame_url(base_url, seq), timeout=timeout)
        except OfflineError as e:
            return [], False, "backfill fetch failed at seq %d: %s" % (seq, e)
        try:
            recomputed = payload_sha256(frame["payload"])
        except Exception as e:
            return [], False, "backfill seq %d not canonicalizable: %s" % (seq, e)
        if recomputed != frame.get("sha256"):
            return [], False, "backfill seq %d sha mismatch (tamper)" % seq
        if frame.get("sha256") != need:
            return [], False, ("chain break: seq %d sha %s != needed parent %s"
                               % (seq, frame.get("sha256"), need))
        if frame.get("sig") is not None and (
                pubkey is None or not verify_frame_sig(frame, pubkey)):
            return [], False, "backfill seq %d signature invalid" % seq
        collected.append(frame)
        need = frame.get("parent_sha")
        seq -= 1
    if need is not None:
        return [], False, "could not reach genesis/checkpoint (dangling parent)"
    collected.reverse()
    return collected, True, None


def assimilate_feed(god, feed, base_url, pubkey, allow_backfill=True,
                    timeout=FETCH_TIMEOUT):
    """Core §3 loop over an already-fetched feed dict. Never touches the
    network unless a backfill is required and allow_backfill is True."""
    result = {
        "ok": True,
        "twin_id": god.twin_id,
        "assimilated": [],
        "assimilated_seq_range": None,
        "rejected": [],
        "head_sha": None,
        "dog_head_sha": feed.get("head_sha"),
        "backfilled": [],
        "halted": False,
        "halt_reason": None,
        "in_sync": False,
        "echo_ref": god.echo_path,
    }
    if feed.get("kind") != FEED_KIND:
        result["ok"] = False
        result["halted"] = True
        result["halt_reason"] = "feed.kind != %s (got %r)" % (
            FEED_KIND, feed.get("kind"))
        return result

    state = god.load_state()
    local_head = state.get("last_assimilated_sha")
    highest_seq = state.get("highest_seq", -1)
    highest_sha = state.get("highest_sha")

    frames = sorted(feed.get("frames", []), key=lambda f: f.get("seq", 0))

    # §8.2 rollback / truncation guard: a head that regresses below the highest
    # (seq, sha) we ever assimilated is a drift/security event, not "nothing new".
    if frames:
        feed_max_seq = frames[-1].get("seq", -1)
        if highest_seq is not None and feed_max_seq < highest_seq:
            ev = {
                "ts": _now_iso(), "event": "rollback_suspected",
                "severity": "security", "twin_id": god.twin_id,
                "feed_head_seq": feed_max_seq, "highest_seq_ever": highest_seq,
                "highest_sha_ever": highest_sha,
                "reason": "feed head regressed below highest assimilated seq",
            }
            god.log_event(ev)
            result["rollback_suspected"] = ev

    public_state = god.load_public_state()
    private_state = god.load_private_state()

    to_apply = list(frames)

    # §3.0 first-run bootstrap / chain reconnect via backfill.
    if frames:
        earliest = frames[0]
        earliest_parent = earliest.get("parent_sha")
        need_backfill = False
        if local_head is None:
            # First run: if the earliest in-window frame is not genesis, walk
            # frames/<seq>.json down to genesis (or a pinned checkpoint).
            if not (earliest.get("seq") == 0 and earliest_parent is None):
                need_backfill = True
        else:
            # Incremental: no backfill if our local head is still in the window
            # (we'll prune to it) or a frame links directly off it. Only when the
            # window has slid entirely past us do we reconnect via backfill.
            window_shas = {f.get("sha256") for f in frames}
            window_parents = {f.get("parent_sha") for f in frames}
            if local_head not in window_shas and local_head not in window_parents:
                need_backfill = True

        if need_backfill:
            if not allow_backfill:
                result["ok"] = False
                result["halted"] = True
                result["halt_reason"] = "chain break and backfill disabled"
                return result
            floor = 0 if local_head is None else 0
            back, ok, reason = _backfill_chain(
                base_url, earliest.get("seq", 0) - 1, earliest_parent, pubkey,
                timeout=timeout, floor_seq=floor)
            if not ok:
                # HALT — never merge across a gap (tamper alarm, §3.0/§4).
                ev = {
                    "ts": _now_iso(), "event": "chain_break",
                    "severity": "security", "twin_id": god.twin_id,
                    "reason": reason,
                }
                god.log_event(ev)
                result["ok"] = False
                result["halted"] = True
                result["halt_reason"] = reason
                return result
            # Only prepend backfilled frames newer than our local head.
            if local_head is not None:
                trimmed = []
                seen_head = False
                for fr in back:
                    if seen_head:
                        trimmed.append(fr)
                    if fr.get("sha256") == local_head:
                        seen_head = True
                back = trimmed if seen_head else back
            result["backfilled"] = [fr.get("seq") for fr in back]
            to_apply = back + to_apply

    # Skip frames at/under the local head (already assimilated).
    running_head = local_head
    if local_head is not None:
        pruned = []
        passed = False
        for fr in to_apply:
            if passed:
                pruned.append(fr)
            elif fr.get("sha256") == local_head:
                passed = True
        # If we never saw local_head in the list, keep frames whose parent is
        # our head (normal incremental case where head is out of window).
        if passed:
            to_apply = pruned
        else:
            to_apply = [fr for fr in to_apply
                        if fr.get("parent_sha") == local_head or
                        _links_forward(fr, local_head, to_apply)]

    # The main verify -> merge loop (§3).
    for frame in to_apply:
        ok, reason = _verify_frame(frame, running_head, pubkey)
        if not ok:
            fpath, event = god.quarantine(frame, reason)
            result["rejected"].append({
                "seq": frame.get("seq"),
                "declared_sha256": frame.get("sha256"),
                "reason": reason,
                "quarantine_file": fpath,
            })
            # Never merge; do not advance the head. Later frames that chained
            # off this one will fail the parent check and quarantine too.
            continue

        # Apply bones by precedence (§3.1) onto a trial copy.
        trial = copy.deepcopy(public_state)
        try:
            skipped_private = _apply_bones(trial, frame, private_state, god)
        except OpReject as e:
            fpath, event = god.quarantine(frame, "op reject: %s" % e)
            result["rejected"].append({
                "seq": frame.get("seq"),
                "declared_sha256": frame.get("sha256"),
                "reason": "op reject: %s" % e,
                "quarantine_file": fpath,
            })
            continue

        public_state = trial
        god.persist_public_state(public_state)
        running_head = frame["sha256"]
        echo = god.snapshot_echo(public_state, frame)  # echo advances on success
        result["assimilated"].append(frame.get("seq"))
        if frame.get("seq", -1) > highest_seq:
            highest_seq = frame.get("seq")
            highest_sha = frame["sha256"]
        if skipped_private:
            result.setdefault("private_precedence", []).extend(skipped_private)

    # Persist final head + highest watermark.
    state["last_assimilated_sha"] = running_head
    state["head_seq"] = (result["assimilated"][-1]
                         if result["assimilated"] else state.get("head_seq"))
    state["highest_seq"] = highest_seq
    state["highest_sha"] = highest_sha
    if feed.get("head_sha"):
        state["feed_url"] = state.get("feed_url")
    god.save_state(state)

    result["head_sha"] = running_head
    if result["assimilated"]:
        result["assimilated_seq_range"] = [result["assimilated"][0],
                                           result["assimilated"][-1]]
    result["in_sync"] = (running_head == feed.get("head_sha"))
    result["highest_seq"] = highest_seq
    return result


def _links_forward(frame, local_head, all_frames):
    """True if ``frame`` is a descendant of local_head within all_frames."""
    by_sha = {f.get("sha256"): f for f in all_frames}
    cur = frame
    guard = 0
    while cur is not None and guard < 1000:
        p = cur.get("parent_sha")
        if p == local_head:
            return True
        cur = by_sha.get(p)
        guard += 1
    return False


def _apply_bones(trial_state, frame, private_state, god):
    """Apply a verified frame's bones to trial_state by precedence (§3.1).
    Public paths -> DOG wins (applied). Private paths -> local GOD wins
    (skipped, logged). Returns the list of skipped private paths."""
    skipped = []
    bones = frame["payload"]["bones"]
    for path, op in bones.items():
        if _is_private_path(path):
            # The DOG cannot, by construction, carry private fields. If it
            # tries, the local GOD wins — never overwrite flesh with bones.
            skipped.append(path)
            god.log_event({
                "ts": _now_iso(), "event": "private_precedence",
                "severity": "info", "twin_id": god.twin_id,
                "seq": frame.get("seq"), "path": path,
                "reason": "bones op on a private path; local GOD wins (skipped)",
            })
            continue
        new = apply_bones_op(trial_state, path, op)
        if new is _MISSING:
            trial_state.pop(path, None)
        else:
            trial_state[path] = new
    return skipped


# ===========================================================================
# 7. Drift reporting (§6) + offline (§5).
# ===========================================================================
def compute_drift(god, feed, feed_ok):
    state = god.load_state()
    local_head = state.get("last_assimilated_sha")
    if not feed_ok or feed is None:
        return {
            "status": "offline",
            "local_head": local_head,
            "dog_head": None,
            "note": "network unreachable — serving the echo (§5)",
        }
    dog_head = feed.get("head_sha")
    frames = sorted(feed.get("frames", []), key=lambda f: f.get("seq", 0))
    shas = {f.get("sha256") for f in frames}
    if dog_head == local_head:
        status = "in_sync"
    elif local_head is None:
        status = "dog_ahead"
    elif local_head in shas:
        status = "dog_ahead"
    else:
        # local head not in the current window: either far behind (backfillable)
        # or a genuine divergence. Flag as drift for the operator (§6).
        status = "drift"
    feed_max_seq = frames[-1].get("seq") if frames else None
    highest_seq = state.get("highest_seq", -1)
    rollback = (feed_max_seq is not None and highest_seq is not None
                and feed_max_seq < highest_seq)
    return {
        "status": "rollback_suspected" if rollback else status,
        "local_head": local_head,
        "dog_head": dog_head,
        "feed_head_seq": feed_max_seq,
        "highest_seq_ever": highest_seq,
        "rollback_suspected": rollback,
    }


# ===========================================================================
# 8. The agent.
# ===========================================================================
class TwinPulseAgent(BasicAgent):
    def __init__(self):
        self.name = "TwinPulse"
        self.metadata = {
            "name": self.name,
            "description": (
                "The DOG->GOD assimilator (rapp-twin-pulse/1.0). Subscribe to a "
                "twin's public pulse (feed.json), verify the JCS SHA-256 chain + "
                "parent_sha linkage + optional Ed25519 signature, assimilate "
                "verified bones into the local GOD (public bones the DOG wins, "
                "private on-device fields the local GOD always wins), advance the "
                "echo only on success, and quarantine tampered frames with a "
                "logged security event. Survives network loss by serving the "
                "last echo. Call with action=subscribe|assimilate|status|echo|"
                "quarantine_list|selftest."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["subscribe", "assimilate", "status", "echo",
                                 "quarantine_list", "selftest"],
                        "description": (
                            "What to do. subscribe registers a feed; assimilate "
                            "pulls + merges verified frames; status reports drift "
                            "(offline-safe); echo returns the last surviving "
                            "snapshot; quarantine_list shows rejected frames; "
                            "selftest runs the stdlib self-test against the real "
                            "branch feed. Default: status."),
                    },
                    "feed_url": {
                        "type": "string",
                        "description": (
                            "DOG feed.json URL. Default "
                            "https://raw.githubusercontent.com/kody-w/twin/main/"
                            "feed.json; overridable per call or via the "
                            "TWIN_PULSE_FEED_URL / FRAME_HEADS env vars."),
                    },
                    "twin_id": {
                        "type": "string",
                        "description": (
                            "Override the twin id (normally read from the feed). "
                            "Lets you subscribe/inspect a GOD while offline."),
                    },
                    "pubkey_hex": {
                        "type": "string",
                        "description": (
                            "Ed25519 pubkey (hex) to verify frame signatures "
                            "against. Defaults to the pinned twin pulse key."),
                    },
                    "state_root": {
                        "type": "string",
                        "description": (
                            "Override the GOD root dir (default ~/.brainstem). "
                            "Also settable via TWIN_PULSE_HOME."),
                    },
                    "quiet": {
                        "type": "boolean",
                        "description": "Trim large fields (bones bodies) from output.",
                    },
                },
                "required": [],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    # --- helpers ---------------------------------------------------------
    def _feed_url(self, kwargs):
        return (kwargs.get("feed_url")
                or os.environ.get(ENV_FEED)
                or os.environ.get(ENV_FEED_ALT)
                or DEFAULT_FEED_URL)

    def _resolve_twin(self, kwargs, feed=None):
        if kwargs.get("twin_id"):
            return kwargs["twin_id"]
        if feed and feed.get("twin_id"):
            return feed["twin_id"]
        return None

    # --- dispatch --------------------------------------------------------
    def perform(self, **kwargs):
        action = (kwargs.get("action") or "status").strip().lower()
        try:
            if action == "selftest":
                return json.dumps(
                    run_selftest(quiet=bool(kwargs.get("quiet")),
                                 feed_url=self._feed_url(kwargs)),
                    ensure_ascii=False, indent=2)
            if action == "subscribe":
                return self._do_subscribe(kwargs)
            if action == "assimilate":
                return self._do_assimilate(kwargs)
            if action == "status":
                return self._do_status(kwargs)
            if action == "echo":
                return self._do_echo(kwargs)
            if action == "quarantine_list":
                return self._do_quarantine_list(kwargs)
            return json.dumps({
                "error": "unknown action %r" % action,
                "actions": ["subscribe", "assimilate", "status", "echo",
                            "quarantine_list", "selftest"],
            })
        except Exception as e:  # never crash the brainstem
            return json.dumps({
                "ok": False,
                "action": action,
                "error": "%s: %s" % (type(e).__name__, e),
            })

    def _do_subscribe(self, kwargs):
        feed_url = self._feed_url(kwargs)
        state_root = kwargs.get("state_root")
        twin_id = kwargs.get("twin_id")
        offline = False
        feed = None
        if twin_id is None:
            try:
                feed, _src = fetch_json(feed_url, timeout=OFFLINE_TIMEOUT)
                twin_id = feed.get("twin_id")
            except OfflineError as e:
                offline = True
        if twin_id is None:
            return json.dumps({
                "ok": False, "action": "subscribe", "offline": offline,
                "error": "could not determine twin_id (offline and no twin_id "
                         "param). Pass twin_id to subscribe while dark.",
                "feed_url": feed_url,
            })
        god = God(twin_id, state_root=state_root)
        state = god.load_state()
        state["feed_url"] = feed_url
        god.save_state(state)
        return json.dumps({
            "ok": True, "action": "subscribe", "twin_id": twin_id,
            "feed_url": feed_url, "offline": offline, "god_dir": god.dir,
            "dog_head": feed.get("head_sha") if feed else None,
            "hint": "run action=assimilate to pull and merge verified frames.",
        }, ensure_ascii=False)

    def _do_assimilate(self, kwargs):
        feed_url = self._feed_url(kwargs)
        pubkey = _resolve_pubkey(kwargs.get("pubkey_hex"))
        state_root = kwargs.get("state_root")
        try:
            feed, src = fetch_json(feed_url, timeout=FETCH_TIMEOUT)
        except OfflineError as e:
            # §5: no network -> degrade to the echo, do not crash, exit 0.
            twin_id = self._resolve_twin(kwargs)
            echo = None
            if twin_id:
                echo = God(twin_id, state_root=state_root).load_echo()
            return json.dumps({
                "ok": True, "action": "assimilate", "offline": True,
                "feed_url": feed_url, "note": "network unreachable — echo holds (§5)",
                "echo_head": echo.get("head_sha") if echo else None,
            }, ensure_ascii=False)
        twin_id = self._resolve_twin(kwargs, feed)
        god = God(twin_id, state_root=state_root)
        st = god.load_state()
        st["feed_url"] = feed_url
        god.save_state(st)
        result = assimilate_feed(god, feed, _base_url(feed_url), pubkey)
        result["action"] = "assimilate"
        result["feed_url"] = feed_url
        result["source"] = src
        result["god_dir"] = god.dir
        if kwargs.get("quiet"):
            result.pop("private_precedence", None)
        return json.dumps(result, ensure_ascii=False, indent=2)

    def _do_status(self, kwargs):
        feed_url = self._feed_url(kwargs)
        state_root = kwargs.get("state_root")
        feed = None
        feed_ok = False
        offline = False
        try:
            feed, _src = fetch_json(feed_url, timeout=OFFLINE_TIMEOUT)
            feed_ok = True
        except OfflineError:
            offline = True
        twin_id = self._resolve_twin(kwargs, feed)
        if twin_id is None:
            return json.dumps({
                "ok": True, "action": "status", "offline": offline,
                "note": "no subscribed twin resolvable (offline, no twin_id).",
                "feed_url": feed_url,
            })
        god = God(twin_id, state_root=state_root)
        drift = compute_drift(god, feed, feed_ok)
        echo = god.load_echo()
        out = {
            "ok": True, "action": "status", "twin_id": twin_id,
            "offline": offline, "feed_url": feed_url,
            "drift": drift,
            "echo_head": echo.get("head_sha") if echo else None,
            "echo_seq": echo.get("head_seq") if echo else None,
            "echo_ref": god.echo_path,
            "quarantined": len(god.list_quarantine()),
            "god_dir": god.dir,
        }
        return json.dumps(out, ensure_ascii=False, indent=2)

    def _do_echo(self, kwargs):
        state_root = kwargs.get("state_root")
        # Echo is offline-safe: never needs the network.
        twin_id = kwargs.get("twin_id")
        if twin_id is None:
            feed_url = self._feed_url(kwargs)
            try:
                feed, _src = fetch_json(feed_url, timeout=OFFLINE_TIMEOUT)
                twin_id = feed.get("twin_id")
            except OfflineError:
                twin_id = None
        if twin_id is None:
            return json.dumps({
                "ok": False, "action": "echo",
                "error": "no twin_id (offline and none provided).",
            })
        god = God(twin_id, state_root=state_root)
        echo = god.load_echo()
        if echo is None:
            return json.dumps({
                "ok": True, "action": "echo", "twin_id": twin_id,
                "echo": None, "note": "no echo yet — assimilate first.",
            })
        if kwargs.get("quiet"):
            echo = {k: v for k, v in echo.items() if k != "bones"}
        return json.dumps({
            "ok": True, "action": "echo", "twin_id": twin_id, "echo": echo,
        }, ensure_ascii=False, indent=2)

    def _do_quarantine_list(self, kwargs):
        state_root = kwargs.get("state_root")
        twin_id = self._resolve_twin(kwargs)
        if twin_id is None:
            feed_url = self._feed_url(kwargs)
            try:
                feed, _src = fetch_json(feed_url, timeout=OFFLINE_TIMEOUT)
                twin_id = feed.get("twin_id")
            except OfflineError:
                twin_id = None
        if twin_id is None:
            return json.dumps({
                "ok": False, "action": "quarantine_list",
                "error": "no twin_id (offline and none provided).",
            })
        god = God(twin_id, state_root=state_root)
        return json.dumps({
            "ok": True, "action": "quarantine_list", "twin_id": twin_id,
            "quarantine": god.list_quarantine(),
            "recent_events": god.recent_events(),
            "god_dir": god.dir,
        }, ensure_ascii=False, indent=2)


# ===========================================================================
# 9. Self-test (stdlib only) — runs against the REAL main-branch feed.
# ===========================================================================
def _mutate_frame_payload(frame):
    """Flip a byte in a bones value WITHOUT updating sha256 -> a tamper."""
    f = copy.deepcopy(frame)
    bones = f["payload"]["bones"]
    path = sorted(bones.keys())[0]
    op = bones[path]
    if op.get("op") == "set":
        v = op.get("value")
        if isinstance(v, dict):
            v["__tamper__"] = "disguise"
        elif isinstance(v, str):
            op["value"] = v + "X"
        else:
            op["value"] = [v, "tamper"]
    else:
        op["__tamper__"] = True
    return f


def _check(results, name, ok, detail):
    results["checks"].append({"name": name, "pass": bool(ok), "detail": detail})
    if not ok:
        results["ok"] = False


def run_selftest(quiet=False, feed_url=None):
    feed_url = feed_url or SELFTEST_FEED_URL
    results = {
        "ok": True,
        "agent": "TwinPulse",
        "spec": "rapp-twin-pulse/1.0",
        "feed_url": feed_url,
        "started": _now_iso(),
        "checks": [],
    }
    tmp = tempfile.mkdtemp(prefix="twin_pulse_selftest_")
    pubkey = _resolve_pubkey()

    # --- golden vector (offline, self-contained) -------------------------
    try:
        got_sha = payload_sha256(GOLDEN_INPUT)
        _check(results, "jcs_golden_vector", got_sha == GOLDEN_SHA256,
               {"expected": GOLDEN_SHA256, "got": got_sha})
    except Exception as e:
        _check(results, "jcs_golden_vector", False, {"error": str(e)})

    # --- ops semantics (offline, synthetic): set/delete/merge/patch, post-
    #     apply-hash reject, and private-field precedence (§2.2.1 / §3.1) ---
    try:
        ops_detail = _selftest_ops(tmp, pubkey)
        _check(results, "bones_ops_semantics", ops_detail.pop("_ok"), ops_detail)
    except Exception as e:
        _check(results, "bones_ops_semantics", False, {"error": repr(e)})

    # --- (a) full-chain verify passes against the REAL branch feed --------
    real_feed = None
    real_twin = None
    try:
        real_feed, src = fetch_json(feed_url, timeout=FETCH_TIMEOUT)
        real_twin = real_feed.get("twin_id")
        god_a = God(real_twin, state_root=os.path.join(tmp, "a"))
        res_a = assimilate_feed(god_a, real_feed, _base_url(feed_url),
                                pubkey)
        n_frames = len(real_feed.get("frames", []))
        signed = sum(1 for f in real_feed.get("frames", []) if f.get("sig"))
        ok_a = (res_a["ok"]
                and not res_a["rejected"]
                and res_a["head_sha"] == real_feed.get("head_sha")
                and res_a["in_sync"]
                and len(res_a["assimilated"]) == n_frames)
        # prove every present signature verified (assimilate would have
        # quarantined it otherwise) by re-checking directly too:
        sigs_ok = all(verify_frame_sig(f, pubkey)
                      for f in real_feed.get("frames", []))
        _check(results, "a_full_chain_verify", ok_a and sigs_ok, {
            "frames": n_frames,
            "assimilated_seq_range": res_a["assimilated_seq_range"],
            "head_sha": res_a["head_sha"],
            "feed_head_sha": real_feed.get("head_sha"),
            "in_sync": res_a["in_sync"],
            "rejected": res_a["rejected"],
            "signed_frames_verified": "%d/%d" % (signed, signed),
            "signatures_ok": sigs_ok,
        })
    except OfflineError as e:
        _check(results, "a_full_chain_verify", False,
               {"error": "offline — cannot reach the real branch feed: %s" % e})
    except Exception as e:
        _check(results, "a_full_chain_verify", False, {"error": repr(e)})

    # --- (b) a locally-mutated frame is rejected + quarantined -----------
    try:
        if real_feed is None:
            raise OfflineError("no real feed fetched")
        tampered = copy.deepcopy(real_feed)
        frames = sorted(tampered.get("frames", []), key=lambda f: f.get("seq", 0))
        victim_seq = frames[-1].get("seq")
        frames[-1] = _mutate_frame_payload(frames[-1])
        tampered["frames"] = frames
        god_b = God(real_twin, state_root=os.path.join(tmp, "b"))
        res_b = assimilate_feed(god_b, tampered, _base_url(feed_url),
                                pubkey)
        rejected_seqs = [r["seq"] for r in res_b["rejected"]]
        qlist = god_b.list_quarantine()
        events = god_b.recent_events()
        head_not_tampered = res_b["head_sha"] != tampered.get("head_sha")
        ok_b = (victim_seq in rejected_seqs
                and len(qlist) >= 1
                and any(ev.get("event") == "quarantine" for ev in events)
                and head_not_tampered
                and victim_seq not in res_b["assimilated"])
        _check(results, "b_tamper_rejected_quarantined", ok_b, {
            "tampered_seq": victim_seq,
            "rejected": res_b["rejected"],
            "assimilated": res_b["assimilated"],
            "quarantine_count": len(qlist),
            "security_events": [e.get("event") for e in events],
            "local_head_advanced_past_tamper": head_not_tampered,
        })
    except OfflineError as e:
        _check(results, "b_tamper_rejected_quarantined", False,
               {"error": "offline: %s" % e})
    except Exception as e:
        _check(results, "b_tamper_rejected_quarantined", False, {"error": repr(e)})

    # --- (c) echo survives a simulated network failure -------------------
    try:
        if real_twin is None:
            raise OfflineError("no real twin resolved")
        # Reuse god_a's populated echo; point the agent at an unreachable URL.
        unreachable = "https://twin-pulse-unreachable.invalid/feed.json"
        agent = TwinPulseAgent()
        root_a = os.path.join(tmp, "a")
        # status must not crash, must report offline, and must still surface the echo.
        status_out = json.loads(agent.perform(
            action="status", feed_url=unreachable, twin_id=real_twin,
            state_root=root_a))
        echo_out = json.loads(agent.perform(
            action="echo", feed_url=unreachable, twin_id=real_twin,
            state_root=root_a, quiet=True))
        # assimilate under network failure must also degrade (exit 0, echo holds).
        assim_out = json.loads(agent.perform(
            action="assimilate", feed_url=unreachable, twin_id=real_twin,
            state_root=root_a))
        echo_head = (echo_out.get("echo") or {}).get("head_sha")
        ok_c = (status_out.get("ok") is True
                and status_out.get("offline") is True
                and status_out.get("drift", {}).get("status") == "offline"
                and status_out.get("echo_head") == real_feed.get("head_sha")
                and assim_out.get("ok") is True
                and assim_out.get("offline") is True
                and echo_head == real_feed.get("head_sha"))
        _check(results, "c_echo_survives_offline", ok_c, {
            "unreachable_url": unreachable,
            "status_offline": status_out.get("offline"),
            "status_ok_exit0": status_out.get("ok"),
            "drift_status": status_out.get("drift", {}).get("status"),
            "served_echo_head": echo_head,
            "expected_head": real_feed.get("head_sha"),
            "assimilate_degraded_ok": assim_out.get("ok"),
        })
    except Exception as e:
        _check(results, "c_echo_survives_offline", False, {"error": repr(e)})

    # cleanup
    try:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    except Exception:
        pass

    results["finished"] = _now_iso()
    results["summary"] = "%d/%d checks passed" % (
        sum(1 for c in results["checks"] if c["pass"]), len(results["checks"]))
    return results


def _selftest_ops(tmp, pubkey):
    """Exercise every bones op + post-apply-hash reject + private precedence
    against a synthetic, chained, self-signed-free (unsigned) feed."""
    twin = "rappid:@selftest/ops:0000000000000000000000000000000000000000"
    god = God(twin, state_root=os.path.join(tmp, "ops"))

    def frame(seq, parent, bones):
        payload = {"bones": bones}
        return {
            "spec": SPEC, "kind": FRAME_KIND, "seq": seq, "ts": _now_iso(),
            "twin_id": twin, "kernel_version": KERNEL_VERSION,
            "payload": payload, "sha256": payload_sha256(payload),
            "parent_sha": parent, "sig": None,
        }

    # seq0: set two JSON bones + a text bone
    f0 = frame(0, None, {
        "card.json": {"op": "set", "value": {"hp": 100, "atk": 10}},
        "soul.md": {"op": "set", "value": "line1\nline2\nline3"},
        "private/secret.json": {"op": "set", "value": {"leak": "should-be-skipped"}},
    })
    # seq1: merge (RFC 7386) onto card.json
    f1 = frame(1, f0["sha256"], {
        "card.json": {"op": "merge", "value": {"atk": 20, "hp": None,
                                               "role": "founder"}},
    })
    # seq2: RFC 6902 patch on card.json (add + replace + test)
    f2 = frame(2, f1["sha256"], {
        "card.json": {"op": "patch", "diff": [
            {"op": "test", "path": "/atk", "value": 20},
            {"op": "add", "path": "/lvl", "value": 5},
            {"op": "replace", "path": "/role", "value": "lead"},
        ]},
    })
    # seq3: text unified-diff patch on soul.md
    f3 = frame(3, f2["sha256"], {
        "soul.md": {"op": "patch",
                    "diff": "@@ -2,1 +2,1 @@\n-line2\n+LINE-TWO"},
    })
    # seq4: delete the text bone
    f4 = frame(4, f3["sha256"], {"soul.md": {"op": "delete"}})

    feed = {"spec": SPEC, "kind": FEED_KIND, "twin_id": twin,
            "head_sha": f4["sha256"], "count": 5,
            "frames": [f0, f1, f2, f3, f4]}
    res = assimilate_feed(god, feed, "file:///nonexistent", pubkey,
                          allow_backfill=False)
    pub = god.load_public_state()

    detail = {
        "assimilated": res["assimilated"],
        "rejected": res["rejected"],
        "card": pub.get("card.json"),
        "soul_present": "soul.md" in pub,
        "private_skipped": "private/secret.json" not in pub,
        "private_precedence": res.get("private_precedence"),
        "head_in_sync": res["in_sync"],
    }
    ops_ok = (
        res["assimilated"] == [0, 1, 2, 3, 4]
        and not res["rejected"]
        and pub.get("card.json") == {"atk": 20, "role": "lead", "lvl": 5}
        and "soul.md" not in pub                       # deleted at seq4
        and "private/secret.json" not in pub           # local wins (skipped)
        and res.get("private_precedence") == ["private/secret.json"]
        and res["in_sync"]
    )

    # --- post-apply hash reject: a merge whose declared hash is wrong -----
    god2 = God(twin + ".hashcheck", state_root=os.path.join(tmp, "ops2"))
    g0 = frame(0, None, {"card.json": {"op": "set", "value": {"a": 1}}})
    bad = {"card.json": {"op": "merge", "value": {"b": 2},
                         "hash": "deadbeef" * 8}}
    g1 = frame(1, g0["sha256"], bad)
    feed2 = {"spec": SPEC, "kind": FEED_KIND, "twin_id": twin,
             "head_sha": g1["sha256"], "count": 2, "frames": [g0, g1]}
    res2 = assimilate_feed(god2, feed2, "file:///nonexistent", pubkey,
                           allow_backfill=False)
    hash_reject_ok = (res2["assimilated"] == [0]
                      and len(res2["rejected"]) == 1
                      and "post-apply hash mismatch" in res2["rejected"][0]["reason"])
    detail["post_apply_hash_reject"] = res2["rejected"]

    # --- good post-apply hash: same merge with the CORRECT hash accepts ---
    god3 = God(twin + ".hashok", state_root=os.path.join(tmp, "ops3"))
    h0 = frame(0, None, {"card.json": {"op": "set", "value": {"a": 1}}})
    good_val = _json_merge_patch({"a": 1}, {"b": 2})
    good_hash = _content_hash("card.json", good_val)
    h1 = frame(1, h0["sha256"], {"card.json": {"op": "merge", "value": {"b": 2},
                                               "hash": good_hash}})
    feed3 = {"spec": SPEC, "kind": FEED_KIND, "twin_id": twin,
             "head_sha": h1["sha256"], "count": 2, "frames": [h0, h1]}
    res3 = assimilate_feed(god3, feed3, "file:///nonexistent", pubkey,
                           allow_backfill=False)
    hash_ok_accept = (res3["assimilated"] == [0, 1] and not res3["rejected"])

    detail["_ok"] = bool(ops_ok and hash_reject_ok and hash_ok_accept)
    detail["hash_reject_ok"] = hash_reject_ok
    detail["hash_accept_ok"] = hash_ok_accept
    return detail


# ===========================================================================
# 10. CLI entry point — run the self-test.
# ===========================================================================
def _main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    action = argv[0] if argv else "selftest"
    agent = TwinPulseAgent()
    if action in ("selftest", "test", "--selftest"):
        report = run_selftest()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        print("")
        for c in report["checks"]:
            print("  [%s] %s" % ("PASS" if c["pass"] else "FAIL", c["name"]))
        print("")
        print("SELFTEST: %s — %s" % (
            "OK" if report["ok"] else "FAIL", report["summary"]))
        return 0 if report["ok"] else 1
    # otherwise treat argv as action + optional feed_url
    kwargs = {"action": action}
    if len(argv) > 1:
        kwargs["feed_url"] = argv[1]
    print(agent.perform(**kwargs))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
