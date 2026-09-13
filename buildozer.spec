[app]
title = Hue Strike
package.name = huestrike
package.domain = org.game
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,wav,mp3,ogg
version = 1.0.0

# python3 என மட்டும் குறிப்பிடவும் (பதிப்பு எண் வேண்டாம்)
requirements = python3,kivy,android

orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/icon.png
android.permissions = INTERNET, VIBRATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

# develop-க்கு பதிலாக master வைக்கவும்
p4a.branch = master
