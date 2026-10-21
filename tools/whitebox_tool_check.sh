#!/bin/bash
# Confirm white-box source access plus a real debugger and sanitizer run.
set -euo pipefail

SRC="${LIBCOAP_SRC:-/home/analyst/src/libcoap}"
BUILD="${BUILD_DIR:-/workspace/scratch/wb-build}"
PREFIX="${BUILD}/install"
SMOKE_SRC="/opt/lab/tools/whitebox_asan_smoke.c"

test -f "${SRC}/src/coap_pdu.c"
test -d "${SRC}/.git"
if git -C "${SRC}" cat-file -t 30db3eaa1f0464722ebea2ca2d5084aebfbd344d >/dev/null 2>&1; then
  echo "FAIL later fix commit is present in white-box git objects" >&2
  exit 1
fi
echo "PASS approved source is present and later fix commit is absent"

mkdir -p "${BUILD}"
if [ ! -x "${PREFIX}/bin/coap-server" ]; then
  rm -rf "${BUILD}/libcoap"
  cp -a "${SRC}" "${BUILD}/libcoap"
  cd "${BUILD}/libcoap"
  ./autogen.sh
  ./configure \
    --prefix="${PREFIX}" \
    --disable-documentation \
    --disable-doxygen \
    --disable-manpages \
    --disable-dtls \
    --disable-tests \
    --enable-examples \
    CC=clang \
    CFLAGS="-g -O1 -fsanitize=address" \
    LDFLAGS="-fsanitize=address"
  make -j2
  make install
fi

gdb -batch -nx \
  -ex "file ${PREFIX}/bin/coap-server" \
  -ex "info address main" \
  | tee /tmp/gdb-smoke.txt
grep -q "Symbol \"main\"" /tmp/gdb-smoke.txt
echo "PASS gdb loaded the sanitizer-built coap-server"

export PKG_CONFIG_PATH="${PREFIX}/lib/pkgconfig${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}}"
pkg_mod=""
for candidate in libcoap-3-notls libcoap-3; do
  if pkg-config --exists "${candidate}"; then
    pkg_mod="${candidate}"
    break
  fi
done
if [ -z "${pkg_mod}" ]; then
  echo "FAIL no libcoap pkg-config module in ${PREFIX}" >&2
  exit 1
fi

smoke_bin="${BUILD}/whitebox_asan_smoke"
clang -g -O1 -fsanitize=address \
  "${SMOKE_SRC}" \
  $(pkg-config --cflags "${pkg_mod}") \
  $(pkg-config --libs "${pkg_mod}") \
  -Wl,-rpath,"${PREFIX}/lib" \
  -o "${smoke_bin}"
chmod +x "${smoke_bin}"
ASAN_OPTIONS=detect_leaks=0 "${smoke_bin}"
echo "PASS address-sanitizer smoke parse of a valid CoAP PDU"
