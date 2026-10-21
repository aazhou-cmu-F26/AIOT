# Testing

## Normal packet test

```sh
docker compose --profile blackbox up -d --wait
docker compose --profile blackbox exec blackbox \
  python3 /opt/lab/tools/new_run.py
docker compose --profile blackbox exec -e LAB_RUN_DIR=/workspace/results/run-001 blackbox \
  python3 /opt/lab/tools/coap_client.py send \
    --host target --port 5683 \
    --input /opt/lab/tools/inputs/get_wellknown.hex \
    --output-dir /workspace/results/run-001/outputs \
    --stem wellknown
```

Harmless inputs in `/opt/lab/tools/inputs/`:

- `get_wellknown.hex` — CON GET `/.well-known/core`
- `get_time.hex` — CON GET `/time`
- `get_empty.hex` — CON GET with no Uri-Path
- `empty_ack.hex` — empty ACK

Sequence with delays:

```sh
python3 /opt/lab/tools/coap_client.py sequence \
  --manifest /opt/lab/tools/sequences/smoke.yaml \
  --output-dir /workspace/results/run-001/outputs
```

## Replay

```sh
python3 /opt/lab/tools/coap_client.py replay \
  --input /workspace/results/run-001/outputs/wellknown.input.bin \
  --output-dir /workspace/results/run-001/outputs \
  --stem replay
```

Compare `response_sha256` across replays. Each saved input's SHA-256 is also in
the JSON metadata (`sent_sha256`).

## Mutation (network testing, not in-process fuzz)

```sh
python3 /opt/lab/tools/mutate_input.py \
  --input /opt/lab/tools/inputs/get_wellknown.hex \
  --output /workspace/scratch/mut.bin \
  --seed 1 --flips 2 --truncate 0 --pad 0
```

## White-box sanitizer and debugger

```sh
docker compose --profile whitebox exec whitebox /opt/lab/tools/whitebox_tool_check.sh
```

That script rebuilds the approved source with AddressSanitizer into
`/workspace/scratch/wb-build`, loads `coap-server` in GDB, and parses one
**valid** CoAP PDU under ASan.

## Optional libFuzzer

The approved tree ships `tests/oss-fuzz/pdu_parse_udp_target.c`. After an ASan
build:

```sh
export PKG_CONFIG_PATH=/workspace/scratch/wb-build/install/lib/pkgconfig
clang -fsanitize=fuzzer,address \
  "$LIBCOAP_SRC/tests/oss-fuzz/pdu_parse_udp_target.c" \
  $(pkg-config --cflags --libs libcoap-3-notls) \
  -Wl,-rpath,/workspace/scratch/wb-build/install/lib \
  -o /workspace/scratch/wb-build/pdu_parse_udp_fuzzer
/workspace/scratch/wb-build/pdu_parse_udp_fuzzer /opt/lab/tools/inputs -max_total_time=30
```

If `libcoap-3-notls` is missing, try `libcoap-3`. Fuzzer crashes are not
findings until the saved input is replayed independently.

## Evidence collection

`new_run.py` creates:

```text
results/<viewpoint>/run-NNN/
  run.yaml
  notes.md
  commands.log
  findings.md
  verdict.md
  inputs/
  outputs/
```

Keep runtime JSON in `outputs/` separate from interpretation in `notes.md`.
The evaluator appends `verdict.md` on the host.

Host-side automated checks:

```sh
python3 -m unittest discover -s tests -v
./scripts/acceptance.sh
```
