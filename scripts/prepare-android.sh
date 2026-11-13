#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_ROOT="${1:?Provide an empty build directory}"
mkdir -p "$BUILD_ROOT"
BUILD_ROOT="$(cd "$BUILD_ROOT" && pwd)"
if [ -e "$BUILD_ROOT/scrobble-mobile" ]; then
  echo 'Build directory already contains scrobble-mobile; use a fresh directory.' >&2
  exit 1
fi

# Reproduce every current web/game patch, including the approved 1.0.54 sponsors.
python3 "$REPO_ROOT/scripts/prepare-board-tests.py" "$BUILD_ROOT"
cd "$BUILD_ROOT/scrobble-mobile"
npm install --no-audit --no-fund
npm install --no-audit --no-fund @capacitor/app@8.1.2 @capacitor/share@8.0.3 @capacitor/haptics@8.0.2
python3 "$REPO_ROOT/scripts/generate-feedback-audio.py"
python3 "$REPO_ROOT/scripts/prepare-android.py" web
node --check www/app-v3140.js
node --check www/scrobble-haptics.js

for check in verify-move-notice test-weird-modes verify-quad-placement verify-integration verify-regressions verify-friend-invite; do
  node "$REPO_ROOT/scripts/$check.cjs" www
done
node "$REPO_ROOT/scripts/verify-ssa-names.cjs" www/game-engine-v3140.js
node "$REPO_ROOT/scripts/verify-haptics.cjs" www/scrobble-haptics.js
node "$REPO_ROOT/scripts/verify-audio-fallback.cjs" www/scrobble-haptics.js
node "$REPO_ROOT/scripts/verify-score-feedback.cjs" www/game-engine-v3140.js
node "$REPO_ROOT/scripts/verify-rack-drop.cjs" www/game-engine-v3140.js

npx cap add android
python3 "$REPO_ROOT/scripts/prepare-android.py" native
npx cap sync android
test -f android/app/src/main/assets/public/feedback/finish.wav
echo 'Android project and current game checks passed.'
