# Activate native iPhone notifications

## Delivery repair, October 8, 2026

Both players' iPhones registered successfully, but the live worker returned
`403 InvalidProviderToken` from Apple. Trimming the APNs key and identifier
settings and normalizing escaped PEM newlines resolved the rejection on a
retry: Apple accepted the push (`count: 1`, `failed: 0`). The worker fix is
deployed to `super-worker` version 9; it does not require a new app build.

The worker now records APNs response status/reason without device tokens or
credentials. `BadDeviceToken` preserves the registration because an environment
or configuration mismatch can cause it. Only a 410/Unregistered response removes
an expired registration. Run `node scripts/verify-push-worker.cjs` to check
normalization, rejection reporting, token cleanup, and worker authentication.

Apple accepting a notification does not prove the phone displayed it. Confirm
the alert on the receiving phone, then check notification tap-to-game behavior.

The app and notification service are implemented. Apple credentials and a push-enabled signing profile are required before building 1.0.33.

1. In Apple Developer → Certificates, Identifiers & Profiles → Identifiers, open `com.yayeverybody.scrobble`. Enable **Push Notifications** and save.
2. Create an **Apple Push Notifications service (APNs)** key under Keys. Keep the downloaded `.p8` file private. Record its Key ID and your Apple developer Team ID. An App Store Connect upload key is a different key.
3. In Supabase → Edge Functions → Secrets, set `APNS_PRIVATE_KEY` to the entire `.p8` file contents, `APNS_KEY_ID` to its Key ID, and `APNS_TEAM_ID` to the Team ID. Do not commit the key or paste it into public source files.
4. Refresh or regenerate the App Store provisioning profile for the app in CodeMagic so it includes Push Notifications. Build `fix/clean-app-flow`, version **1.0.33**.
5. Install it through TestFlight, open Account → notifications, and allow notifications. Both players must enable notifications on their devices. Verify a turn alert while the receiving app is closed, open that alert to its game, then try Nudge from the waiting player's Games screen.

Nudge is available only in an active two-player game when it is the opponent's turn. The server allows one successful/queued nudge per sender per game every 12 hours. Disabled notifications and delivery failures are reported honestly; failed deliveries do not consume the cooldown.

Readiness: `https://wvjotzhjfllnttisrywh.supabase.co/functions/v1/super-worker/health` must return `native_push_ready: true` after the Apple secrets are set. That checks configuration only; actual device delivery must still be tested.
