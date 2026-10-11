from pathlib import Path
import json
import xml.etree.ElementTree as ET

app = Path('ios/App/App/AppDelegate.swift')
marker = '// SCROBBLE_CUSTOM_FEEDBACK'
s = app.read_text().split(marker)[0].rstrip()
app.write_text(s + '\n\n' + marker + '\n' + Path(__file__).with_name('ScrobbleFeedback.swift').read_text())

# CapacitorBridge.registerPlugins resolves these @objc class names before loading
# the webview, and exports their methods into Capacitor.Plugins at document start.
config = Path('ios/App/App/capacitor.config.json')
data = json.loads(config.read_text())
classes = data.setdefault('packageClassList', [])
if 'ScrobbleFeedbackPlugin' not in classes:
    classes.append('ScrobbleFeedbackPlugin')
config.write_text(json.dumps(data, indent=2) + '\n')

# Use the standard bridge controller; registration no longer depends on a custom
# storyboard subclass being instantiated.
story = Path('ios/App/App/Base.lproj/Main.storyboard')
s = story.read_text().replace('customClass="ScrobbleViewController" customModule="App" customModuleProvider="target"', 'customClass="CAPBridgeViewController" customModule="Capacitor"')
assert 'customClass="CAPBridgeViewController"' in s, 'Capacitor storyboard controller missing'
ET.fromstring(s)
story.write_text(s)
