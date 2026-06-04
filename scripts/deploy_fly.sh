#!/usr/bin/env bash
# Deploy Chronos API to Fly.io
# Run once: bash scripts/deploy_fly.sh
# Subsequent: git push main (GitHub Actions handles it)
set -e

export PATH="/home/ws/udyyk/.fly/bin:$PATH"

echo "==> Logging in to Fly.io"
flyctl auth login

echo "==> Creating app (skip if exists)"
flyctl apps create chronos-app --org personal 2>/dev/null || true

echo "==> Setting secrets"
flyctl secrets set \
  GROQ_API_KEY="$GROQ_API_KEY" \
  GEE_PROJECT="907232950083" \
  --app chronos-app

echo "==> Deploying"
flyctl deploy --app chronos-app --remote-only

echo "==> Done. App URL: https://chronos-app.fly.dev"
