#!/usr/bin/env bash
# Publish one video at a public raw URL for Instagram's video_url.
# It goes to the orphan branch "reel-host", which is force-pushed with only
# this file, so old reels drop out of the repo instead of piling up.
# Usage: host_reel.sh FILE  -> prints the URL. Needs GH_TOKEN, GITHUB_REPOSITORY.
set -euo pipefail
src=$1
dir=$(mktemp -d)
cp "$src" "$dir/reel.mp4"
cd "$dir"
git init -q -b reel-host
git add reel.mp4
git -c user.name="github-actions[bot]" -c user.email="41898282+github-actions[bot]@users.noreply.github.com" \
  commit -q -m "Reel for Instagram"
git push -q -f "${REEL_HOST_REMOTE:-https://x-access-token:${GH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git}" reel-host
url="https://raw.githubusercontent.com/${GITHUB_REPOSITORY}/$(git rev-parse HEAD)/reel.mp4"
# raw URLs can take a moment to become reachable after a push
for _ in $(seq 1 12); do
  curl -sfI "$url" >/dev/null 2>&1 && break
  sleep 5
done
echo "$url"
