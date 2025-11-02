# WebLogic Base Image Automation

This repository automates rebuilding a customized WebLogic Docker image whenever Oracle publishes a new tag for `container-registry.oracle.com/middleware/weblogic`.

## What the pipeline does
- Discovers the latest upstream tag via the Oracle Container Registry API and inspects its digest.
- Caches the most recently processed digest to avoid redundant rebuilds.
- Pulls and smoke-tests the upstream Oracle image.
- Builds the Dockerfile in this repository to apply the custom layer and health check.
- Runs smoke tests against the customized image.
- Pushes the updated image to Docker Hub at `partofaplan/weblogic-base` with both `latest` and the same tag as the upstream Oracle image.

## Required GitHub secrets
Set these repository secrets before enabling the workflow:
- `OCR_USERNAME` and `OCR_PASSWORD`: Oracle Container Registry credentials with access to `middleware/weblogic`.
- `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`: Docker Hub credentials with permission to push to `partofaplan/weblogic-base`.

## Custom layer overview
The `Dockerfile` installs a handful of troubleshooting utilities, adds a health-check script under `/opt/oracle/weblogic/custom/healthcheck.sh`, and enables the script as the container health check. You can extend the layer by editing the Dockerfile or adding more scripts/artefacts under `scripts/`.

## Local validation
```bash
# Build locally from the latest upstream tag
docker login container-registry.oracle.com
export BASE_TAG=$(python3 scripts/get_latest_tag.py | jq -r '.tag')
docker pull "container-registry.oracle.com/middleware/weblogic:${BASE_TAG}"
docker build --build-arg "BASE_IMAGE=container-registry.oracle.com/middleware/weblogic:${BASE_TAG}" -t "weblogic-base:${BASE_TAG}" .

# Smoke test the custom image
scripts/test-custom-image.sh "weblogic-base:${BASE_TAG}"
```

Requirements: Python 3 and `jq` must be installed locally.

## Workflow location
The GitHub Actions definition lives at `.github/workflows/weblogic-base.yml`. Adjust the schedule or testing steps there if your release cadence changes.
