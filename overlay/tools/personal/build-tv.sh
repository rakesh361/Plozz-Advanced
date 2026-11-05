#!/usr/bin/env bash
# Unsigned device build only. Never installs, signs in, or changes device pairing.
set -euo pipefail
cd "$(dirname "$0")/../.."
source tools/personal/environment.sh
build_root="$PWD/.build/personal"
mkdir -p "$build_root"
output="$(mktemp -d "$build_root/build-XXXXXXXX")"
main() {
echo "Build evidence: $output"
python3 tools/personal/verify-source.py
xcodebuild -version
if ! xcodebuild -version | head -n1 | grep -Eq '^Xcode 27\.'; then
  echo 'This baseline requires full Xcode 27 with the tvOS SDK.' >&2
  exit 1
fi
xcrun --sdk appletvos --show-sdk-version
xcrun --sdk appletvos metal --version
if [[ "$(xcodegen --version)" != *'2.46.0'* ]]; then
  echo 'Use XcodeGen 2.46.0 for this build recipe.' >&2
  exit 1
fi
source tools/lib/apple-build-lease.sh
acquire_apple_build_shared_lease 'plozz/personal-build'
install_apple_build_lease_traps
# XcodeGen rewrites the tracked platform plists. Preserve exact input bytes,
# including any local edits; leave the generated project ignored as upstream does.
cp App/Resources/Info.plist "$output/tvos-original.plist"
cp App/PlozziOS/Info.plist "$output/ios-original.plist"
export PLOZZ_PERSONAL_SOURCE_DIRTY
PLOZZ_PERSONAL_SOURCE_DIRTY="$(git status --porcelain)"
# shellcheck disable=SC2329 # Invoked by the EXIT trap.
cleanup_personal_build() {
  local status=$?
  trap - EXIT HUP INT TERM
  cp "$output/tvos-original.plist" App/Resources/Info.plist || status=1
  cp "$output/ios-original.plist" App/PlozziOS/Info.plist || status=1
  if [[ "${APPLE_BUILD_LEASE_SIGNALLED:-0}" == 1 || "$status" -ne 0 ]]; then
    abandon_apple_build_lease
  elif ! release_apple_build_lease; then
    status=75
  fi
  exit "$status"
}
trap cleanup_personal_build EXIT
tools/generate-project.sh
source tools/lib/swift-package-storage.sh
configure_plozz_package_resolution "$output/packages"
xcodebuild build -hideShellScriptEnvironment -project Plozz.xcodeproj -scheme Plozz \
  -configuration Debug -destination 'generic/platform=tvOS' \
  -derivedDataPath "$output/DerivedData" "${PACKAGE_RESOLUTION_ARGS[@]}" \
  ARCHS=arm64 ONLY_ACTIVE_ARCH=YES SWIFT_OPTIMIZATION_LEVEL=-O \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO DEVELOPMENT_TEAM='' \
  COMPILER_INDEX_STORE_ENABLE=NO
cmp Package.resolved Plozz.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved
app="$output/DerivedData/Build/Products/Debug-appletvos/Plozz.app"
python3 tools/personal/package-tv.py "$app" "$output"
echo "Unsigned IPA ready for local signing: $output/Plozz-Personal-tvOS.ipa"
}
( main ) 2>&1 | tee "$output/build.log"
