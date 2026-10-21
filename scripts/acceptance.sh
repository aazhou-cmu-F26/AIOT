#!/bin/bash
# Execute AC-01 through AC-07. Do not mark PASS unless the command ran.
set -u

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "${root}"
evidence="${root}/results/acceptance"
mkdir -p "${evidence}"
checklist="${root}/docs/ACCEPTANCE_CHECKLIST.md"
status_file="${evidence}/summary.txt"
: > "${status_file}"

pass_count=0
fail_count=0
blocked_count=0

record() {
  local id="$1"
  local status="$2"
  local command="$3"
  local notes="$4"
  printf '%s %s\ncommand: %s\nnotes: %s\n\n' "${id}" "${status}" "${command}" "${notes}" \
    | tee -a "${status_file}"
  case "${status}" in
    PASS) pass_count=$((pass_count + 1)) ;;
    FAIL) fail_count=$((fail_count + 1)) ;;
    BLOCKED) blocked_count=$((blocked_count + 1)) ;;
  esac
}

docker_ready() {
  docker info >/dev/null 2>&1
}

if ! docker_ready; then
  cat > "${checklist}" <<'EOF'
# Acceptance Checklist

Docker Engine was not reachable when this file was generated. AC-01 through
AC-07 are BLOCKED until `docker info` succeeds. AC-08 remains PENDING.

See `results/acceptance/summary.txt`.
EOF
  record AC-01 BLOCKED "docker info" "Docker daemon is not running"
  record AC-02 BLOCKED "n/a" "blocked by AC-01"
  record AC-03 BLOCKED "n/a" "blocked by AC-01"
  record AC-04 BLOCKED "n/a" "blocked by AC-01"
  record AC-05 BLOCKED "n/a" "blocked by AC-01"
  record AC-06 BLOCKED "n/a" "blocked by AC-01"
  record AC-07 BLOCKED "n/a" "blocked by AC-01"
  record AC-08 PENDING "teammate README replay" "must not be self-certified"
  exit 1
fi

ac01_cmd='docker compose --profile blackbox build --no-cache && docker compose --profile whitebox build'
if docker compose --profile blackbox build --no-cache \
    > "${evidence}/ac01-blackbox-build.log" 2>&1 \
  && docker compose --profile whitebox build \
    > "${evidence}/ac01-whitebox-build.log" 2>&1; then
  record AC-01 PASS "${ac01_cmd}" "See results/acceptance/ac01-*-build.log"
else
  record AC-01 FAIL "${ac01_cmd}" "See results/acceptance/ac01-*-build.log"
fi

start_blackbox() {
  docker compose --profile blackbox up -d --wait --wait-timeout 120
}

stop_all() {
  docker compose --profile blackbox down --volumes --remove-orphans >/dev/null 2>&1 || true
  docker compose --profile whitebox down --volumes --remove-orphans >/dev/null 2>&1 || true
}

if [ "${fail_count}" -eq 0 ]; then
  if start_blackbox > "${evidence}/ac02-up.log" 2>&1; then
    if docker compose --profile blackbox exec -T blackbox \
        python3 /opt/lab/tools/coap_client.py send \
          --input /opt/lab/tools/inputs/get_wellknown.hex \
          --output-dir /workspace/results/acceptance-smoke \
          --stem wellknown \
        > "${evidence}/ac02-send.json" 2> "${evidence}/ac02-send.err"; then
      if grep -q '"timed_out": false' "${evidence}/ac02-send.json" \
        && grep -q '"response_len":' "${evidence}/ac02-send.json"; then
        record AC-02 PASS "coap_client.py send get_wellknown.hex" \
          "target answered a valid CoAP GET; evidence ac02-send.json"
      else
        record AC-02 FAIL "coap_client.py send get_wellknown.hex" \
          "no usable CoAP response; see ac02-send.json"
      fi
    else
      record AC-02 FAIL "coap_client.py send get_wellknown.hex" \
        "client failed; see ac02-send.err"
    fi
  else
    record AC-02 FAIL "docker compose --profile blackbox up -d --wait" \
      "stack failed to become healthy; see ac02-up.log"
  fi
else
  record AC-02 BLOCKED "n/a" "blocked by AC-01"
fi

