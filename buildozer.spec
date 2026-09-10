[app]

title = Color Switch
package.name = colorswitch
package.domain = org.test

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

requirements = python3,kivy==2.3.0

version = 0.1
orientation = portrait

android.api = 34
android.minapi = 23
android.ndk = 25b
android.sdk_build_tools_version = 34.0.0
android.accept_sdk_license = True
android.archs = arm64-v8a

p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 0
