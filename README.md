# Plozz Advanced

A small build recipe for Plozz with TrueHD Atmos, DTS:X and dual-layer Dolby
Vision retained. This repository contains automation, patches and build helpers.
It contains no inherited Plozz or personal Git history and no signing credentials.

## How it works

One **Plozz Advanced** workflow checks upstream daily at 07:17 UTC. It downloads
public upstream source into the temporary runner, applies the saved restoration
and app-identity patches, builds an unsigned tvOS IPA, runs scoped simulator tests,
and publishes a release only after those checks pass. Unchanged source and recipe
skip the macOS build. A failed patch or check stops publication and leaves the
previous release available. **Actions → Plozz Advanced → Run workflow** performs
the same check manually.

Each release includes the unsigned IPA, matching patched source snapshot, pinned
package lock, provenance and checksums. The source snapshot excludes Git history.
Public upstream base trees may be fetched temporarily to apply three-way patches;
they are not committed to this repository or included in release snapshots.

## Signing and installation

Sign locally using tvsign. Apple accounts, signing keys, provisioning profiles,
GitHub read tokens and device pairings stay outside this repository. Configure
new-version installation for manual approval. The existing personal app identity
is retained so updates can preserve settings; the official app remains separate.

About follows the upstream release; the separate installation number starts at
6001.1 to remain higher than the existing build. Physical playback and renewal
still require device testing. A passing build does not certify Atmos or FEL output.

GPLv3 and the upstream App Store exception apply; see the included licence files.
Exact dependency sources and notices are provided by the patched source snapshot.
