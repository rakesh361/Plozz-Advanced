# Plozz Advanced

Automated tvOS builds of Plozz with TrueHD Atmos, DTS:X and dual-layer
Dolby Vision support retained.

## How it works

One **Plozz Advanced** workflow checks upstream daily at 07:17 UTC. It downloads
public upstream source into the temporary runner, applies the saved restoration
and app-identity patches, builds an unsigned tvOS IPA, runs scoped simulator tests,
and publishes a release only after those checks pass. Unchanged source and recipe
skip the macOS build. A failed patch or check stops publication and leaves the
previous release available. **Actions → Plozz Advanced → Run workflow** performs
the same check manually.

Each release includes the unsigned IPA, matching patched source, dependency
versions and checksums.

Unsigned tvOS IPAs are available from [Releases](https://github.com/rakesh361/Plozz-Advanced/releases).

GPLv3 and the upstream App Store exception apply; see the included licence files.
Exact dependency sources and notices are provided by the patched source snapshot.
