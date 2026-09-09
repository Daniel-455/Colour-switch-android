[app]

title = Color Switch
package.name = colorswitch
package.domain = org.colorswitch

source.dir = .
source.main = main.py

version = 1.0.0

requirements = python3,kivy==2.3.0

orientation = portrait
fullscreen = 1

android.permissions = INTERNET
android.api = 35
android.minapi = 23
android.archs = arm64-v8a
android.accept_sdk_license = True

# presplash.filename = %(source.dir)s/data/presplash.png
# icon.filename = %(source.dir)s/data/icon.png


[buildozer]

log_level = 2
warn_on_root = 1
