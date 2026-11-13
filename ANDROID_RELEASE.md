# Yay Everybody Android test release

Source: current `fix/current-scrobble-board` game, version 1.0.54.
Android application ID: `com.yayeverybody.app`, matching the Google Play listing
created during setup. iOS keeps `com.yayeverybody.scrobble`.

## First build

1. In Codemagic, upload the Android **upload keystore** under Team settings →
   codemagic.yaml settings → Code signing identities → Android keystores. Use
   reference `yay_everybody_android`. Keep a secure backup of this key and its
   passwords. Never commit them. If no upload key exists, create one first.
2. Select branch `android/google-play`, workflow **Yay Everybody Android Release**.
3. Start the build. Download `Yay-Everybody-Android.aab` from its artifacts.
4. Upload that file to the existing Google Play internal testing draft.
   Complete Play App Signing enrollment and release notes there, then review
   before distributing to testers. This workflow does not publish to Google Play.

Codemagic supplies Java 21, Node 22, Android SDK and the four `CM_KEY*` signing
variables through the keystore reference. The build fails if signing is missing;
it never substitutes a debug key. The Codemagic build number becomes Android's
version code; it must increase for each upload. `ANDROID_VERSION_CODE` can
override it when necessary.

## Scope and checks

The build reuses the existing game patches, Supabase connection, account flow,
sharing, native Haptics, and WAV sound fallback. It runs the current game
regression checks before producing a signed release bundle.

- Android push notifications are **not available in this first test build**.
  The existing notification server uses Apple's APNs; Android needs Firebase
  configuration plus FCM delivery/token support. The test build suppresses
  automatic permission prompts and explains this in notification settings.
- HTTPS invite handling is configured, but automatic Android App Links need
  `/.well-known/assetlinks.json` on both domains with the **Google Play app
  signing certificate** fingerprint. Obtain that after Play App Signing setup.
  The upload certificate is not the app signing certificate.
- An actual device test is still required for sign-in, computer/friend games,
  tile dragging, sharing, camera/photo selection, safe areas, audio and haptics.
  JavaScript checks and Capacitor sync do not replace an Android device test.

Local preparation only (Node 22+, Python 3):

```sh
bash scripts/prepare-android.sh /absolute/path/to/fresh-build-directory
```

To compile locally, also install Java 21 and Android SDK 36, provide the signing
variables, and run `./gradlew bundleRelease` inside the generated `android` folder.
