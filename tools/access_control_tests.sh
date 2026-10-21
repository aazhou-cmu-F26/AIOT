#!/bin/bash
# Negative checks for the black-box information boundary.
set -u

pass=0
fail=0

record() {
  local status="$1"
  local name="$2"
  local detail="$3"
  printf '%s %s: %s\n' "${status}" "${name}" "${detail}"
  if [ "${status}" = "PASS" ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
  fi
}

absent() {
  local name="$1"
  shift
  local path
  for path in "$@"; do
    if [ -e "${path}" ]; then
      record FAIL "${name}" "found ${path}"
      return
    fi
  done
  record PASS "${name}" "paths not present"
}

absent "no-source-tree" /src /home/analyst/src /home/analyst/src/libcoap /opt/libcoap /usr/local/src/libcoap
absent "no-git-dir" /home/analyst/src/libcoap/.git /opt/lab/.git
absent "no-evaluator" /evaluator /opt/evaluator /opt/lab/evaluator
absent "no-docker-socket" /var/run/docker.sock /run/docker.sock /var/run/docker.sock
absent "no-host-bind" /Users /host /hostfs
absent "no-target-logs" /var/log/target /opt/lab/target-logs /workspace/target-logs

if [ "$(id -u)" -eq 0 ]; then
  record FAIL "non-root" "running as uid 0"
else
  record PASS "non-root" "uid=$(id -u)"
fi

if [ -w /usr/local/bin ] || [ -w /opt/lab/tools/coap_client.py ]; then
  record FAIL "read-only-root" "unexpected writable system path"
else
  record PASS "read-only-root" "system paths are not writable"
fi

python3 - <<'PY'
import socket
import sys

try:
    socket.create_connection(("1.1.1.1", 443), timeout=2)
except OSError:
    sys.exit(0)
sys.exit(1)
PY
if [ "$?" -eq 0 ]; then
  record PASS "no-external-network" "outbound 1.1.1.1:443 failed as expected"
else
  record FAIL "no-external-network" "outbound TCP connection unexpectedly succeeded"
fi

python3 - <<'PY'
import socket
import sys

try:
    socket.getaddrinfo("example.com", 80)
except OSError:
    sys.exit(0)
sys.exit(1)
PY
if [ "$?" -eq 0 ]; then
  record PASS "no-external-dns" "example.com did not resolve"
else
  record FAIL "no-external-dns" "example.com resolved"
fi

if python3 /opt/lab/tools/coap_client.py send \
    --input /opt/lab/tools/inputs/get_wellknown.hex \
    --output-dir /tmp/acl-smoke \
    --stem acl >/tmp/acl-smoke.json 2>/tmp/acl-smoke.err; then
  if grep -q '"timed_out": true' /tmp/acl-smoke.json; then
    record FAIL "target-reachability" "CoAP smoke request timed out"
  else
    record PASS "target-reachability" "CoAP smoke request completed"
  fi
else
  record FAIL "target-reachability" "client exited nonzero"
fi

echo "summary pass=${pass} fail=${fail}"
if [ "${fail}" -ne 0 ]; then
  exit 1
fi
exit 0
