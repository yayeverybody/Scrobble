import Capacitor
import CoreHaptics
import AVFoundation
import UIKit

// Kept in AppDelegate's compiled source so generated Xcode projects cannot omit it.
@objc(ScrobbleViewController)
class ScrobbleViewController: CAPBridgeViewController {
    override func capacitorDidLoad() {
        bridge?.registerPluginInstance(ScrobbleFeedbackPlugin())
    }
}

@objc(ScrobbleFeedbackPlugin)
public class ScrobbleFeedbackPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "ScrobbleFeedbackPlugin"
    public let jsName = "ScrobbleFeedback"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "prepare", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "play", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "cancel", returnType: CAPPluginReturnPromise)
    ]
    private var engine: CHHapticEngine?
    private var players: [String: CHHapticPatternPlayer] = [:]
    private var audio: [String: [AVAudioPlayer]] = [:]

    public override func load() {
        NotificationCenter.default.addObserver(self, selector: #selector(stopFeedback), name: UIApplication.willResignActiveNotification, object: nil)
        NotificationCenter.default.addObserver(self, selector: #selector(stopFeedback), name: AVAudioSession.interruptionNotification, object: nil)
    }
    deinit { NotificationCenter.default.removeObserver(self) }
    @objc private func stopFeedback() {
        for player in players.values { try? player.stop(atTime: CHHapticTimeImmediate) }
        players.removeAll()
        for group in audio.values { group.forEach { $0.stop() } }
        audio.removeAll()
    }

    private func readyEngine() throws -> CHHapticEngine? {
        guard CHHapticEngine.capabilitiesForHardware().supportsHaptics else { return nil }
        if engine == nil {
            let e = try CHHapticEngine()
            e.playsHapticsOnly = true
            e.isAutoShutdownEnabled = true
            e.resetHandler = { [weak self] in
                DispatchQueue.main.async { self?.engine = nil; self?.players.removeAll() }
            }
            engine = e
        }
        try engine?.start()
        return engine
    }
    @objc func prepare(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            do {
                let ready = try self.readyEngine() != nil
                call.resolve(["ready": ready])
            }
            catch { call.resolve(["ready": false]) }
        }
    }
    private func event(_ time: Double, _ intensity: Float, _ sharpness: Float) -> CHHapticEvent {
        CHHapticEvent(eventType: .hapticTransient, parameters: [
            CHHapticEventParameter(parameterID: .hapticIntensity, value: intensity),
            CHHapticEventParameter(parameterID: .hapticSharpness, value: sharpness)
        ], relativeTime: time)
    }
    @objc func play(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            guard UIApplication.shared.applicationState == .active else { call.resolve(); return }
            let kind = call.getString("kind") ?? "tap"
            let key = call.getString("key") ?? "ui"
            let p = Float(max(0, min(1, call.getDouble("progress") ?? 0)))
            let gain = max(0, min(200, call.getDouble("gain") ?? 0))
            var events: [CHHapticEvent]
            switch kind {
            case "score": events = [self.event(0, (0.16 + p * 0.55) * 0.7, 0.2 + p * 0.65)]
            case "finish":
                let strength = Float(0.45 + min(gain / 100, 1) * 0.4) * 0.7
                events = [self.event(0, strength * 0.65, 0.45), self.event(0.075, strength * 0.8, 0.65), self.event(0.18, strength, 0.85)]
            case "splashTile": events = [self.event(0, 0.17, 0.55)]
            case "splashStudio": events = [self.event(0, 0.22, 0.35), self.event(0.09, 0.14, 0.5)]
            case "return": events = [self.event(0, 0.22, 0.12)]
            case "tile": events = [self.event(0, 0.32, 0.8)]
            case "error": events = [self.event(0, 0.4, 0.15), self.event(0.12, 0.3, 0.15)]
            case "create": events = [self.event(0, 0.4, 0.4)]
            default: events = [self.event(0, 0.18, 0.5)]
            }
            if call.getBool("haptics") ?? true {
                do {
                    if let engine = try self.readyEngine() {
                        let player = try engine.makePlayer(with: CHHapticPattern(events: events, parameters: []))
                        self.players[key] = player
                        try player.start(atTime: CHHapticTimeImmediate)
                    } else {
                        UIImpactFeedbackGenerator(style: kind == "tap" ? .light : .medium).impactOccurred()
                    }
                } catch { UIImpactFeedbackGenerator(style: .light).impactOccurred() }
            }
            var audioPlayed = false
            var audioError: String?
            if (call.getBool("sound") ?? false) && (kind == "score" || kind == "finish") {
                // Ambient audio respects silent mode, mixes with music, and never claims playback priority.
                do {
                    if AVAudioSession.sharedInstance().category != .ambient {
                        try AVAudioSession.sharedInstance().setCategory(.ambient, mode: .default)
                    }
                    try AVAudioSession.sharedInstance().setActive(true)
                    let note = kind == "finish" ? "finish" : "note-\(max(0, min(11, Int(p * 11))))"
                    if let url = Bundle.main.url(forResource: note, withExtension: "wav", subdirectory: "public/feedback") {
                        let player = try AVAudioPlayer(contentsOf: url)
                        player.volume = kind == "finish" ? 0.55 : 0.25 + p * 0.2
                        var live = (self.audio[key] ?? []).filter { $0.isPlaying }
                        live.append(player)
                        self.audio[key] = Array(live.suffix(4))
                        player.prepareToPlay()
                        audioPlayed = player.play()
                        if !audioPlayed { audioError = "Audio player could not start." }
                    } else { audioError = "Scoring sound asset missing: " + note }
                } catch { audioError = error.localizedDescription }
                if let error = audioError { NSLog("Scrobble scoring audio: %@", error) }
            }
            var result: [String: Any] = ["audioPlayed": audioPlayed]
            if let error = audioError { result["audioError"] = error }
            call.resolve(result)
        }
    }
    @objc func cancel(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            let key = call.getString("key") ?? "ui"
            if key == "*" { self.stopFeedback(); call.resolve(); return }
            try? self.players.removeValue(forKey: key)?.stop(atTime: CHHapticTimeImmediate)
            self.audio.removeValue(forKey: key)?.forEach { $0.stop() }
            call.resolve()
        }
    }
}
