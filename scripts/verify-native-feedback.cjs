const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const root = process.argv[2];
const config = JSON.parse(fs.readFileSync(path.join(root, 'capacitor.config.json'), 'utf8'));
assert.equal(config.packageClassList.filter(x => x === 'ScrobbleFeedbackPlugin').length, 1, 'Custom feedback must be in the native auto-registration manifest exactly once');
const swift = fs.readFileSync(path.join(root, 'AppDelegate.swift'), 'utf8');
assert(swift.includes('@objc(ScrobbleFeedbackPlugin)'));
assert(swift.includes('CAPPlugin, CAPBridgedPlugin'));
assert(swift.includes('jsName = "ScrobbleFeedback"'));
for (const name of ['prepare', 'play', 'cancel']) {
  assert(swift.includes(`CAPPluginMethod(name: "${name}"`));
  assert(swift.includes(`@objc func ${name}(`));
}
assert(swift.includes('didRegisterForRemoteNotificationsWithDeviceToken'));
const storyboard = fs.readFileSync(path.join(root, 'Base.lproj/Main.storyboard'), 'utf8');
assert(storyboard.includes('customClass="CAPBridgeViewController" customModule="Capacitor"'));
assert(!storyboard.includes('ScrobbleViewController'));
for (const note of ['finish', ...Array.from({ length: 12 }, (_, i) => 'note-' + i)]) {
  const file = fs.readFileSync(path.join(root, 'public/feedback', note + '.wav'));
  assert.equal(file.subarray(0, 4).toString(), 'RIFF');
  assert(file.length > 1000);
}
console.log('PASS: custom feedback manifest registration, Objective-C identity, bridged methods, standard storyboard controller, push delegates and all audio assets.');