if docker compose --profile blackbox exec -T blackbox true >/dev/null 2>&1; then
  if docker compose --profile blackbox exec -T blackbox \
      /opt/lab/tools/access_control_tests.sh \
      > "${evidence}/ac03-ac04-access.log" 2>&1; then
    record AC-03 PASS "access_control_tests.sh" \
      "black-box cannot see source/internal logs; can send packets"
    record AC-04 PASS "access_control_tests.sh" \
      "no docker.sock, no evaluator files, no external network"
  else
    record AC-03 FAIL "access_control_tests.sh" "see ac03-ac04-access.log"
    record AC-04 FAIL "access_control_tests.sh" "see ac03-ac04-access.log"
  fi
else
  record AC-03 BLOCKED "access_control_tests.sh" "blackbox service is not running"
  record AC-04 BLOCKED "access_control_tests.sh" "blackbox service is not running"
fi

if docker compose --profile blackbox exec -T blackbox true >/dev/null 2>&1; then
  docker compose --profile blackbox exec -T blackbox \
    python3 /opt/lab/tools/new_run.py --results-root /workspace/results \
    > "${evidence}/ac07-run-path.txt" 2> "${evidence}/ac07-run.err"
  run_dir="$(tr -d '\r' < "${evidence}/ac07-run-path.txt" | tail -n 1)"
  if docker compose --profile blackbox exec -T blackbox \
      env LAB_RUN_DIR="${run_dir}" \
      python3 /opt/lab/tools/coap_client.py replay \
        --input /opt/lab/tools/inputs/get_wellknown.hex \
        --output-dir "${run_dir}/outputs" \
        --stem replay1 \
      > "${evidence}/ac06-replay1.json" 2> "${evidence}/ac06-replay1.err" \
    && docker compose --profile blackbox exec -T blackbox \
      env LAB_RUN_DIR="${run_dir}" \
      python3 /opt/lab/tools/coap_client.py replay \
        --input /opt/lab/tools/inputs/get_wellknown.hex \
        --output-dir "${run_dir}/outputs" \
        --stem replay2 \
      > "${evidence}/ac06-replay2.json" 2> "${evidence}/ac06-replay2.err"; then
    hash1="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["response_sha256"])' \
      "${evidence}/ac06-replay1.json")"
    hash2="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["response_sha256"])' \
      "${evidence}/ac06-replay2.json")"
    if [ -n "${hash1}" ] && [ "${hash1}" = "${hash2}" ] && [ "${hash1}" != "None" ]; then
      record AC-06 PASS "coap_client.py replay twice" \
        "repeatable response sha256=${hash1}"
    else
      record AC-06 FAIL "coap_client.py replay twice" \
        "response hashes differ or missing"
    fi
    if [ -f "${root}/results/blackbox/$(basename "${run_dir}")/run.yaml" ] \
      && [ -f "${root}/results/blackbox/$(basename "${run_dir}")/commands.log" ]; then
      record AC-07 PASS "new_run.py + commands.log" \
        "run.yaml, commands.log, inputs/outputs exist under results/blackbox"
    else
      record AC-07 FAIL "new_run.py + commands.log" \
        "expected run artifacts were not on the host bind mount"
    fi
  else
    record AC-06 FAIL "coap_client.py replay" "see ac06-replay*.err"
    record AC-07 FAIL "new_run.py" "see ac07-run.err"
  fi
else
  record AC-06 BLOCKED "replay" "blackbox service is not running"
  record AC-07 BLOCKED "new_run.py" "blackbox service is not running"
fi

stop_all
if docker compose --profile whitebox up -d --wait --wait-timeout 120 \
    > "${evidence}/ac05-up.log" 2>&1; then
  if docker compose --profile whitebox exec -T whitebox \
      /opt/lab/tools/whitebox_tool_check.sh \
      > "${evidence}/ac05-whitebox.log" 2>&1; then
    record AC-05 PASS "whitebox_tool_check.sh" \
      "source present; gdb and ASan valid-PDU smoke passed"
  else
    record AC-05 FAIL "whitebox_tool_check.sh" "see ac05-whitebox.log"
  fi
else
  record AC-05 FAIL "docker compose --profile whitebox up -d --wait" \
    "see ac05-up.log"
fi
stop_all

record AC-08 PENDING "independent teammate follows README" \
  "must remain PENDING until another person actually runs the lab"

{
  echo "# Acceptance Checklist"
  echo
  echo "Generated by \`scripts/acceptance.sh\`."
  echo
  echo '```'
  cat "${status_file}"
  echo '```'
} > "${checklist}"

echo "PASS=${pass_count} FAIL=${fail_count} BLOCKED=${blocked_count}"
if [ "${fail_count}" -ne 0 ] || [ "${blocked_count}" -ne 0 ]; then
  exit 1
fi
exit 0
