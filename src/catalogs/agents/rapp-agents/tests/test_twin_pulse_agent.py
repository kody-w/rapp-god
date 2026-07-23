"""Tests for agents/twin_pulse_agent.py — the DOG->GOD assimilator.

Offline-safe: every test here runs with no network. The network-backed
end-to-end self-test (run_selftest) is exercised separately and skipped
gracefully when the real branch feed is unreachable.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
AGENTS_DIR = REPO_ROOT / "agents"
sys.path.insert(0, str(AGENTS_DIR))

import twin_pulse_agent as tp  # noqa: E402
from twin_pulse_agent import (  # noqa: E402
    God,
    TwinPulseAgent,
    assimilate_feed,
    canonicalize,
    ed25519_publickey,
    ed25519_sign,
    ed25519_verify,
    payload_sha256,
    verify_frame_sig,
)
from basic_agent import BasicAgent  # noqa: E402


def _frame(twin, seq, parent, bones, seed=None):
    payload = {"bones": bones}
    fr = {
        "spec": tp.SPEC, "kind": tp.FRAME_KIND, "seq": seq,
        "ts": "2026-07-06T00:00:00Z", "twin_id": twin,
        "kernel_version": tp.KERNEL_VERSION, "payload": payload,
        "sha256": payload_sha256(payload), "parent_sha": parent, "sig": None,
    }
    if seed is not None:
        sig = ed25519_sign(seed, fr["sha256"].encode("ascii"))
        fr["sig"] = {"alg": "ed25519", "sig": sig.hex()}
    return fr


def _feed(twin, frames):
    return {"spec": tp.SPEC, "kind": tp.FEED_KIND, "twin_id": twin,
            "head_sha": frames[-1]["sha256"], "count": len(frames),
            "frames": frames}


class TestContract(unittest.TestCase):
    def setUp(self):
        self.agent = TwinPulseAgent()

    def test_extends_basic_agent(self):
        self.assertIsInstance(self.agent, BasicAgent)

    def test_name(self):
        self.assertEqual(self.agent.name, "TwinPulse")

    def test_metadata_fields(self):
        m = self.agent.metadata
        self.assertEqual(m["name"], "TwinPulse")
        self.assertIn("description", m)
        self.assertIn("parameters", m)

    def test_action_enum(self):
        props = self.agent.metadata["parameters"]["properties"]
        self.assertIn("action", props)
        for a in ["subscribe", "assimilate", "status", "echo",
                  "quarantine_list", "selftest"]:
            self.assertIn(a, props["action"]["enum"])

    def test_to_tool_shape(self):
        tool = self.agent.to_tool()
        self.assertEqual(tool["type"], "function")
        self.assertEqual(tool["function"]["name"], "TwinPulse")

    def test_perform_returns_json_string(self):
        out = self.agent.perform(action="echo", twin_id="rappid:@a/b:c",
                                 state_root=tempfile.mkdtemp())
        self.assertIsInstance(out, str)
        self.assertIsInstance(json.loads(out), dict)

    def test_unknown_action(self):
        r = json.loads(self.agent.perform(action="frobnicate"))
        self.assertIn("error", r)


class TestJCS(unittest.TestCase):
    def test_golden_vector_sha(self):
        self.assertEqual(payload_sha256(tp.GOLDEN_INPUT), tp.GOLDEN_SHA256)

    def test_golden_vector_bytes_shape(self):
        # empty key first, sorted keys, no structural whitespace, raw UTF-8.
        b = canonicalize(tp.GOLDEN_INPUT)
        self.assertTrue(b.startswith(b'{"":'))
        self.assertTrue(b.endswith(b'}'))
        # arrays/objects have no insignificant whitespace
        self.assertIn(b'"arr":[1,2,3,-4,0]', b)
        self.assertIn(b'"nested":{"Z":3,"a":1,"b":2}', b)  # 'Z' < 'a' (UTF-16)
        # non-ASCII carried as raw UTF-8, not \u-escaped
        self.assertIn('unicode:\u20ac'.encode('utf-8'), b)
        self.assertIn('\u00e9'.encode('utf-8') + b'":"unicode-key"', b)

    def test_bare_float_rejected(self):
        with self.assertRaises(ValueError):
            canonicalize({"x": 1.5})


class TestEd25519(unittest.TestCase):
    def test_sign_verify_roundtrip(self):
        seed = b"\x01" * 32
        pub = ed25519_publickey(seed)
        msg = b"the pulse"
        sig = ed25519_sign(seed, msg)
        self.assertTrue(ed25519_verify(pub, msg, sig))

    def test_tampered_sig_fails(self):
        seed = b"\x02" * 32
        pub = ed25519_publickey(seed)
        sig = bytearray(ed25519_sign(seed, b"hello"))
        sig[0] ^= 0xFF
        self.assertFalse(ed25519_verify(pub, b"hello", bytes(sig)))

    def test_wrong_msg_fails(self):
        seed = b"\x03" * 32
        pub = ed25519_publickey(seed)
        sig = ed25519_sign(seed, b"hello")
        self.assertFalse(ed25519_verify(pub, b"goodbye", sig))

    def test_verify_frame_sig_absent_is_valid(self):
        fr = _frame("t", 0, None, {"a.json": {"op": "set", "value": {"x": 1}}})
        self.assertTrue(verify_frame_sig(fr, tp.PINNED_PUBKEY_HEX and
                                         bytes.fromhex(tp.PINNED_PUBKEY_HEX)))

    def test_verify_frame_sig_present(self):
        seed = b"\x07" * 32
        pub = ed25519_publickey(seed)
        fr = _frame("t", 0, None, {"a.json": {"op": "set", "value": {"x": 1}}},
                    seed=seed)
        self.assertTrue(verify_frame_sig(fr, pub))
        # wrong key rejects
        self.assertFalse(verify_frame_sig(fr, ed25519_publickey(b"\x08" * 32)))


class TestAssimilation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.twin = "rappid:@test/twin:deadbeef"
        self.pub = bytes.fromhex(tp.PINNED_PUBKEY_HEX)

    def _god(self, tag=""):
        return God(self.twin + tag, state_root=os.path.join(self.tmp, tag or "g"))

    def test_clean_chain_assimilates(self):
        f0 = _frame(self.twin, 0, None,
                    {"card.json": {"op": "set", "value": {"hp": 100}}})
        f1 = _frame(self.twin, 1, f0["sha256"],
                    {"card.json": {"op": "merge", "value": {"atk": 5}}})
        feed = _feed(self.twin, [f0, f1])
        god = self._god("clean")
        res = assimilate_feed(god, feed, "file:///x", self.pub,
                              allow_backfill=False)
        self.assertEqual(res["assimilated"], [0, 1])
        self.assertEqual(res["rejected"], [])
        self.assertTrue(res["in_sync"])
        self.assertEqual(res["head_sha"], feed["head_sha"])
        self.assertEqual(god.load_public_state()["card.json"],
                         {"hp": 100, "atk": 5})

    def test_tampered_frame_rejected_and_quarantined(self):
        f0 = _frame(self.twin, 0, None,
                    {"card.json": {"op": "set", "value": {"hp": 100}}})
        f1 = _frame(self.twin, 1, f0["sha256"],
                    {"card.json": {"op": "set", "value": {"hp": 200}}})
        # tamper f1's payload without fixing sha256
        f1["payload"]["bones"]["card.json"]["value"]["hp"] = 999
        feed = _feed(self.twin, [f0, f1])
        feed["head_sha"] = f1["sha256"]  # stale/declared head
        god = self._god("tamper")
        res = assimilate_feed(god, feed, "file:///x", self.pub,
                              allow_backfill=False)
        self.assertEqual(res["assimilated"], [0])
        self.assertEqual([r["seq"] for r in res["rejected"]], [1])
        self.assertGreaterEqual(len(god.list_quarantine()), 1)
        self.assertTrue(any(e.get("event") == "quarantine"
                            for e in god.recent_events()))
        # head did not advance to the tampered frame
        self.assertEqual(res["head_sha"], f0["sha256"])

    def test_fork_parent_break_rejected(self):
        f0 = _frame(self.twin, 0, None,
                    {"card.json": {"op": "set", "value": {"hp": 1}}})
        f1 = _frame(self.twin, 1, "0" * 64,  # wrong parent -> fork
                    {"card.json": {"op": "set", "value": {"hp": 2}}})
        feed = _feed(self.twin, [f0, f1])
        god = self._god("fork")
        res = assimilate_feed(god, feed, "file:///x", self.pub,
                              allow_backfill=False)
        self.assertEqual(res["assimilated"], [0])
        self.assertEqual([r["seq"] for r in res["rejected"]], [1])
        self.assertTrue(any("fork" in r["reason"] for r in res["rejected"]))

    def test_private_precedence_local_wins(self):
        f0 = _frame(self.twin, 0, None, {
            "card.json": {"op": "set", "value": {"hp": 1}},
            "private/secret.json": {"op": "set", "value": {"leak": "no"}},
        })
        feed = _feed(self.twin, [f0])
        god = self._god("priv")
        res = assimilate_feed(god, feed, "file:///x", self.pub,
                              allow_backfill=False)
        self.assertEqual(res["assimilated"], [0])
        pub = god.load_public_state()
        self.assertIn("card.json", pub)
        self.assertNotIn("private/secret.json", pub)  # DOG cannot write private
        self.assertEqual(res.get("private_precedence"), ["private/secret.json"])

    def test_post_apply_hash_mismatch_rejects_frame(self):
        f0 = _frame(self.twin, 0, None,
                    {"card.json": {"op": "set", "value": {"a": 1}}})
        f1 = _frame(self.twin, 1, f0["sha256"], {
            "card.json": {"op": "merge", "value": {"b": 2},
                          "hash": "deadbeef" * 8}})
        feed = _feed(self.twin, [f0, f1])
        god = self._god("hash")
        res = assimilate_feed(god, feed, "file:///x", self.pub,
                              allow_backfill=False)
        self.assertEqual(res["assimilated"], [0])
        self.assertEqual(len(res["rejected"]), 1)
        self.assertIn("post-apply hash mismatch", res["rejected"][0]["reason"])

    def test_echo_advances_only_on_success(self):
        f0 = _frame(self.twin, 0, None,
                    {"card.json": {"op": "set", "value": {"hp": 100}}})
        feed = _feed(self.twin, [f0])
        god = self._god("echo")
        self.assertIsNone(god.load_echo())
        assimilate_feed(god, feed, "file:///x", self.pub, allow_backfill=False)
        echo = god.load_echo()
        self.assertIsNotNone(echo)
        self.assertEqual(echo["head_sha"], f0["sha256"])

    def test_incremental_advance(self):
        f0 = _frame(self.twin, 0, None, {"c.json": {"op": "set", "value": {"n": 0}}})
        f1 = _frame(self.twin, 1, f0["sha256"], {"c.json": {"op": "set", "value": {"n": 1}}})
        f2 = _frame(self.twin, 2, f1["sha256"], {"c.json": {"op": "set", "value": {"n": 2}}})
        god = self._god("inc")
        r1 = assimilate_feed(god, _feed(self.twin, [f0, f1]), "file:///x",
                             self.pub, allow_backfill=False)
        self.assertEqual(r1["assimilated"], [0, 1])
        # re-pull with a newer head in the window -> only the new frame merges
        r2 = assimilate_feed(god, _feed(self.twin, [f0, f1, f2]), "file:///x",
                             self.pub, allow_backfill=False)
        self.assertEqual(r2["assimilated"], [2])
        self.assertTrue(r2["in_sync"])
        # idempotent re-pull -> nothing new, still in sync
        r3 = assimilate_feed(god, _feed(self.twin, [f0, f1, f2]), "file:///x",
                             self.pub, allow_backfill=False)
        self.assertEqual(r3["assimilated"], [])
        self.assertTrue(r3["in_sync"])

    def test_incremental_window_slid_but_links_off_head(self):
        f0 = _frame(self.twin, 0, None, {"c.json": {"op": "set", "value": {"n": 0}}})
        f1 = _frame(self.twin, 1, f0["sha256"], {"c.json": {"op": "set", "value": {"n": 1}}})
        f2 = _frame(self.twin, 2, f1["sha256"], {"c.json": {"op": "set", "value": {"n": 2}}})
        god = self._god("slid")
        assimilate_feed(god, _feed(self.twin, [f0]), "file:///x", self.pub,
                        allow_backfill=False)
        # window no longer contains f0, but f1 links directly off our head
        r = assimilate_feed(god, _feed(self.twin, [f1, f2]), "file:///x",
                            self.pub, allow_backfill=False)
        self.assertEqual(r["assimilated"], [1, 2])
        self.assertTrue(r["in_sync"])

    def test_real_gap_halts_without_backfill(self):
        f0 = _frame(self.twin, 0, None, {"c.json": {"op": "set", "value": {"n": 0}}})
        f1 = _frame(self.twin, 1, f0["sha256"], {"c.json": {"op": "set", "value": {"n": 1}}})
        f2 = _frame(self.twin, 2, f1["sha256"], {"c.json": {"op": "set", "value": {"n": 2}}})
        god = self._god("gap")
        assimilate_feed(god, _feed(self.twin, [f0]), "file:///x", self.pub,
                        allow_backfill=False)
        # window slid entirely past our head (only f2); f1 missing -> must HALT,
        # never merge across a gap (§3.0 / §4).
        r = assimilate_feed(god, _feed(self.twin, [f2]), "file:///none",
                            self.pub, allow_backfill=False)
        self.assertTrue(r["halted"])
        self.assertEqual(r["assimilated"], [])

    def test_rollback_suspected_logged(self):
        f0 = _frame(self.twin, 0, None, {"c.json": {"op": "set", "value": {"n": 0}}})
        f1 = _frame(self.twin, 1, f0["sha256"], {"c.json": {"op": "set", "value": {"n": 1}}})
        f2 = _frame(self.twin, 2, f1["sha256"], {"c.json": {"op": "set", "value": {"n": 2}}})
        god = self._god("rb")
        assimilate_feed(god, _feed(self.twin, [f0, f1, f2]), "file:///x",
                        self.pub, allow_backfill=False)
        res = assimilate_feed(god, _feed(self.twin, [f0]), "file:///x",
                              self.pub, allow_backfill=False)
        self.assertIn("rollback_suspected", res)


class TestOffline(unittest.TestCase):
    def test_status_offline_serves_echo(self):
        tmp = tempfile.mkdtemp()
        twin = "rappid:@off/twin:1234"
        pub = bytes.fromhex(tp.PINNED_PUBKEY_HEX)
        f0 = _frame(twin, 0, None, {"card.json": {"op": "set", "value": {"hp": 7}}})
        god = God(twin, state_root=tmp)
        assimilate_feed(god, _feed(twin, [f0]), "file:///x", pub,
                        allow_backfill=False)
        agent = TwinPulseAgent()
        out = json.loads(agent.perform(
            action="status", twin_id=twin, state_root=tmp,
            feed_url="https://twin-pulse-unreachable.invalid/feed.json"))
        self.assertTrue(out["ok"])
        self.assertTrue(out["offline"])
        self.assertEqual(out["drift"]["status"], "offline")
        self.assertEqual(out["echo_head"], f0["sha256"])

    def test_assimilate_offline_degrades(self):
        tmp = tempfile.mkdtemp()
        twin = "rappid:@off2/twin:5678"
        agent = TwinPulseAgent()
        out = json.loads(agent.perform(
            action="assimilate", twin_id=twin, state_root=tmp,
            feed_url="https://twin-pulse-unreachable.invalid/feed.json"))
        self.assertTrue(out["ok"])
        self.assertTrue(out["offline"])


class TestSelfTestNetwork(unittest.TestCase):
    """The full network-backed self-test — skipped when offline."""

    def test_run_selftest(self):
        report = tp.run_selftest()
        # offline runs still cover golden + ops; a/b/c need the branch feed.
        net_checks = {c["name"]: c for c in report["checks"]}
        if net_checks["a_full_chain_verify"].get("pass") is False and \
                "offline" in str(net_checks["a_full_chain_verify"]["detail"]).lower():
            self.skipTest("branch feed unreachable — network self-test skipped")
        self.assertTrue(report["ok"], report)


if __name__ == "__main__":
    unittest.main()
