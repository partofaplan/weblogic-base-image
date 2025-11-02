#!/usr/bin/env python3
"""Select the most recent tag from Oracle Container Registry."""
from __future__ import annotations

import base64
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request

REALM = os.environ.get("OCR_REALM", "https://container-registry.oracle.com/auth")
SERVICE = os.environ.get("OCR_SERVICE", "Oracle Registry")
REGISTRY = os.environ.get("BASE_IMAGE_REGISTRY", "container-registry.oracle.com")
REPOSITORY = os.environ.get("BASE_IMAGE_REPOSITORY")
USERNAME = os.environ.get("OCR_USERNAME")
PASSWORD = os.environ.get("OCR_PASSWORD")


def fail(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)


def require_env(var: str) -> str:
    value = os.environ.get(var)
    if not value:
        fail(f"Environment variable {var} is required")
    return value


REPOSITORY = REPOSITORY or fail("Environment variable BASE_IMAGE_REPOSITORY is required")
USERNAME = require_env("OCR_USERNAME")
PASSWORD = require_env("OCR_PASSWORD")


def request(
    url: str,
    *,
    headers: dict[str, str] | None = None,
) -> tuple[bytes, dict[str, str]]:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read(), dict(resp.headers)


def get_token() -> str:
    params = urllib.parse.urlencode(
        {
            "service": SERVICE,
            "scope": f"repository:{REPOSITORY}:pull",
        }
    )
    url = f"{REALM}?{params}"
    credentials = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode("utf-8")).decode("ascii")
    data, _ = request(url, headers={"Authorization": f"Basic {credentials}"})
    token = json.loads(data.decode("utf-8")).get("token")
    if not token:
        fail("Unable to obtain registry token")
    return token


def with_bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def to_datetime(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return dt.datetime.fromisoformat(value)
    except ValueError:
        return None


def main() -> None:
    token = get_token()

    tags_url = f"https://{REGISTRY}/v2/{REPOSITORY}/tags/list"
    payload, _ = request(tags_url, headers=with_bearer(token))
    tags = json.loads(payload.decode("utf-8")).get("tags") or []
    if not tags:
        fail("No tags returned from Oracle Container Registry")

    latest_tag: str | None = None
    latest_created: dt.datetime | None = None
    latest_digest: str | None = None

    accept_manifest = {
        "Accept": "application/vnd.docker.distribution.manifest.v2+json",
    }

    for tag in tags:
        manifest_url = f"https://{REGISTRY}/v2/{REPOSITORY}/manifests/{urllib.parse.quote(tag)}"
        manifest_bytes, manifest_headers = request(
            manifest_url,
            headers={**with_bearer(token), **accept_manifest},
        )
        manifest = json.loads(manifest_bytes.decode("utf-8"))
        digest = manifest_headers.get("Docker-Content-Digest")
        config_digest = manifest.get("config", {}).get("digest")
        created = None

        if config_digest:
            config_url = f"https://{REGISTRY}/v2/{REPOSITORY}/blobs/{config_digest}"
            config_bytes, _ = request(config_url, headers=with_bearer(token))
            try:
                config = json.loads(config_bytes.decode("utf-8"))
                created = to_datetime(config.get("created"))
            except json.JSONDecodeError:
                created = None

        if should_update(latest_created, latest_tag, created, tag):
            latest_created = created
            latest_digest = digest
            latest_tag = tag

    if not latest_tag or not latest_digest:
        fail("Unable to determine latest tag and digest")

    output = {
        "tag": latest_tag,
        "created": latest_created.isoformat() if latest_created else "",
        "digest": latest_digest,
    }
    print(json.dumps(output))


def should_update(
    best_created: dt.datetime | None,
    best_tag: str | None,
    candidate_created: dt.datetime | None,
    candidate_tag: str,
) -> bool:
    if best_tag is None:
        return True
    if candidate_created and best_created:
        if candidate_created != best_created:
            return candidate_created > best_created
    elif candidate_created or best_created:
        return candidate_created is not None
    return candidate_tag > best_tag


if __name__ == "__main__":
    main()
