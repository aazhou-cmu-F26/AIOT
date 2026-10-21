#!/usr/bin/env python3
"""Unit tests for the lab CoAP client, mutator, and run directory helper."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import coap_client  # noqa: E402
import mutate_input  # noqa: E402
import new_run  # noqa: E402


class LoadDatagramTest(unittest.TestCase):
    def test_hex_file_round_trip(self) -> None:
        path = TOOLS / "inputs" / "get_wellknown.hex"
        data = coap_client.load_datagram(path)
        self.assertGreaterEqual(len(data), 4)
        self.assertEqual(data[0] >> 6, 1)
        self.assertEqual(data.hex().upper(), path.read_text().strip())

    def test_binary_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pkt.bin"
            path.write_bytes(b"\x40\x01\x00\x01")
            self.assertEqual(coap_client.load_datagram(path), b"\x40\x01\x00\x01")


class SequenceParserTest(unittest.TestCase):
    def test_smoke_sequence_has_three_steps(self) -> None:
        steps = coap_client.load_sequence(TOOLS / "sequences" / "smoke.yaml")
        self.assertEqual(len(steps), 3)
        self.assertIn("get_wellknown.hex", steps[0]["input"])
        self.assertEqual(steps[1]["delay_ms"], 200)


class MutatorTest(unittest.TestCase):
    def test_seed_is_repeatable(self) -> None:
        original = b"\x40\x01\x00\x01\xff"
        first = mutate_input.mutate(original, seed=7, flips=2, truncate=0, pad=1)
        second = mutate_input.mutate(original, seed=7, flips=2, truncate=0, pad=1)
        self.assertEqual(first, second)
        self.assertEqual(len(first), len(original) + 1)
        self.assertNotEqual(first, original + b"\x00")

    def test_truncate_edge_does_not_go_negative(self) -> None:
        mutated = mutate_input.mutate(b"\x01\x02", seed=1, flips=0, truncate=9, pad=0)
        self.assertEqual(mutated, b"")


class NewRunTest(unittest.TestCase):
    def test_creates_required_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = new_run.next_run_id(root)
            self.assertEqual(run_id, "run-001")
            (root / "run-001").mkdir()
            self.assertEqual(new_run.next_run_id(root), "run-002")


class ObservationSaveTest(unittest.TestCase):
    def test_json_contains_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            payload = b"\x40\x01\x00\x01"
            observation = {
                "timed_out": True,
                "sent_sha256": coap_client.sha256_hex(payload),
                "response_hex": None,
            }
            coap_client.save_observation(out, "attempt", payload, observation)
            saved = json.loads((out / "attempt.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["sent_sha256"], coap_client.sha256_hex(payload))
            self.assertEqual((out / "attempt.input.bin").read_bytes(), payload)


if __name__ == "__main__":
    unittest.main()
