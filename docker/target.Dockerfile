# Target image: pinned libcoap example server. No source, no compiler.
ARG UBUNTU_DIGEST=sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac
FROM ubuntu@${UBUNTU_DIGEST} AS build

ARG LIBCOAP_COMMIT=7cf7465b784baded4de183290c547d582becfd28
ARG LIBCOAP_TAG=v4.3.5
ENV LIBCOAP_COMMIT=${LIBCOAP_COMMIT}
ENV LIBCOAP_TAG=${LIBCOAP_TAG}
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        autoconf \
        automake \
        build-essential \
        ca-certificates \
        git \
        libtool \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp/src
RUN git init \
    && git remote add origin https://github.com/obgm/libcoap.git \
    && git fetch --depth 1 origin "${LIBCOAP_COMMIT}" \
    && git checkout --detach FETCH_HEAD \
    && ./autogen.sh \
    && ./configure \
        --disable-documentation \
        --disable-doxygen \
        --disable-manpages \
        --disable-dtls \
        --disable-tests \
        --enable-examples \
        --prefix=/usr/local \
    && make -j"$(nproc)" \
    && make install

COPY docker/scripts/record_manifest.sh /tmp/record_manifest.sh
RUN chmod +x /tmp/record_manifest.sh \
    && /tmp/record_manifest.sh /opt/lab/environment-manifest.txt \
    && echo "libcoap_commit=${LIBCOAP_COMMIT}" >> /opt/lab/environment-manifest.txt \
    && echo "libcoap_tag=${LIBCOAP_TAG}" >> /opt/lab/environment-manifest.txt

ARG UBUNTU_DIGEST=sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac
FROM ubuntu@${UBUNTU_DIGEST}

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /opt/lab \
    && chown -R 1000:1000 /opt/lab

COPY --from=build /usr/local /usr/local
COPY --from=build /opt/lab/environment-manifest.txt /opt/lab/environment-manifest.txt
COPY docker/scripts/target_entrypoint.sh /usr/local/bin/target_entrypoint.sh
RUN ldconfig \
    && chmod 755 /usr/local/bin/target_entrypoint.sh \
    && chmod 644 /opt/lab/environment-manifest.txt

ENV PATH="/usr/local/bin:${PATH}"
USER 1000:1000
EXPOSE 5683/udp
ENTRYPOINT ["/usr/local/bin/target_entrypoint.sh"]
