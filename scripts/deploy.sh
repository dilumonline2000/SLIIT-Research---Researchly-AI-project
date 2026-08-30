#!/usr/bin/env bash
# One-command deploy: builds each backend service remotely via ACR Tasks
# (no local Docker needed) and points its Azure Container App at the new image.
#
# Usage:
#   ./scripts/deploy.sh                # deploy all 6 services
#   ./scripts/deploy.sh module1-integrity paper-chat   # deploy only these
#
# Requires: az cli logged in as an account with Contributor on the
# "researchly-rg" resource group (the same account you already use to
# manage these Container Apps).

set -euo pipefail

REGISTRY="researchlyacrit22210524"
RESOURCE_GROUP="researchly-rg"
TAG="$(date +%Y%m%d%H%M%S)-$(git rev-parse --short HEAD)"

declare -A DOCKERFILES=(
  [api-gateway]="docker/Dockerfile.gateway"
  [module1-integrity]="services/module1-integrity/Dockerfile"
  [module2-collaboration]="services/module2-collaboration/Dockerfile"
  [module3-data]="services/module3-data/Dockerfile"
  [module4-analytics]="services/module4-analytics/Dockerfile"
  [paper-chat]="services/paper-chat/Dockerfile"
)

SERVICES=("$@")
if [ ${#SERVICES[@]} -eq 0 ]; then
  SERVICES=(api-gateway module1-integrity module2-collaboration module3-data module4-analytics paper-chat)
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "Deploying tag: $TAG"
echo "Services: ${SERVICES[*]}"
echo

for svc in "${SERVICES[@]}"; do
  dockerfile="${DOCKERFILES[$svc]:-}"
  if [ -z "$dockerfile" ]; then
    echo "!! Unknown service '$svc' — skipping. Known: ${!DOCKERFILES[*]}"
    continue
  fi

  image="${REGISTRY}.azurecr.io/${svc}:${TAG}"
  echo "=== [$svc] building + pushing $image (remote ACR build, no local Docker) ==="
  az acr build \
    --registry "$REGISTRY" \
    --image "${svc}:${TAG}" \
    --file "$dockerfile" \
    .

  echo "=== [$svc] updating Container App to new image ==="
  az containerapp update \
    --name "$svc" \
    --resource-group "$RESOURCE_GROUP" \
    --image "$image" \
    --output table

  echo "=== [$svc] done -> $image ==="
  echo
done

echo "All requested services deployed at tag $TAG."
