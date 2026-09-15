[app]
accept_sdk_license = True
title = Hue Strike
package.name = huestrike
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,mp3
version = 0.2
requirements = python3,kivy,android
presplash.filename = %(source.dir)s/icon.png
icon.filename = %(source.dir)s/icon.png
orientation = portrait
fullscreen = 1
android.permissions = INTERNET, VIBRATE, MODIFY_AUDIO_SETTINGS
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True
android.allow_backup = True
android.clean_on_build = True
android.archs = arm64-v8a, armeabi-v7a

[buildozer]

log_level = 2
warn_on_root = 1
