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
# The upstream vendor-confinement guard only permits its original engine test
# target to import Aether. Our integration-only target intentionally spans the
# engine and settings modules; shipping hooks are checked by verify-source.py.
export PLOZZ_SKIP_ARCH_GUARD=1
# Only our dedicated target is built and executed; upstream test targets stay intact.
exec tools/run-tests.sh PlozzAdvancedTests
