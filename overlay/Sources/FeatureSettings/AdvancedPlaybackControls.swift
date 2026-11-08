import CoreModels
import CoreUI
import SwiftUI

struct AdvancedPlaybackControls: View {
    @AppStorage(AdvancedPlaybackSettingsStore.spatialKey) private var spatialAudio = true
    @AppStorage(AdvancedPlaybackSettingsStore.felKey) private var fel = false
    @AppStorage(SpatialAudioLayoutStore.storageKey) private var layout = SpatialAudioLayout.default

    var body: some View {
        SettingsControlRows {
            Text("These settings apply only to this device, across all profiles. Restart playback after making changes.")
                .settingsHelperText().fixedSize(horizontal: false, vertical: true)
            if #available(tvOS 26.0, iOS 26.0, *) {
                Toggle("Spatial audio (height channel support)", isOn: $spatialAudio)
                    .accessibilityIdentifier("advanced-spatial-audio")
                Text("Uses PCM for supported TrueHD Atmos and DTS:X tracks; lossy audio over AirPlay.")
                    .settingsHelperText().fixedSize(horizontal: false, vertical: true)
                SettingsMenuRow(title: "Rendering layout", value: Text(verbatim: layout.rawValue)) {
                    Picker("Rendering layout", selection: $layout) {
                        ForEach(SpatialAudioLayout.allCases, id: \.self) { option in
                            Text(verbatim: option.rawValue).tag(option)
                        }
                    }
                }
                .accessibilityIdentifier("advanced-spatial-layout")
                Text("DTS:X heights require 7.1.4 or 9.1.6. Used when Spatial audio is on.")
                    .settingsHelperText().fixedSize(horizontal: false, vertical: true)
            }
            Toggle("Dolby Vision FEL (experimental)", isOn: $fel)
                .accessibilityIdentifier("advanced-dolby-vision-fel")
            Text("May impact performance. Applies to supported Profile 7 videos.")
                .settingsHelperText().fixedSize(horizontal: false, vertical: true)
        }
    }

    static var rows: [SettingsSplitRow] {
        [SettingsSplitRow(id: "advanced-aether-playback", title: "Advanced playback") {
            AdvancedPlaybackControls()
        }]
    }
}
