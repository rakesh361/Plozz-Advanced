@testable import AetherEngine
import CoreModels
import FeaturePlayback
import XCTest
@testable import EnginePlozzigen

final class AdvancedPlaybackTests: XCTestCase {
    func testAllOptionalComponentsAreActuallyLinked() {
        for component: AetherEngine.OptionalComponent in [
            .trueHDObjectAudio, .dtsxObjectAudio, .dualLayerDolbyVision, .dolbyVisionStillReshaping
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
                            let options = engine.onDemandLoadOptions(for: request)
                            XCTAssertEqual(options.preferDualLayerDolbyVision, fel)
                            XCTAssertEqual(options.dolbyVisionHandling, fel ? .automatic : .profile7BaseLayer)
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

    func testRestrictedOutputsStayDisabled() {
        let enabled = AdvancedPlaybackSettings(spatialAudio: true, dolbyVisionFEL: true)
        for policy in [LiveChannelOutputPolicy(isAudible: false),
                       .init(isAudible: true, sharesAudioSession: true)] {
            let options = PlozzigenVideoEngine.onDemandLoadOptions(advanced: enabled, outputPolicy: policy)
            XCTAssertEqual(options.objectAudioRendering, .off)
            XCTAssertFalse(options.preferDualLayerDolbyVision)
            XCTAssertEqual(options.dolbyVisionHandling, .profile7BaseLayer)
        }
        let preview = PlozzigenVideoEngine.onDemandLoadOptions(
            advanced: enabled, outputPolicy: .init(isAudible: true, suppressesDisplayMatching: true))
        XCTAssertFalse(preview.preferDualLayerDolbyVision)
        for suffix in ["ts", "m3u8"] {
            let live = PlozzigenVideoEngine.liveLoadOptions(
                httpHeaders: [:], url: URL(string: "https://example.invalid/live.\(suffix)")!)
            XCTAssertEqual(live.objectAudioRendering, .off)
            XCTAssertFalse(live.preferDualLayerDolbyVision)
        }
    }

    func testAdvancedPolicyPreservesBufferAndAudioBridgeChoices() {
        for lossless in [false, true] {
            for buffer in PlaybackReadAhead.allCases {
                let options = PlozzigenVideoEngine.onDemandLoadOptions(
                    advanced: .init(spatialAudio: true, dolbyVisionFEL: true),
                    losslessAudioEnabled: lossless, readAhead: buffer)
                XCTAssertEqual(options.audioBridgeMode, lossless ? .lossless : .surroundCompat)
                XCTAssertEqual(options.sessionCacheByteBudget, buffer == .automatic ? nil : Int.max)
                XCTAssertFalse(options.progressiveSegmentDelivery)
            }
        }
    }
}
