[app]
# (str) Title of your application
 title = Color Switch
# (str) Package name
 package.name = colorswitch
# (str) Package domain (needed for android/ios packaging)
 package.domain = org.colorswitch
# (str) Source code where main.py lives
 source.dir = .
# (str) Main entry point
 source.main = main.py
# (str) Application version
 version = 1.0.0
# (list) Python requirements
 requirements = python3,kivy==2.3.0
# (str) Supported orientation
 orientation = portrait
# (bool) Indicate if the application should be fullscreen or not
 fullscreen = 1
# (str) Android app permissions
 android.permissions = INTERNET
# (int) Target Android API
 android.api = 35
# (int) Minimum Android API
 android.minapi = 23
# (str) Android architecture
 android.archs = arm64-v8a
 android.api = 35
android.minapi = 23
android.archs = arm64-v8a
android.accept_sdk_license = True
# (str) Presplash
 # presplash.filename = %(source.dir)s/data/presplash.png
# (str) Icon
 # icon.filename = %(source.dir)s/data/icon.png

[buildozer]
log_level = 2
warn_on_root = 1


# Android build settings are intentionally kept in [app] above.
