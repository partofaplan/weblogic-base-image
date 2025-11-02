#!/usr/bin/env bash
set -euo pipefail

IMAGE_REF="${1:-}"

if [ -z "$IMAGE_REF" ]; then
  echo "Usage: $0 <image-ref>" >&2
  exit 1
fi

docker run --rm "$IMAGE_REF" /bin/bash -lc "/opt/oracle/weblogic/custom/healthcheck.sh"
