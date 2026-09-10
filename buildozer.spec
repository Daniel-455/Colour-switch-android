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

[buildozer]
log_level = 2
warn_on_root = 0
