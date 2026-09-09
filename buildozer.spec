[app]
title = My Application
package.name = myapp
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# Requirements
requirements = python3,kivy==2.3.0

# Versioning
version = 0.1

# Android Configurations
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk_build_tools_version = 33.0.2
android.accept_sdk_license = True
android.archs = arm64-v8a

p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 0
