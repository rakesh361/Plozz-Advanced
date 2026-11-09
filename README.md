# Plozz Advanced

Automated tvOS builds of Plozz with TrueHD Atmos, DTS:X and dual-layer
Dolby Vision support retained.

## How it works

One **Plozz Advanced** workflow checks upstream every six hours, at 00:00, 06:00,
12:00 and 18:00 UTC. GitHub may delay scheduled runs during busy periods. It downloads
public upstream source into the temporary runner, enables the optional Aether components and adds device-local Advanced controls,
then applies the version-display patch, builds an unsigned tvOS IPA, runs focused simulator tests,
and publishes a release only after those checks pass. Unchanged source and recipe
skip the macOS build. A failed patch or check stops publication and leaves the
previous release available. **Actions → Plozz Advanced → Run workflow** performs
the same check manually.
Its optional upstream release field can rebuild an existing release for recipe
changes; leave it blank to follow the newest upstream release.

The release checks cover the Advanced components, playback options, device-local
preferences, Advanced panel and version display. The complete Apple TV app must
build, and its dependencies, bundled frameworks, identity and checksums are
verified before publication. Unrelated upstream test suites are not part of this
release gate.

## Advanced playback

Open **Settings → Playback → Advanced** for Spatial audio, Rendering layout and
experimental Dolby Vision FEL. These choices apply only to the current device,
across all profiles, and take effect when playback is restarted. Spatial audio
defaults on; experimental FEL defaults off. Settings are not transferred between
devices with profiles.

Plozz Advanced keeps the AetherEngine revision selected by upstream Plozz. Only
the optional playback components and their runtime controls are enabled; source
eligibility and fallback remain engine-owned. Unexpected integration changes stop
publication and leave the previous release available.

Each release includes the unsigned IPA, matching patched source, dependency
versions and checksums.

Unsigned tvOS IPAs are available from [Releases](https://github.com/rakesh361/Plozz-Advanced/releases).

GPLv3 and the upstream App Store exception apply; see the included licence files.
Exact dependency sources and notices are provided by the patched source snapshot.
