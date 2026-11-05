[app]
title = Tank Level Corrector
package.name = tanklevelapp
package.domain = org.tankcorrector
source.dir = .
source.include_exts = py,csv,png,jpg
version = 1.0.0
requirements = python3,kivy==2.3.0,openssl,certifi
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 34
android.minapi = 21
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0
