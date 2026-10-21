#!/bin/bash
# Stop a viewpoint stack and drop its anonymous/named volumes for a fresh run.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "${root}"

profile="${1:-}"
if [ "${profile}" != "blackbox" ] && [ "${profile}" != "whitebox" ]; then
  echo "usage: $0 blackbox|whitebox" >&2
  exit 2
fi

docker compose --profile "${profile}" down --volumes --remove-orphans
if [ "${profile}" = "blackbox" ]; then
  rm -rf "${root}/results/blackbox/run-"* "${root}/workspaces/blackbox/scratch/"*
else
  rm -rf "${root}/results/whitebox/run-"* "${root}/workspaces/whitebox/scratch/"*
fi
mkdir -p "${root}/results/${profile}" "${root}/workspaces/${profile}/scratch"
echo "reset complete for profile ${profile}"
