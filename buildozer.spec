[app]
title = Hue Strike
package.name = huestrike
package.domain = org.game
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,wav,mp3,ogg
version = 1.0.0
requirements = python3,kivy,android
orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/icon.png
android.permissions = INTERNET, VIBRATE
android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
