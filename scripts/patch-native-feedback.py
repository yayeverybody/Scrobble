from pathlib import Path
import xml.etree.ElementTree as ET

app = Path('ios/App/App/AppDelegate.swift')
marker = '// SCROBBLE_CUSTOM_FEEDBACK'
s = app.read_text().split(marker)[0].rstrip()
app.write_text(s + '\n\n' + marker + '\n' + Path(__file__).with_name('ScrobbleFeedback.swift').read_text())
story = Path('ios/App/App/Base.lproj/Main.storyboard')
s = story.read_text()
s = s.replace('customClass="CAPBridgeViewController" customModule="Capacitor"', 'customClass="ScrobbleViewController" customModule="App" customModuleProvider="target"')
assert 'customClass="ScrobbleViewController"' in s, 'Capacitor storyboard controller missing'
ET.fromstring(s)
story.write_text(s)
