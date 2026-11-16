[app]
title = RakibX
package.name = rakibx
package.domain = org.rakibx

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0

requirements = python3,kivy

orientation = portrait
fullscreen = 0

# Only the plain internet permission — no background service, no
# foreground-service, no boot-completed, no wake-lock. By design this app
# cannot keep sending requests once Android backgrounds it.
android.permissions = INTERNET

android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
