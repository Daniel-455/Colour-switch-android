[app]
title = My Kivy App
package.name = myapp
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 0.1
requirements = python3,kivy==2.3.0

orientation = portrait

[android]
android.api = 35
android.minapi = 23
android.ndk = 25b
android.sdk = 35
android.ndk_api = 23
android.archs = arm64-v8a

android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
