#!/usr/bin/env bash
set -euo pipefail
if [ "$COLLECTION_RESULT" != success ]; then git restore -- index.json renders/; git clean -fd -- renders/; fi
if [ -z "$(git status --porcelain -- index.json renders/ collection-status.json)" ]; then echo "No new verified assets."; exit 0; fi
git config user.name github-actions[bot]
git config user.email 41898282+github-actions[bot]@users.noreply.github.com
git add index.json renders/ collection-status.json
git commit -m "Collect verified Kotama 3D artifact checkpoints"
for attempt in 1 2 3; do
  if git push origin HEAD:3d-progress-data; then exit 0; fi
  if [ "$attempt" = 3 ]; then exit 1; fi
  sleep "$((attempt * 2))"
  cp collection-status.json ../collection-status-retry.json
  git fetch origin 3d-progress-data
  git reset --hard FETCH_HEAD
  cp ../collection-status-retry.json collection-status.json
  if [ "$COLLECTION_RESULT" = success ]; then
    python3 ../collector/tools/3d-progress/ingest_artifacts.py . ../incoming
  fi
  git add index.json renders/ collection-status.json
  if git diff --cached --quiet; then exit 0; fi
  git commit -m "Retry verified gallery collection"
done
