"""Configure the generated Capacitor Android test release, without changing iOS."""
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

APP_ID = 'com.yayeverybody.app'
APP_NAME = 'Yay Everybody'
root = Path.cwd()


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise SystemExit(f'Android preparation target missing or ambiguous: {old[:80]}')
    return text.replace(old, new, 1)


if sys.argv[1:] == ['web']:
    config_path = root / 'capacitor.config.json'
    config = json.loads(config_path.read_text())
    config.update(appId=APP_ID, appName=APP_NAME)
    config_path.write_text(json.dumps(config, indent=2) + '\n')

    # The existing server delivers APNs notifications, not Android FCM tokens.
    # Do not register Android tokens with that server or promise working push.
    app_path = root / 'www/app-v3140.js'
    app = app_path.read_text()
    app = replace_once(app, "    if(!cap?.isNativePlatform?.())return null;",
                       "    if(!cap?.isNativePlatform?.()||cap.getPlatform?.()==='android')return null;")
    app = replace_once(app, '  async function ensurePushSubscription(requestPermission=false){',
                       "  async function ensurePushSubscription(requestPermission=false){\n    if(window.Capacitor?.getPlatform?.()==='android')return null; // Android push awaits FCM delivery support.")
    app = replace_once(app, '  async function maybeShowPushPrompt(){',
                       "  async function maybeShowPushPrompt(){\n    if(window.Capacitor?.getPlatform?.()==='android')return; // Android push is not configured yet.")
    app = replace_once(app, '  function notificationSetupCopy(){',
                       "  function notificationSetupCopy(){\n    if(window.Capacitor?.getPlatform?.()==='android')return {copy:'Notifications are not available in this Android test build. Open the app to check for turns.',help:'',action:'CLOSE'};")
    app = replace_once(app, '  async function enableTurnNotifications(){',
                       "  async function enableTurnNotifications(){\n    if(window.Capacitor?.getPlatform?.()==='android'){notifyTurnBox.classList.add('hidden');return;}")
    app_path.write_text(app)

    # Android uses the existing audio and Capacitor Haptics fallback; the custom
    # ScrobbleFeedback plugin is implemented in Swift only.
    feedback_path = root / 'www/scrobble-haptics.js'
    feedback = feedback_path.read_text()
    feedback = replace_once(feedback,
        "    if (!custom) { status.textContent = 'Custom feedback plugin is unavailable in this build.'; return; }",
        "    if (!custom) { soundFallback({kind:'finish',sound:true,gain:30}); status.textContent = 'Test chime requested. Check your media volume.'; return; }")
    feedback_path.write_text(feedback)
    print(f'Android web assets prepared: {APP_NAME} ({APP_ID})')
elif sys.argv[1:] == ['native']:
    gradle_path = root / 'android/app/build.gradle'
    gradle = gradle_path.read_text()
    gradle = replace_once(gradle, '        versionCode 1',
        '        versionCode Integer.parseInt(System.getenv("ANDROID_VERSION_CODE") ?: System.getenv("BUILD_NUMBER") ?: "1")')
    gradle = replace_once(gradle, '        versionName "1.0"', '        versionName "1.0.54"')
    signing = '''    signingConfigs {
        release {
            def keyPath = System.getenv("CM_KEYSTORE_PATH")
            if (keyPath) {
                storeFile file(keyPath)
                storePassword System.getenv("CM_KEYSTORE_PASSWORD")
                keyAlias System.getenv("CM_KEY_ALIAS")
                keyPassword System.getenv("CM_KEY_PASSWORD")
            }
        }
    }
'''
    gradle = replace_once(gradle, '    buildTypes {', signing + '    buildTypes {')
    gradle = replace_once(gradle, '            minifyEnabled false',
                         '            signingConfig signingConfigs.release\n            minifyEnabled false')
    gradle_path.write_text(gradle)

    # Use the existing mascot, including Android adaptive launcher icons.
    res = root / 'android/app/src/main/res'
    icon = root / 'www/icons/scrobble-mascot-v291-512.png'
    (res / 'drawable').mkdir(exist_ok=True)
    shutil.copyfile(icon, res / 'drawable/scrobble_mascot.png')
    for folder in res.glob('mipmap-*'):
        for name in ('ic_launcher', 'ic_launcher_round', 'ic_launcher_foreground'):
            if (folder / f'{name}.png').exists():
                shutil.copyfile(icon, folder / f'{name}.png')
    adaptive = '''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@android:color/white" />
    <foreground android:drawable="@drawable/scrobble_mascot" />
</adaptive-icon>
'''
    for path in res.glob('mipmap-anydpi-v*/ic_launcher*.xml'):
        path.write_text(adaptive)

    manifest_path = root / 'android/app/src/main/AndroidManifest.xml'
    manifest = manifest_path.read_text()
    # Link verification also needs assetlinks.json with the Google Play app
    # signing certificate. Do not publish an upload-key fingerprint in its place.
    links = '''
            <intent-filter android:autoVerify="true">
                <action android:name="android.intent.action.VIEW" />
                <category android:name="android.intent.category.DEFAULT" />
                <category android:name="android.intent.category.BROWSABLE" />
                <data android:scheme="https" android:host="yayeverybody.com" />
                <data android:scheme="https" android:host="www.yayeverybody.com" />
            </intent-filter>
'''
    manifest = replace_once(manifest, '        </activity>', links + '        </activity>')
    ET.fromstring(manifest)
    manifest_path.write_text(manifest)
    print('Android native project configured for signed release bundle')
else:
    raise SystemExit('Usage: prepare-android.py web|native (from scrobble-mobile)')
