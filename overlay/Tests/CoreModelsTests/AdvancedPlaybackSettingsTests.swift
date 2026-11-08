import CoreModels
import XCTest

final class AdvancedPlaybackSettingsTests: XCTestCase {
    func testDeviceStoresPersistIndependentlyAndIgnoreProfileFlags() throws {
        let names = ["Advanced.DeviceA.\(UUID())", "Advanced.DeviceB.\(UUID())"]
        let a = try XCTUnwrap(UserDefaults(suiteName: names[0]))
        let b = try XCTUnwrap(UserDefaults(suiteName: names[1]))
        defer { a.removePersistentDomain(forName: names[0]); b.removePersistentDomain(forName: names[1]) }
        let first = AdvancedPlaybackSettingsStore(defaults: a)
        let second = AdvancedPlaybackSettingsStore(defaults: b)
        XCTAssertEqual(first.load(), AdvancedPlaybackSettings())
        first.save(.init(spatialAudio: false, dolbyVisionFEL: true, layout: .sevenOneFour))
        XCTAssertEqual(AdvancedPlaybackSettingsStore(defaults: a).load(),
                       .init(spatialAudio: false, dolbyVisionFEL: true, layout: .sevenOneFour))
        XCTAssertEqual(second.load(), AdvancedPlaybackSettings())
        // Replacing/importing profile settings never writes these device keys.
        let old = Data("{\"trueHDAtmosEnabled\":false,\"dolbyVisionFELEnabled\":true}".utf8)
        let profile = try JSONDecoder().decode(PlaybackSettings.self, from: old)
        let exported = try JSONSerialization.jsonObject(with: JSONEncoder().encode(profile)) as? [String: Any]
        XCTAssertNil(exported?["trueHDAtmosEnabled"])
        XCTAssertNil(exported?["dolbyVisionFELEnabled"])
        XCTAssertEqual(second.load(), AdvancedPlaybackSettings())
        XCTAssertFalse(first.load().spatialAudio)
    }

    func testMalformedDeviceValuesFallBackToSafeDefaults() throws {
        let name = "Advanced.Invalid.\(UUID())"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: name))
        defer { defaults.removePersistentDomain(forName: name) }
        defaults.set("wrong", forKey: AdvancedPlaybackSettingsStore.spatialKey)
        defaults.set("wrong", forKey: AdvancedPlaybackSettingsStore.felKey)
        defaults.set("wrong", forKey: SpatialAudioLayoutStore.storageKey)
        XCTAssertEqual(AdvancedPlaybackSettingsStore(defaults: defaults).load(), AdvancedPlaybackSettings())
    }
}
