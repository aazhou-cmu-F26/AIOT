#!/bin/bash
# Start the frozen CoAP/UDP example server.
set -euo pipefail

LISTEN_ADDR="${LISTEN_ADDR:-0.0.0.0}"
LISTEN_PORT="${LISTEN_PORT:-5683}"

server_bin="/usr/local/bin/coap-server"
if [ ! -x "${server_bin}" ]; then
  server_bin="/usr/local/bin/coap-server-notls"
fi

exec "${server_bin}" \
  -A "${LISTEN_ADDR}" \
  -p "${LISTEN_PORT}" \
  -P, \
  -v 3
