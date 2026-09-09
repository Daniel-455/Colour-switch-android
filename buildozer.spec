[app]

# (str) Title of your application
title = My Application

# (str) Package name
package.name = myapp

# (str) Package domain (needed for android packaging)
package.domain = org.test

# (str) Source files where the let it be (relative to directory of buildozer.spec)
source.dir = .

# (list) Source files to include (let it empty to include all files)
source.include_exts = py,png,jpg,kv,atlas

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy==2.3.0

# (str) Version of the application
version = 0.1

# (list) Supported orientations
orientation = portrait

#
# Android specific
#

# (int) Target Android API, should be as high as possible.
android.api = 34

# (int) Minimum API your APK / AAB will support.
android.minapi = 23

# (str) Android SDK build tools version to use
android.sdk_build_tools_version = 34.0.0

# (bool) If True, automatically accept the SDK license
android.accept_sdk_license = True

# (list) Permissions
#android.permissions = INTERNET

# (list) aab archs
android.archs = arm64-v8a

# (str) python-for-android branch to use
p4a.branch = master

[buildozer]

# (int) Log level (0 = error, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 0
