@testable import AetherEngine
import CoreModels
import FeaturePlayback
import XCTest
@testable import EnginePlozzigen

final class AdvancedPlaybackTests: XCTestCase {
    func testAllOptionalComponentsAreActuallyLinked() {
        for component: AetherEngine.OptionalComponent in [
            .trueHDObjectAudio, .dtsxObjectAudio, .dualLayerDolbyVision, .dolbyVisionStillReshaping,
            .dolbyVisionFelCurves
        ] { XCTAssertTrue(component.isBuiltIn) }
    }

    @MainActor
    func testDeviceChoicesReachActualEngineRequests() throws {
        let suite = "Advanced.Engine.\(UUID())"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suite))
        defer { defaults.removePersistentDomain(forName: suite) }
        let store = AdvancedPlaybackSettingsStore(defaults: defaults)
        let engine = try PlozzigenVideoEngine(advancedPlaybackPreference: { store.load() })
        defer { engine.stop() }
        for spatial in [false, true] {
            for fel in [false, true] {
                for layout in SpatialAudioLayout.allCases {
                    store.save(.init(spatialAudio: spatial, dolbyVisionFEL: fel, layout: layout))
                    for provider: ProviderKind in [.plex, .jellyfin, .emby, .silo, .mediaShare] {
                        for url in [URL(string: "https://example.invalid/movie.mkv")!,
                                    URL(fileURLWithPath: "/fixture/download.mkv")] {
                            var request = PlaybackRequest(
                                item: MediaItem(id: "advanced", title: "Fixture", kind: .movie), streamURL: url)
                            request.sourceProvider = provider
                            for conversion in [false, true] {
                                request.dolbyVisionFELConversion = conversion
                                let options = engine.onDemandLoadOptions(for: request)
                                assertFELPolicy(options, conversion: conversion, experimental: fel)
                                if #available(tvOS 26.0, iOS 26.0, *) {
                                    XCTAssertEqual(options.objectAudioRendering,
                                        spatial ? .render(AdvancedPlaybackOptions.speakerLayout(layout)) : .off)
                                }
                                XCTAssertEqual(options.audioBridgeMode, .lossless)
                                XCTAssertFalse(options.isLive)
                            }
                        }
                    }
                }
            }
        }
    }

    private func assertFELPolicy(_ options: LoadOptions, conversion: Bool, experimental: Bool,
                                 file: StaticString = #filePath, line: UInt = #line) {
        XCTAssertEqual(options.preferDualLayerDolbyVision, conversion && experimental, file: file, line: line)
        XCTAssertEqual(options.foldsDolbyVisionFEL, conversion && !experimental, file: file, line: line)
        XCTAssertEqual(options.dolbyVisionHandling,
                       !conversion ? .profile7MELOnly : experimental ? .automatic : .profile7KnownLayers,
                       file: file, line: line)
    }

    @MainActor
    func testConversionChangesOnTheSameRequestSelectBothDirections() throws {
        let engine = try PlozzigenVideoEngine(advancedPlaybackPreference: {
            .init(spatialAudio: false, dolbyVisionFEL: false)
        })
        defer { engine.stop() }
        var request = PlaybackRequest(
            item: MediaItem(id: "conversion", title: "Fixture", kind: .movie),
            streamURL: URL(string: "https://example.invalid/movie.mkv")!)
        for conversion in [true, false, true] {
            request.dolbyVisionFELConversion = conversion
            assertFELPolicy(engine.onDemandLoadOptions(for: request), conversion: conversion, experimental: false)
        }
    }

    @MainActor
    func testConversionExclusionsAlsoPreventExperimentalReconstruction() throws {
        let engine = try PlozzigenVideoEngine(advancedPlaybackPreference: {
            .init(spatialAudio: false, dolbyVisionFEL: true)
        })
        defer { engine.stop() }
        var request = PlaybackRequest(
            item: MediaItem(id: "excluded", title: "Fixture", kind: .movie),
            streamURL: URL(string: "https://example.invalid/movie.mkv")!)
        request.dolbyVisionFELConversion = true
        assertFELPolicy(engine.onDemandLoadOptions(for: request), conversion: true, experimental: true)
        request.externalAudioURL = URL(string: "https://example.invalid/audio.m4a")!
        assertFELPolicy(engine.onDemandLoadOptions(for: request), conversion: false, experimental: true)
        request.externalAudioURL = nil
        request.suppressOrdinaryWatchReporting = true
        assertFELPolicy(engine.onDemandLoadOptions(for: request), conversion: false, experimental: true)
        request.suppressOrdinaryWatchReporting = false
        request.discPlayback = .openMenu
        assertFELPolicy(engine.onDemandLoadOptions(for: request), conversion: false, experimental: true)
    }

    @MainActor
    func testLinkedEngineConvertsKnownFELOnlyWhenEnabledAndPreservesMEL() throws {
        let engine = try AetherEngine()
        defer { engine.stop() }
        for experimental in [false, true] {
            for conversion in [false, true] {
                let options = PlozzigenVideoEngine.onDemandLoadOptions(
                    advanced: .init(spatialAudio: false, dolbyVisionFEL: experimental),
                    dolbyVisionFELConversion: conversion)
                for type in ["FEL", "MEL"] {
                    engine.sourceDolbyVisionEnhancementLayerType = type
                    XCTAssertEqual(engine.resolvedDolbyVisionHandling(
                        options.dolbyVisionHandling, foldsFEL: options.foldsDolbyVisionFEL),
                        conversion || type == "MEL" ? .automatic : .profile7BaseLayer)
                }
            }
        }
        engine.sourceDolbyVisionEnhancementLayerType = nil
        XCTAssertEqual(engine.resolvedDolbyVisionHandling(.profile7KnownLayers, foldsFEL: true), .profile7BaseLayer)
        // The off policy targets Profile 7 only; it is not the global baseLayerOnly policy.
        let off = PlozzigenVideoEngine.onDemandLoadOptions(dolbyVisionFELConversion: false)
        XCTAssertEqual(off.dolbyVisionHandling, .profile7MELOnly)
    }

    func testRestrictedOutputsStayDisabled() {
        let enabled = AdvancedPlaybackSettings(spatialAudio: true, dolbyVisionFEL: true)
        for policy in [LiveChannelOutputPolicy(isAudible: false),
                       .init(isAudible: true, sharesAudioSession: true)] {
            let options = PlozzigenVideoEngine.onDemandLoadOptions(
                advanced: enabled, dolbyVisionFELConversion: true, outputPolicy: policy)
            XCTAssertEqual(options.objectAudioRendering, .off)
            XCTAssertFalse(options.preferDualLayerDolbyVision)
            // Advanced must leave the upstream policy intact for these outputs.
            XCTAssertTrue(options.foldsDolbyVisionFEL)
            XCTAssertEqual(options.dolbyVisionHandling, .profile7KnownLayers)
        }
        let preview = PlozzigenVideoEngine.onDemandLoadOptions(
            advanced: enabled, dolbyVisionFELConversion: true,
            outputPolicy: .init(isAudible: true, suppressesDisplayMatching: true))
        XCTAssertFalse(preview.preferDualLayerDolbyVision)
        XCTAssertTrue(preview.foldsDolbyVisionFEL)
        for suffix in ["ts", "m3u8"] {
            let live = PlozzigenVideoEngine.liveLoadOptions(
                httpHeaders: [:], url: URL(string: "https://example.invalid/live.\(suffix)")!)
            XCTAssertEqual(live.objectAudioRendering, .off)
            XCTAssertFalse(live.preferDualLayerDolbyVision)
            XCTAssertFalse(live.foldsDolbyVisionFEL)
            XCTAssertEqual(live.dolbyVisionHandling, .profile7MELOnly)
        }
    }

    func testAdvancedPolicyPreservesBufferAndAudioBridgeChoices() {
        for lossless in [false, true] {
            for buffer in PlaybackReadAhead.allCases {
                let options = PlozzigenVideoEngine.onDemandLoadOptions(
                    advanced: .init(spatialAudio: true, dolbyVisionFEL: true),
                    losslessAudioEnabled: lossless, dolbyVisionFELConversion: true, readAhead: buffer)
                XCTAssertEqual(options.audioBridgeMode, lossless ? .lossless : .surroundCompat)
                XCTAssertEqual(options.sessionCacheByteBudget, buffer == .automatic ? nil : Int.max)
                XCTAssertFalse(options.progressiveSegmentDelivery)
            }
        }
    }
}
