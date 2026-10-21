# Black-box workspace: protocol tests only. No source, no debugger, no evaluator files.
ARG UBUNTU_DIGEST=sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac
FROM ubuntu@${UBUNTU_DIGEST}

ARG LIBCOAP_COMMIT=7cf7465b784baded4de183290c547d582becfd28
ARG LIBCOAP_TAG=v4.3.5
ENV LIBCOAP_COMMIT=${LIBCOAP_COMMIT}
ENV LIBCOAP_TAG=${LIBCOAP_TAG}
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/opt/lab/tools
ENV HOME=/home/analyst
ENV COAP_HOST=target
ENV COAP_PORT=5683

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-minimal \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /opt/lab /workspace/results /workspace/scratch /home/analyst \
    && chown -R 1000:1000 /opt/lab /workspace /home/analyst

COPY --chown=1000:1000 tools/ /opt/lab/tools/
COPY --chown=1000:1000 config/target.lock /opt/lab/target.lock
COPY --chown=1000:1000 config/protocol.yaml /opt/lab/protocol.yaml
COPY --chown=1000:1000 docs/protocol/ /opt/lab/protocol/
COPY docker/scripts/record_manifest.sh /tmp/record_manifest.sh
RUN chmod +x /tmp/record_manifest.sh \
    && /tmp/record_manifest.sh /opt/lab/environment-manifest.txt \
    && chmod 755 /opt/lab/tools/*.py /opt/lab/tools/*.sh \
    && chown 1000:1000 /opt/lab/environment-manifest.txt

WORKDIR /workspace
USER 1000:1000
CMD ["sleep", "infinity"]
