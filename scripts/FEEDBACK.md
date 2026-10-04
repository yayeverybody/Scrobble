# Scrobble feedback — 1.0.36

The custom Capacitor plugin uses Core Haptics transients with distinct intensity,
sharpness and spacing. Tile placement gets a crisp click, rack return a soft tap,
and rejected moves a gentle double pulse. The score animation drives pulses from
200 ms down toward 73 ms apart (30% faster pulse cadence), with increasing intensity/sharpness; completion
gets a three-pulse payoff whose strength scales with the points gained.

Twelve original pentatonic bell tones rise with the animation and end with a short
three-note chime. Python generates the PCM assets during packaging. AVAudioPlayer
uses the ambient audio category to respect silent mode and mix with other music.
Ordinary button presses have haptics only. Account contains separate, persistent
Scoring sounds and Haptic feedback switches, enabled by default.

Native custom-plugin errors fall back to the existing Capacitor haptic presets.
Web runs remain safe and silent. Backgrounding, audio interruptions, leaving a
game and disabling feedback stop active feedback. Loading a score without an
increase, decreases and cancelled animations do not produce a score celebration.

The native plugin and bridge controller are appended to AppDelegate's compiled
source. The storyboard selects that controller; no generated Xcode project source
list edits are needed. Push notification delegates remain intact. Packaging checks
fail if registration, storyboard selection or sound assets are missing.

Validation: JS behavior tests cover throttling, score completion/cancellation,
settings, fallback, and actual tile drops; packaging is checked against the
Capacitor 8 template. Full Swift compilation requires the macOS Codemagic build.
Physical iPhone validation still required: feel, volume, silent switch, music
mixing, background interruptions and both settings across a relaunch.

The accepted 1.0.34 (174) baseline remains on baseline/1.0.34-build-174.
