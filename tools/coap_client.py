#!/usr/bin/env python3
"""Minimal CoAP/UDP datagram client for Stage 1 investigation.

The client sends raw datagrams from files, records replies or timeouts, and
can replay the same bytes. It does not implement a CoAP stack.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence


DEFAULT_HOST = os.environ.get("COAP_HOST", "target")
DEFAULT_PORT = int(os.environ.get("COAP_PORT", "5683"))
DEFAULT_TIMEOUT_S = 2.0


def sha256_hex(data: bytes) -> str:
    """Return the SHA-256 hex digest of *data*."""
    return hashlib.sha256(data).hexdigest()


def load_datagram(path: Path) -> bytes:
    """Load a datagram from a binary or hex text file.

    Args:
        path: Path to a ``.hex`` file of hex digits or a raw binary file.

    Returns:
        The datagram bytes.

    Raises:
        ValueError: If a hex file is empty or not valid hexadecimal.
    """
    raw = path.read_bytes()
    if path.suffix.lower() == ".hex":
        hex_text = "".join(
            line.split("#", 1)[0] for line in raw.decode("ascii").splitlines()
        )
        hex_text = "".join(hex_text.split())
        if not hex_text:
            raise ValueError(f"hex file is empty: {path}")
        return bytes.fromhex(hex_text)
    return raw


def write_bytes(path: Path, data: bytes) -> None:
    """Write *data* to *path*, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def send_datagram(
    host: str,
    port: int,
    payload: bytes,
    timeout_s: float,
) -> dict[str, Any]:
    """Send one UDP datagram and wait for a single reply or timeout.

    Args:
        host: Target hostname or IP.
        port: Target UDP port.
        payload: Exact datagram to send.
        timeout_s: Socket timeout in seconds.

    Returns:
        Observation dictionary with timing, hashes, and reply bytes if any.
    """
    started = time.time()
    observation: dict[str, Any] = {
        "host": host,
        "port": port,
        "timeout_s": timeout_s,
        "sent_len": len(payload),
        "sent_sha256": sha256_hex(payload),
        "timed_out": False,
        "error": None,
        "response_hex": None,
        "response_len": 0,
        "response_sha256": None,
        "elapsed_ms": None,
        "peer": None,
    }
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.settimeout(timeout_s)
        sock.sendto(payload, (host, port))
        try:
            data, peer = sock.recvfrom(2048)
        except socket.timeout:
            observation["timed_out"] = True
        else:
            observation["response_hex"] = data.hex()
            observation["response_len"] = len(data)
            observation["response_sha256"] = sha256_hex(data)
            observation["peer"] = f"{peer[0]}:{peer[1]}"
    except OSError as exc:
        observation["error"] = str(exc)
    finally:
        sock.close()
        observation["elapsed_ms"] = round((time.time() - started) * 1000.0, 3)
        observation["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return observation


def load_sequence(path: Path) -> list[dict[str, Any]]:
    """Load a tiny YAML-ish sequence file without an extra dependency.

    Each step requires ``input:`` and may include ``timeout_s`` and
    ``delay_ms``. This parser understands only the subset used by the lab.
    """
    steps: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip() or line.strip() == "steps:":
            continue
        stripped = line.strip()
        if stripped.startswith("- "):
            if current:
                steps.append(current)
            current = {}
            stripped = stripped[2:].strip()
            if stripped:
                key, value = _split_kv(stripped)
                current[key] = value
            continue
        if current is None:
            continue
        key, value = _split_kv(stripped)
        current[key] = value
    if current:
        steps.append(current)
    if not steps:
        raise ValueError(f"no steps found in {path}")
    return steps


def _split_kv(item: str) -> tuple[str, Any]:
    if ":" not in item:
        raise ValueError(f"invalid sequence line: {item}")
    key, value = item.split(":", 1)
    text = value.strip().strip('"').strip("'")
    if key.strip() in {"timeout_s"}:
        return key.strip(), float(text)
    if key.strip() in {"delay_ms"}:
        return key.strip(), int(text)
    return key.strip(), text


def run_sequence(
    host: str,
    port: int,
    sequence_path: Path,
    output_dir: Path,
) -> list[dict[str, Any]]:
    """Send a sequence of datagrams with configurable delays and timeouts."""
    steps = load_sequence(sequence_path)
    results: list[dict[str, Any]] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for index, step in enumerate(steps, start=1):
        delay_ms = int(step.get("delay_ms", 0))
        if delay_ms:
            time.sleep(delay_ms / 1000.0)
        input_path = Path(str(step["input"]))
        payload = load_datagram(input_path)
        timeout_s = float(step.get("timeout_s", DEFAULT_TIMEOUT_S))
        observation = send_datagram(host, port, payload, timeout_s)
        observation["step"] = index
        observation["input_path"] = str(input_path)
        write_bytes(output_dir / f"step-{index:02d}.input.bin", payload)
        if observation.get("response_hex"):
            write_bytes(
                output_dir / f"step-{index:02d}.response.bin",
                bytes.fromhex(observation["response_hex"]),
            )
        (output_dir / f"step-{index:02d}.json").write_text(
            json.dumps(observation, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        results.append(observation)
    return results


def append_command_log(run_dir: Path | None, argv: Sequence[str]) -> None:
    """Append the current command to an investigation commands.log if present."""
    if run_dir is None:
        return
    log_path = run_dir / "commands.log"
    line = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "argv": list(argv),
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(line) + "\n")


def save_observation(
    output_dir: Path,
    stem: str,
    payload: bytes,
    observation: Mapping[str, Any],
) -> None:
    """Save input bytes, optional reply bytes, and JSON metadata."""
    write_bytes(output_dir / f"{stem}.input.bin", payload)
    if observation.get("response_hex"):
        write_bytes(
            output_dir / f"{stem}.response.bin",
            bytes.fromhex(str(observation["response_hex"])),
        )
    (output_dir / f"{stem}.json").write_text(
        json.dumps(dict(observation), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Send and replay raw CoAP/UDP datagrams."
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    parser.add_argument(
        "--run-dir",
        default=os.environ.get("LAB_RUN_DIR"),
        help="Optional investigation run directory for commands.log",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    send_cmd = sub.add_parser("send", help="Send one datagram from a file")
    send_cmd.add_argument("--input", required=True, type=Path)
    send_cmd.add_argument("--output-dir", required=True, type=Path)
    send_cmd.add_argument("--stem", default="attempt")

    replay_cmd = sub.add_parser("replay", help="Replay a previously saved input")
    replay_cmd.add_argument("--input", required=True, type=Path)
    replay_cmd.add_argument("--output-dir", required=True, type=Path)
    replay_cmd.add_argument("--stem", default="replay")

    seq_cmd = sub.add_parser("sequence", help="Send a small packet sequence")
    seq_cmd.add_argument("--manifest", required=True, type=Path)
    seq_cmd.add_argument("--output-dir", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point.

    Returns:
        Process exit status. 0 on a completed send/replay, 2 on local errors.
        A target timeout is a recorded observation, not a local error.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    run_dir = Path(args.run_dir) if args.run_dir else None
    append_command_log(run_dir, sys.argv if argv is None else argv)

    try:
        if args.command in {"send", "replay"}:
            payload = load_datagram(args.input)
            observation = send_datagram(
                args.host, args.port, payload, args.timeout
            )
            save_observation(args.output_dir, args.stem, payload, observation)
            json.dump(observation, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
            if observation.get("error"):
                return 1
            return 0
        results = run_sequence(
            args.host, args.port, args.manifest, args.output_dir
        )
        json.dump(results, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        if any(item.get("error") for item in results):
            return 1
        return 0
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
