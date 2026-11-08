import CoreModels
import XCTest
@testable import FeatureSettings

@MainActor
final class AdvancedPlaybackControlsTests: XCTestCase {
    func testDeviceControlsAreInAdvancedWithoutChangingExternalPlayerRows() {
        XCTAssertEqual(AdvancedPlaybackControls.rows.map(\.id), ["advanced-aether-playback"])
        XCTAssertEqual(PlaybackAdvancedSettingsView.rows().map(\.id),
                       ["external-player", "advanced-aether-playback"])
        XCTAssertEqual(ExternalPlayerSettingsRows.advanced().map(\.id), ["external-player"])
    }
}
