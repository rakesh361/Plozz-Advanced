import AetherEngine
import CoreModels
import FeaturePlayback

/// The only Advanced playback policy; Aether retains source eligibility and fallback.
enum AdvancedPlaybackOptions {
    static func apply(_ settings: AdvancedPlaybackSettings,
                      policy: LiveChannelOutputPolicy, to options: inout LoadOptions) {
        guard !options.isLive, policy.isAudible, !policy.sharesAudioSession else { return }
        if settings.dolbyVisionFEL && !policy.suppressesDisplayMatching {
            options.preferDualLayerDolbyVision = true
            options.dolbyVisionHandling = .automatic
        }
        #if os(tvOS) || os(iOS)
        if #available(tvOS 26.0, iOS 26.0, *), settings.spatialAudio {
            options.objectAudioRendering = .render(speakerLayout(settings.layout))
        }
        #endif
    }

    static func speakerLayout(_ layout: SpatialAudioLayout) -> SpatialSpeakerLayout {
        switch layout {
        case .fiveOneTwo: .l512
        case .fiveOneFour: .l514
        case .sevenOneTwo: .l712
        case .sevenOneFour: .l714
        case .nineOneSix: .l916
        }
    }
}
