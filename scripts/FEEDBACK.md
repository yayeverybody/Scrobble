# Scrobble feedback — 1.0.39

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

1.0.37 corrects an unsupported explicit mixWithOthers option on the ambient
category (ambient already mixes by default), activates the audio session and
checks whether playback actually starts. Asset/setup failures now produce native
logs and a result instead of disappearing silently. Account includes a Test sound
button with playback/error status; it uses the same finish chime path as scoring.

1.0.38 shortens the score animation from 3 seconds to 2 seconds, so pulses and
tones finish one second sooner together. Core Haptics intensity for score pulses
and the score payoff is multiplied by 0.7; sharpness and other interactions retain
their existing values. The 30% faster pulse cadence remains in place.

1.0.39 synchronizes feedback with actual displayed score increments. Progress for
pitch and intensity comes from the visible points gained rather than elapsed time.
Repeated frames with an unchanged number send no pulses or tones. A 77 ms rate cap
keeps very large scores comfortable. When the rounded score first reaches its
final total, the animation and feedback end together immediately; there is no
silent visual pause followed by a delayed payoff. The cubic easing, two-second
maximum duration and 30% softer score intensity remain.
