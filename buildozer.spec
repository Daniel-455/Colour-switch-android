[app]

# (str) Title of your application
title = Hue Strike

# (str) Package name
package.name = huestrike

# (str) Package domain (needed for android/ios packaging)
package.domain = org.game

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (break by comma)
source.include_exts = py,png,jpg,kv,atlas,json,wav,mp3,ogg

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
# python3==3.10.12 என குறிப்பிடப்பட்டுள்ளதால் Python 3.14 பிழை வராது
requirements = python3==3.10.12,kivy,android

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (str) Icon of the application
icon.filename = %(source.dir)s/icon.png

# (str) Supported platforms
# (list) Permissions
android.permissions = INTERNET, VIBRATE

# (int) Target Android API
android.api = 33

# (int) Minimum API required
android.minapi = 21

# (str) NDK version to use
android.ndk = 25b

# (list) The Android archs to build for
android.archs = arm64-v8a

# (bool) Accept SDK license automatically
android.accept_sdk_license = True

# (str) python-for-android git clone directory / branch
# Stable version பயன்படுத்துவது Build-ஐ சீராக இயக்கும்
p4a.branch = v2024.01.21

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = ignore, 1 = warn, 2 = error)
warn_on_root = 1
