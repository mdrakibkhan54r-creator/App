# RAKIB X — Android App (foreground-only)

Only test a website you own or have explicit permission to test.

## What this is (and isn't)

- A Kivy Android app with a Start/Stop button and a URL/rate/duration form.
- `android.permissions = INTERNET` only. No background service, no
  wake-lock, no boot-receiver, no notification permission.
- `on_pause()` in `main.py` calls `self.engine.stop()` — the moment Android
  backgrounds the app (home button, app switch, screen lock), the test
  stops itself. It only runs while you are looking at it, open in the
  foreground — same as a browser tab.

## How to build the APK (GitHub Actions does the real build — no Android
SDK/NDK needed on your phone)

1. Create a new **private** GitHub repository (e.g. `rakibx-app`).
2. Upload these 3 items into it, keeping the folder structure:
   - `main.py`
   - `buildozer.spec`
   - `.github/workflows/build.yml`
3. Go to the repo's **Actions** tab. The workflow runs automatically on
   push (or click "Run workflow" to trigger it manually).
4. Wait for the build to finish (first build can take ~15-20 minutes —
   it's compiling Python for Android from scratch).
5. Open the finished run → scroll to **Artifacts** → download
   `rakibx-apk` → unzip it, you'll get a `.apk` file.
6. Copy that `.apk` to your phone, enable "Install unknown apps" for your
   file manager/browser when prompted, and install it.

## Using the app

1. Open RakibX.
2. Target URL is pre-filled with your script
   (`https://kamrul24.site/Web/FreeHost/uploads/xrdpt8g8/1793974665_script.php`) — change it if needed.
3. Set Rate (requests/sec) and Minutes (0 = unlimited, but remember it
   only runs while the app is open on screen).
4. Tap the confirm toggle, then LAUNCH.
5. Tap STOP any time, or just leave the screen — it stops by itself.

## If you'd rather not deal with a 15-20 minute CI build

The Termux script (`rakibx_termux.py`, sent earlier in this chat) does the
exact same job, same throughput, same Stop behavior — just in a terminal
instead of an app icon, and it *can* keep running if you switch apps
(with `termux-wake-lock`). No GitHub, no build wait.
