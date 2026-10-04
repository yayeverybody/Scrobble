from pathlib import Path

p=Path('ios/App/App/AppDelegate.swift')
s=p.read_text()
if 'didRegisterForRemoteNotificationsWithDeviceToken' not in s:
    callbacks='''
    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        NotificationCenter.default.post(name: .capacitorDidRegisterForRemoteNotifications, object: deviceToken)
    }
    func application(_ application: UIApplication, didFailToRegisterForRemoteNotificationsWithError error: Error) {
        NotificationCenter.default.post(name: .capacitorDidFailToRegisterForRemoteNotifications, object: error)
    }
'''
    end=s.rfind('}')
    if end<0: raise SystemExit('AppDelegate class ending not found')
    s=s[:end]+callbacks+s[end:]
    p.write_text(s)
