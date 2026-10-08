from pathlib import Path

# Clean V12 popper test: replace the app web root with a standalone known-good test page.
# This intentionally avoids the Scrobble/Popper Lab wrapper so Capacitor has no layout influence.
popper_html = Path('../scripts/popper-v12.html').read_text()
popper_js = Path('../scripts/popper-v12.js').read_text()
Path('www/index.html').write_text(popper_html)
Path('www/popper-v12.js').write_text(popper_js)


# V13 native iOS sound + haptic bridge. Both effects are generated natively so
# TestFlight does not depend on WKWebView WebAudio or JS plugin registration.
vc = Path('ios/App/App/ViewController.swift')
vc.write_text(r'''import UIKit
import Capacitor
import WebKit
import AVFoundation
import AudioToolbox

class ViewController: CAPBridgeViewController, WKScriptMessageHandler {
    private let feedback = UIImpactFeedbackGenerator(style: .heavy)
    private let audioEngine = AVAudioEngine()
    private let player = AVAudioPlayerNode()

    private var popperBridgeInstalled = false

    override func viewDidLoad() {
        super.viewDidLoad()
        installPopperBridge()
        feedback.prepare()
        audioEngine.attach(player)
        let format = AVAudioFormat(standardFormatWithSampleRate: 44100, channels: 1)!
        audioEngine.connect(player, to: audioEngine.mainMixerNode, format: format)
        try? AVAudioSession.sharedInstance().setCategory(.ambient, mode: .default, options: [.mixWithOthers])
        try? AVAudioSession.sharedInstance().setActive(true)
        try? audioEngine.start()
    }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        installPopperBridge()
    }

    private func installPopperBridge() {
        guard !popperBridgeInstalled, let webView = bridge?.webView else { return }
        webView.configuration.userContentController.removeScriptMessageHandler(forName: "popperFX")
        webView.configuration.userContentController.add(self, name: "popperFX")
        popperBridgeInstalled = true
        print("POPPER_FX_BRIDGE_INSTALLED")
    }

    deinit {
        if popperBridgeInstalled {
            bridge?.webView?.configuration.userContentController.removeScriptMessageHandler(forName: "popperFX")
            bridge?.webView?.configuration.userContentController.removeScriptMessageHandler(forName: "popperHaptic")
        }
    }

    private func playMechanical(_ release: Bool) {
        let sr: Double = 44100
        let duration = release ? 0.095 : 0.14
        let frames = AVAudioFrameCount(sr * duration)
        let format = AVAudioFormat(standardFormatWithSampleRate: sr, channels: 1)!
        guard let buffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: frames),
              let data = buffer.floatChannelData?[0] else { return }
        buffer.frameLength = frames
        for i in 0..<Int(frames) {
            let t = Double(i) / sr
            let env = Float(max(0, 1.0 - t / duration))
            if release {
                let body = sin(2 * Double.pi * (330.0 - 170.0 * t / duration) * t)
                let crack = (Double.random(in: -1...1)) * exp(-t * 48.0)
                data[i] = Float(body * 0.42 + crack * 0.58) * env * 0.72
            } else {
                let f = 96.0 - 36.0 * t / duration
                data[i] = Float(sin(2 * Double.pi * f * t)) * env * 0.48
            }
        }
        player.scheduleBuffer(buffer, at: nil, options: .interrupts, completionHandler: nil)
        if !player.isPlaying { player.play() }
    }

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard let stage = message.body as? String else { return }
        if message.name == "popperHaptic" {
            DispatchQueue.main.async {
                self.feedback.prepare()
                self.feedback.impactOccurred(intensity: stage == "HEAVY" ? 1.0 : 0.55)
            }
            return
        }
        guard message.name == "popperFX" else { return }
        print("POPPER_FX_RECEIVED:\(stage)")
        DispatchQueue.main.async {
            let release = stage == "release"
            self.feedback.prepare()
            self.feedback.impactOccurred(intensity: release ? 1.0 : 0.65)
            AudioServicesPlaySystemSoundWithCompletion(release ? 1520 : 1519, nil)
            self.playMechanical(release)
        }
    }
}
''')

# Compile the custom controller and make it the storyboard entry point.
project = Path('ios/App/App.xcodeproj/project.pbxproj')
pbx = project.read_text()
if '/* ViewController.swift */' not in pbx:
    edits = {
        '/* Begin PBXBuildFile section */': '/* Begin PBXBuildFile section */\n\t\tA1B2C3D4E5F6071829304051 /* ViewController.swift in Sources */ = {isa = PBXBuildFile; fileRef = A1B2C3D4E5F6071829304050 /* ViewController.swift */; };',
        '/* Begin PBXFileReference section */': '/* Begin PBXFileReference section */\n\t\tA1B2C3D4E5F6071829304050 /* ViewController.swift */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = ViewController.swift; sourceTree = "<group>"; };',
        '\t\t\t\t504EC3071FED79650016851F /* AppDelegate.swift */,': '\t\t\t\t504EC3071FED79650016851F /* AppDelegate.swift */,\n\t\t\t\tA1B2C3D4E5F6071829304050 /* ViewController.swift */,',
        '\t\t\t\t504EC3081FED79650016851F /* AppDelegate.swift in Sources */,': '\t\t\t\t504EC3081FED79650016851F /* AppDelegate.swift in Sources */,\n\t\t\t\tA1B2C3D4E5F6071829304051 /* ViewController.swift in Sources */,',
    }
    for old, new in edits.items():
        if old not in pbx:
            raise SystemExit('Native controller project insertion target not found: ' + old)
        pbx = pbx.replace(old, new, 1)
    project.write_text(pbx)

storyboard = Path('ios/App/App/Base.lproj/Main.storyboard')
sb = storyboard.read_text()
old = 'customClass="CAPBridgeViewController" customModule="Capacitor"'
new = 'customClass="ViewController" customModule="App" customModuleProvider="target"'
if old in sb:
    sb = sb.replace(old, new, 1)
elif new not in sb:
    raise SystemExit('Native controller storyboard target not found')
storyboard.write_text(sb)
