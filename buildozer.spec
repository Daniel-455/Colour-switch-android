[app]

# (your app title and name)
title = My Application
package.name = myapp
package.domain = org.test

# Source code location
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# Requirements
requirements = python3,kivy==2.3.0

# Android specific settings
android.api = 34
android.minapi = 23
android.sdk_build_tools_version = 34.0.0
android.archs = arm64-v8a
android.accept_sdk_license = True

# Python for android settings
p4a.branch = master
