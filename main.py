"""
RAKIB X — Android app (Kivy), foreground-only load tester.

Only test a website you own or have explicit permission to test.

IMPORTANT behavior by design:
- No background service, no background permissions are requested.
- The test ONLY runs while this app is open and in the foreground.
- Minimizing, closing, or switching away from the app stops the test
  (Android will pause/kill the worker thread along with the app),
  exactly like closing a browser tab would.
"""

import threading
import time
import random
import urllib.request
import urllib.error

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup

DEFAULT_URL = "https://kamrul24.site/Web/FreeHost/uploads/xrdpt8g8/1793974665_script.php"


class Engine:
    """Runs entirely on a background THREAD inside this app's own process.
    It only exists while the app process is alive and in the foreground;
    there is no Android service, no WorkManager, no boot receiver — closing
    the app ends it, same as closing a browser tab."""

    def __init__(self, on_update):
        self.on_update = on_update
        self._stop = threading.Event()
        self.thread = None
        self.dispatched = 0
        self.success = 0
        self.fail = 0

    def is_running(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self, url, rate, duration_sec, max_workers=200):
        self._stop.clear()
        self.dispatched = 0
        self.success = 0
        self.fail = 0
        self.thread = threading.Thread(
            target=self._run, args=(url, rate, duration_sec, max_workers), daemon=True
        )
        self.thread.start()

    def stop(self):
        self._stop.set()

    def _fire_one(self, url):
        t0 = time.time()
        ok = False
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "RakibX-App/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp.read(0)
                ok = 200 <= resp.status < 400
        except urllib.error.HTTPError as e:
            ok = 200 <= e.code < 400
        except Exception:
            ok = False
        return ok, int((time.time() - t0) * 1000)

    def _run(self, url, target_rate, duration_sec, max_workers):
        from concurrent.futures import ThreadPoolExecutor

        start = time.time()
        executor = ThreadPoolExecutor(max_workers=max_workers)
        in_flight = [0]
        lock = threading.Lock()

        def done_cb(fut):
            with lock:
                in_flight[0] -= 1
            try:
                ok, ms = fut.result()
                with lock:
                    if ok:
                        self.success += 1
                    else:
                        self.fail += 1
            except Exception:
                with lock:
                    self.fail += 1

        last_emit = 0
        while True:
            elapsed = time.time() - start
            if duration_sec > 0 and elapsed >= duration_sec:
                break
            if self._stop.is_set():
                break

            ramp_sec = min(8, max(1, (duration_sec or 60) * 0.2))
            if elapsed < ramp_sec:
                base = max(5, target_rate * 0.05)
                rate = base + (target_rate - base) * (elapsed / ramp_sec)
            else:
                rate = min(target_rate, target_rate * (0.9 + random.randint(0, 200) / 1000.0))

            to_add = max(1, int(round(rate * 0.05)))
            with lock:
                capacity = max_workers - in_flight[0]
            to_add = max(0, min(to_add, capacity))

            for _ in range(to_add):
                fut = executor.submit(self._fire_one, url)
                fut.add_done_callback(done_cb)
                with lock:
                    in_flight[0] += 1
                self.dispatched += 1

            now = time.time()
            if now - last_emit > 0.3:
                Clock.schedule_once(lambda dt: self.on_update(self.dispatched, self.success, self.fail, int(rate)))
                last_emit = now
            time.sleep(0.02)

        executor.shutdown(wait=True, cancel_futures=False)
        Clock.schedule_once(lambda dt: self.on_update(self.dispatched, self.success, self.fail, 0, finished=True))


class RakibXRoot(BoxLayout):
    pass


class RakibXApp(App):
    def build(self):
        self.engine = Engine(self.on_engine_update)
        root = BoxLayout(orientation="vertical", padding=14, spacing=10)

        root.add_widget(Label(text="[b]RAKIB X[/b] — foreground-only load tester", markup=True, size_hint_y=None, height=30))
        warn = Label(
            text="Only test a website you own or have permission to test.\nCloses the test automatically if you leave this app.",
            size_hint_y=None, height=50, color=(1, 0.75, 0.3, 1),
        )
        root.add_widget(warn)

        self.url_input = TextInput(text=DEFAULT_URL, multiline=False, size_hint_y=None, height=44)
        root.add_widget(Label(text="Target URL", size_hint_y=None, height=22))
        root.add_widget(self.url_input)

        row = BoxLayout(size_hint_y=None, height=44, spacing=8)
        self.rate_input = TextInput(text="2000", multiline=False, input_filter="int")
        self.dur_input = TextInput(text="5", multiline=False, input_filter="float")
        row.add_widget(Label(text="Rate /sec", size_hint_x=None, width=70))
        row.add_widget(self.rate_input)
        row.add_widget(Label(text="Minutes", size_hint_x=None, width=70))
        row.add_widget(self.dur_input)
        root.add_widget(row)

        self.confirm_toggle = ToggleButton(text="I confirm this is my own site (tap to confirm)", size_hint_y=None, height=44)
        root.add_widget(self.confirm_toggle)

        btn_row = BoxLayout(size_hint_y=None, height=52, spacing=8)
        self.start_btn = Button(text="LAUNCH")
        self.stop_btn = Button(text="STOP", disabled=True)
        self.start_btn.bind(on_release=self.on_start)
        self.stop_btn.bind(on_release=self.on_stop)
        btn_row.add_widget(self.start_btn)
        btn_row.add_widget(self.stop_btn)
        root.add_widget(btn_row)

        self.stats_label = Label(text="Dispatched: 0   Success: 0   Fail: 0   Rate: 0/s", size_hint_y=None, height=30)
        root.add_widget(self.stats_label)

        self.verdict_label = Label(text="", size_hint_y=None, height=80)
        root.add_widget(self.verdict_label)

        root.add_widget(Label())  # spacer
        return root

    def on_start(self, *_):
        if not self.confirm_toggle.state == "down":
            self.show_popup("Please confirm this is your own website first.")
            return
        url = self.url_input.text.strip()
        if not url.startswith("http"):
            url = "https://" + url
        try:
            rate = max(1, int(self.rate_input.text or "2000"))
        except ValueError:
            rate = 2000
        try:
            minutes = float(self.dur_input.text or "5")
        except ValueError:
            minutes = 5
        duration_sec = 0 if minutes <= 0 else int(minutes * 60)

        self.start_btn.disabled = True
        self.stop_btn.disabled = False
        self.verdict_label.text = ""
        self.engine.start(url, rate, duration_sec)

    def on_stop(self, *_):
        self.engine.stop()

    def on_engine_update(self, dispatched, success, fail, rate, finished=False):
        self.stats_label.text = f"Dispatched: {dispatched}   Success: {success}   Fail: {fail}   Rate: {rate}/s"
        if finished:
            self.start_btn.disabled = False
            self.stop_btn.disabled = True
            fail_pct = round((fail / dispatched) * 100) if dispatched else 0
            self.verdict_label.text = f"Done. Failure rate: {fail_pct}%"

    def on_pause(self):
        # Android called this when the app goes to background (home button,
        # app switch, screen lock). We deliberately do NOT keep running —
        # this app has no background permission, by design.
        self.engine.stop()
        return True

    def show_popup(self, text):
        Popup(title="RakibX", content=Label(text=text), size_hint=(0.8, 0.3)).open()


if __name__ == "__main__":
    RakibXApp().run()
