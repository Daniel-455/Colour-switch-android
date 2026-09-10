[app]

title = Color Switch
package.name = colorswitch
package.domain = org.test

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

requirements = python3,kivy==2.3.0

version = 0.1
orientation = portrait

android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a

# Python 3.14 பிழையைத் தவிர்க்க நிலையான p4a பதிப்பு:
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 0
