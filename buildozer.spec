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
# Removing pinned versions lets Buildozer pull safe, pre-compiled environment recipes
requirements = python3, kivy, requests, urllib3, idna, certifi

# (str) Supported orientations
orientation = portrait

# (list) Permissions (Required to ping your VersionControl Google Sheet online)
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible.
android.api = 34

# (int) Minimum API your APK will support.
android.minapi = 21

# (bool) Automatically accept SDK licenses
android.accept_sdk_license = True

# (list) Only compiling for modern 64-bit devices cuts your build time in half!
android.archs = arm64-v8a

# (bool) Use command line for progress
android.skip_update = False

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 0
