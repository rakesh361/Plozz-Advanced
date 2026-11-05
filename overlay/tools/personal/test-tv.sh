#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source tools/personal/environment.sh
# Cold SwiftUI compilation can exceed the upstream three-minute silence limit.
# Keep a bounded ten-minute watchdog; test verdicts and the job timeout still apply.
export PLOZZ_HANG_SECS="${PLOZZ_HANG_SECS:-600}"
mkdir -p .build/personal
export PLOZZ_LOG_DIR="${PLOZZ_LOG_DIR:-$PWD/.build/personal/simulator-logs}"
if [[ -z "${PLOZZ_SIM_ID:-}" ]]; then
  sdk="$(xcrun --sdk appletvsimulator --show-sdk-version)"
  PLOZZ_SIM_ID="$(python3 tools/select-ci-tvos-simulator.py --sdk-version "$sdk")"
  export PLOZZ_SIM_ID
fi
exec tools/run-tests.sh CoreModelsTests EnginePlozzigenTests FeaturePlaybackTests FeatureSettingsTests
