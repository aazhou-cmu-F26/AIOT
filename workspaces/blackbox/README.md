# Black-box workspace

Use the `blackbox` Compose profile. This directory's `scratch/` folder is the
only extra writable space bind-mounted into the container, besides
`results/blackbox`.

Start a run:

```sh
docker compose --profile blackbox exec blackbox python3 /opt/lab/tools/new_run.py
docker compose --profile blackbox exec -e LAB_RUN_DIR=/workspace/results/run-001 blackbox \
  python3 /opt/lab/tools/coap_client.py send \
    --input /opt/lab/tools/inputs/get_wellknown.hex \
    --output-dir /workspace/results/run-001/outputs \
    --stem smoke
```
