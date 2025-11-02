#!/usr/bin/env bash
set -euo pipefail

if [ ! -d "/u01/oracle" ]; then
  echo "Oracle home directory missing" >&2
  exit 1
fi

if ! command -v java >/dev/null 2>&1; then
  echo "Java runtime not found" >&2
  exit 1
fi

java -version >/dev/null 2>&1
