# Release 073: FEL conversion and experimental reconstruction

Investigated 17 November 2026. The feasibility review below records the pre-change findings.

Implementation follow-up: the user authorized implementation and publication as 073.1. The proposed policy is now implemented, with focused regression coverage for both toggles, request exclusions, linked engine handling, profile/device independence and version identity. Local recipe tests (26), prepared-source preservation/version tests (14), source guards and workflow lint passed. The prepared source retains the exact 073 engine and dependency lock. Full build, simulator checks and publication are recorded by the release workflow; physical Apple TV playback has not been performed in this task.

## Finding

The requested four combinations are feasible with the engine already pinned by Advanced 073. No engine upgrade, decoder replacement or new conversion implementation is needed. The defect is in our policy overlay: it always clears the official approximation flag, and enables experimental reconstruction independently of the official conversion choice.

For confirmed Profile 7 FEL, supported on-demand playback and a suitable Dolby Vision output:

| Official conversion | Advanced experimental | Current Advanced 073 request | Proposed request |
| --- | --- | --- | --- |
| On | On | Experimental reconstruction | Experimental reconstruction |
| On | Off | HDR10 | Official brightness approximation |
| Off | On | Experimental reconstruction | HDR10 |
| Off | Off | HDR10 | HDR10 |

These are requested playback methods, not unconditional guarantees of the displayed output. Engine eligibility, source parsing and display capability still apply.

## Sources inspected

