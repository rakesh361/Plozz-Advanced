#!/usr/bin/env bash
# Reuse upstream's branded generation inputs, with identity independent of branch.
if [[ -z "${DEVELOPER_DIR:-}" && -d /Applications/Xcode.app/Contents/Developer ]]; then
  export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
fi
export PLOZZ_ID_SUFFIX='.personal-advanced'
export PLOZZ_NAME_SUFFIX=' Personal'
export PLOZZ_TV_APP_ENTITLEMENTS='App/Resources/Plozz.branded.entitlements'
export PLOZZ_TV_TOPSHELF_ENTITLEMENTS='TopShelf/TopShelf.branded.entitlements'
export PLOZZ_IOS_APP_ENTITLEMENTS='App/PlozziOS/PlozziOS.branded.entitlements'
export PLOZZ_PAIRING_SERVICE_TYPE='_plozz-personal._tcp'
export PLOZZ_URL_SCHEME='plozz-personal'
export PLOZZ_DEV_FEATURE='Personal advanced'
# Resolve the accepted release, not the newest catalog entry or today's date.
personal_release_identity="$(python3 tools/personal/release_identity.py)" || return
read -r PLOZZ_PERSONAL_UPSTREAM_VERSION PLOZZ_PERSONAL_UPSTREAM_BUILD <<< "$personal_release_identity"
export PLOZZ_PERSONAL_UPSTREAM_VERSION PLOZZ_PERSONAL_UPSTREAM_BUILD
export GIT_CONFIG_PARAMETERS="${GIT_CONFIG_PARAMETERS-'safe.bareRepository=all'}"
