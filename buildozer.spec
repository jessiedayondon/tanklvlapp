[app]

# (str) Title of your application
title = Tank Level Corrector

# (str) Package name
package.name = tanklevelapp

# (str) Package domain (needed for android packaging)
package.domain = org.tankcorrector

# (str) Source code directory
source.dir = .

# (str) List of inclusions using pattern matching
source.include_exts = py, png, jpg, kv, atlas, csv

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
# Added specific Python 3.11 bindings and required web dependencies 
requirements = python3==3.11.0, hostpython3==3.11.0, kivy, requests, urllib3, idna, certifi

# (str) Supported orientations
orientation = portrait

# (list) Permissions (Required to ping your VersionControl Google Sheet online)
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible.
android.api = 34

# (int) Minimum API your APK will support.
android.minapi = 21

# (bool) If True, then skip trying to update the Android sdk licenses
android.accept_sdk_license = True

# (list) The Android architectures to build for
android.archs = arm64-v8a, armeabi-v7a

# (bool) Use command line for progress (keeps build actions logging readable)
android.skip_update = False

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = false, 1 = true)
warn_on_root = 0
