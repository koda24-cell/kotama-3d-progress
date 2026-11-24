#!/usr/bin/env bash
set -euo pipefail
remote=${1:-origin}
branch=${2:-3d-progress-data}
report=${3:?report required}
for attempt in 1 2 3; do
  echo "publication attempt $attempt/3"
  git fetch "$remote" "$branch"
  git reset --hard FETCH_HEAD
  cp "$report" visual-review.json
  git add visual-review.json
  if git diff --cached --quiet; then exit 0; fi
  git commit -m 'Update advisory visual review'
  if git push "$remote" "HEAD:$branch"; then exit 0; fi
  if [ "$attempt" -lt 3 ]; then sleep "${RETRY_DELAY:-3}"; fi
done
echo 'Publication stopped after three failed pushes' >&2
exit 1
