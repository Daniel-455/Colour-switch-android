[app]

# (package) Application title
title = Hue strike

# (package) Package name
package.name = huestrike

# (package) Package domain
package.domain = org.game

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,json

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
requirements = python3,kivy

# (str) Supported orientation
orientation = portrait

# (bool) Fullscreen
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API
android.api = 31

# (int) Minimum API
android.minapi = 21

# (str) Android NDK version
android.ndk = 23b

# (list) Architectures to build for
android.archs = arm64-v8a

# (bool) Accept SDK licenses
android.accept_sdk_license = True

# Artifact format
android.release_artifact = apk
android.debug_artifact = apk

[buildozer]

log_level = 2
warn_on_root = 1