The published [Advanced 073 release](https://github.com/rakesh361/Plozz-Advanced/releases/tag/advanced/build-43906239516) identifies upstream Plozz `e57ddfb3a84d07f0539fb1c4216711915ce0f422` and recipe `16e7f4c7b26d89c9610d40131d880facc540de4a`. Its engine is `055860a0accaaafa1852d1a65c4f7f505cb7e6ab`. Remote release metadata and the relevant immutable source files were checked; this review did not inspect or run the released IPA.

- [Official load-option selection](https://github.com/brandomoore/Plozz/blob/e57ddfb3a84d07f0539fb1c4216711915ce0f422/Sources/EnginePlozzigen/PlozzigenVideoEngine.swift): eligible conversion sets `foldsDolbyVisionFEL = true`, `dolbyVisionHandling = .profile7KnownLayers`, and leaves `preferDualLayerDolbyVision = false`. Off uses `.profile7MELOnly` and disables folding.
- [Advanced override](https://github.com/rakesh361/Plozz-Advanced/blob/16e7f4c7b26d89c9610d40131d880facc540de4a/overlay/Sources/EnginePlozzigen/AdvancedPlaybackOptions.swift): unconditionally clears folding, then selects `.automatic` plus dual-layer preference if experimental is on.
- [Engine source inspection](https://github.com/brandomoore/AetherEngine/blob/055860a0accaaafa1852d1a65c4f7f505cb7e6ab/Sources/AetherEngine/AetherEngine.swift): selective known-layer handling without folding is downgraded to MEL-only. Selective handling also explicitly clears dual-layer preference.
- [Selective resolver](https://github.com/brandomoore/AetherEngine/blob/055860a0accaaafa1852d1a65c4f7f505cb7e6ab/Sources/AetherEngine/Decoder/VideoRoutingPolicy.swift): known FEL is accepted only when folding and its compiled component are enabled; MEL remains accepted with conversion off.
- [Official FEL documentation](https://github.com/brandomoore/Plozz/blob/e57ddfb3a84d07f0539fb1c4216711915ce0f422/docs/playback-engines.md#dolby-vision-fel): the approximation adjusts per-scene brightness, without restoring local detail, grain or full enhancement-layer precision.

This explains the reported HDR result in option 2 directly from the code.

## Smallest proposed change

Keep official 073's options intact unless experimental reconstruction is both selected and permitted by the official conversion decision. In `AdvancedPlaybackOptions.apply`, replace the unconditional folding override and existing experimental condition with:

```swift
if options.foldsDolbyVisionFEL && settings.dolbyVisionFEL && !policy.suppressesDisplayMatching {
    options.foldsDolbyVisionFEL = false
    options.preferDualLayerDolbyVision = true
    options.dolbyVisionHandling = .automatic
}
```

Retain the existing live/audible/shared-session guards and spatial-audio code. The pre-override folding flag currently carries the official, already-filtered conversion eligibility. Alternatively, pass the resolved `convertsFEL` Boolean explicitly into this helper to make the dependency more obvious.

Both flag changes inside the branch matter. Keeping selective handling would make the engine clear experimental preference; retaining folding could introduce unwanted processing on native fallback. Experimental mode should keep its existing full-reconstruction configuration.

The current manifest already inherits `DolbyVisionFelCurves` from upstream and enables `DualLayerDolbyVision` through the recipe. Keep the pinned engine. Extend required-component checks to include the curves component so its accidental removal cannot silently disable approximation in a future build.

## Compatibility details and remaining decisions

1. The table concerns FEL. Conversion off should preserve ordinary MEL conversion and supported single-layer DV. It must not become a global Dolby Vision off switch.
2. Official conversion is per profile, defaults on, and has a temporary in-player override. Advanced experimental is per device, across profiles. The effective profile/session conversion choice should be the master permission; experimental chooses the method only when permission is on.
3. Preview, separate-audio and interactive disc-menu exclusions are already applied before the helper. Respecting the official decision also stops experimental mode bypassing those exclusions. Preserve live/output-policy restrictions.
4. Official conversion is gated to debug/TestFlight builds. Our packaged build uses Debug with optimization, so it passes this gate. Any future move to a Release configuration needs an explicit review of this assumption.
5. The official in-player switch requires `engine.sourceDolbyVisionEnhancementLayerType == "FEL"`. In this engine revision that property is assigned by the selective inspection path. Experimental `.automatic` skips that path and probes FEL separately, without populating this property. Consequently the in-player switch can disappear in experimental mode. Settings-based selection is feasible without an engine change; preserving a visible switch through experimental transitions needs separate work and tests. Do not relax the UI guard to advertise conversion on unknown sources.
6. Experimental reconstruction can be refused by source/device constraints. Its existing native fallback is not automatically the new approximation. Treat "experimental preferred, approximation if unavailable" as a separate fallback policy; it is not one of the four toggle combinations and is not required for the reported use case.
7. Approximation can add startup and seek latency, and requires a suitable delivered stream and output route to show DV. Native remote-HLS bypass, external players and server-transcoded output are outside this local conversion guarantee.

Update Advanced helper text to explain that experimental reconstruction requires P7 FEL conversion on. The official description currently promises approximation whenever conversion is on; qualify that description in Advanced when experimental is selected.

## Validation and release scope

An isolated Swift policy probe is saved under ignored `work/fel-073-investigation/policy-probe.swift`. All 20 assertions passed using `swift -D DolbyVisionFelCurves -module-cache-path /private/tmp/plozz-fel-073-module-cache work/fel-073-investigation/policy-probe.swift`. It uses the current overlay, a proposed copy, and the pinned engine's selective resolver with lightweight substitute types. It checks the current and proposed four-case matrix, mutually exclusive methods, MEL/unknown handling with conversion off, and existing output/live guards. It does not link Aether or exercise decoders, output, app lifecycle or playback.

Before a release:

- Extend the dedicated Advanced simulator suite to exercise both toggles through real `PlaybackRequest` construction across existing providers and local/network sources. Existing tests leave the new request flag false and currently expect experimental to bypass it, so those assertions must change.
- Cover profile/session choices, exclusions, linked curves availability, and ordinary DV/MEL preservation. Retain buffer/audio regression checks.
- Verify both in-player override directions on the approximation path. Document or address its experimental-path availability separately.
- Build the complete tvOS app and run the focused release gates. Confirm all four choices on an Apple TV with a known FEL sample, restarting playback after settings changes; check seek/resume and diagnostics as well as the display's DV indicator.

Recommendation from the investigation: proceed with the small policy change and focused coverage. There is no source-level reason these methods need to conflict when selected exclusively. Actual display output and performance still need physical-device validation. The investigation itself did not change production playback code; the separately authorized implementation is described above.
