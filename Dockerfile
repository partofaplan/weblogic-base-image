ARG BASE_IMAGE=container-registry.oracle.com/middleware/weblogic:latest
FROM ${BASE_IMAGE}

USER root

RUN microdnf update -y \
    && microdnf install -y zip tar gzip \
    && microdnf clean all

RUN mkdir -p /opt/oracle/weblogic/custom
COPY scripts/healthcheck.sh /opt/oracle/weblogic/custom/healthcheck.sh
RUN chmod +x /opt/oracle/weblogic/custom/healthcheck.sh

ENV CUSTOM_LAYER_VERSION=1

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
  CMD /opt/oracle/weblogic/custom/healthcheck.sh || exit 1

USER oracle
