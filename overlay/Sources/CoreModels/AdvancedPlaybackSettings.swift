import Foundation

/// Device output choices. Deliberately excluded from profiles and profile transfer.
public struct AdvancedPlaybackSettings: Equatable, Sendable {
    public var spatialAudio: Bool
    public var dolbyVisionFEL: Bool
    public var layout: SpatialAudioLayout

    public init(spatialAudio: Bool = true, dolbyVisionFEL: Bool = false,
                layout: SpatialAudioLayout = .default) {
        self.spatialAudio = spatialAudio
        self.dolbyVisionFEL = dolbyVisionFEL
        self.layout = layout
    }

    public static let disabled = Self(spatialAudio: false, dolbyVisionFEL: false)
}

public struct AdvancedPlaybackSettingsStore {
    public static let spatialKey = "com.plozz.advanced.device.spatialAudio"
    public static let felKey = "com.plozz.advanced.device.dolbyVisionFEL"
    private let defaults: UserDefaults

    public init(defaults: UserDefaults = .standard) { self.defaults = defaults }

    public func load() -> AdvancedPlaybackSettings {
        AdvancedPlaybackSettings(
            spatialAudio: defaults.object(forKey: Self.spatialKey) as? Bool ?? true,
            dolbyVisionFEL: defaults.object(forKey: Self.felKey) as? Bool ?? false,
            layout: SpatialAudioLayoutStore(defaults: defaults).load()
        )
    }

    public func save(_ settings: AdvancedPlaybackSettings) {
        defaults.set(settings.spatialAudio, forKey: Self.spatialKey)
        defaults.set(settings.dolbyVisionFEL, forKey: Self.felKey)
        SpatialAudioLayoutStore(defaults: defaults).save(settings.layout)
    }
}
