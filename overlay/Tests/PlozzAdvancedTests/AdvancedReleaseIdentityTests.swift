import XCTest
@testable import CoreModels

final class AdvancedReleaseIdentityTests: XCTestCase {
    func testAdvancedPatchNumberSurvivesResigningWithoutChangingInstallationBuild() {
        for identifier in ["com.thatcube.Plozz.personal-advanced", "com.resigned.Plozz.ABC123"] {
            let identity = AppVersionIdentity(infoDictionary: [
                "CFBundleIdentifier": identifier,
                "CFBundleShortVersionString": "2026.11.16",
                "CFBundleVersion": "6100.1",
                "PlozzPersonalBuild": true,
                "PlozzPersonalUpstreamVersion": "2026.11.16",
                "PlozzPersonalUpstreamBuild": "73.1"
            ])
            XCTAssertEqual(identity.displayVersion, "73.1")
            XCTAssertEqual(identity.displayBuild, "73.1")
            XCTAssertEqual(identity.build, "6100.1")
        }
    }
}
