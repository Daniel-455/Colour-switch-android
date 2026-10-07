[app]
title = Hue Strike
package.name = huestrike
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.exclude_dirs = .github,bin,.buildozer
version = 0.3
requirements = hostpython3==3.10.10,python3==3.10.10,kivy==2.3.0,pyjnius,android
presplash.filename = %(source.dir)s/icon.png
icon.filename = %(source.dir)s/icon.png
orientation = portrait
fullscreen = 1
android.permissions = VIBRATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True
android.allow_backup = True
android.archs = arm64-v8a
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
