import os
import csv
import io
import ssl
import shutil
import urllib.request

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.textinput import TextInput
from kivy.utils import get_color_from_hex

ONLINE_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJdUUlLlRZ49lBcKxR7QhUx-8Grh6iks1vR00BRiNXej4UUx3rfFQR1tikuZLX53aJLP8vb4kPyBgh/pub?gid=0&single=true&output=csv"
VERSION_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJdUUlLlRZ49lBcKxR7QhUx-8Grh6iks1vR00BRiNXej4UUx3rfFQR1tikuZLX53aJLP8vb4kPyBgh/pub?gid=95776090&single=true&output=csv"

# ---- Design values (copy the hex codes from Figma here) ----
DARK, GRAY, BORDER = "#222222", "#6B6B6B", "#D0D0D0"
RED = "#A92B2B"
FIELD_BG, RESULT_BG = "#FFFFFF", "#EFEFEF"
PLACEHOLDER = "Calculated automatically"

HERE = os.path.dirname(os.path.abspath(__file__))
Window.clearcolor = get_color_from_hex("#EDEDED")
Window.softinput_mode = "below_target"  # keep the field above the keyboard

# Android has no system CA store for Python, so use certifi's
try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_CTX = ssl.create_default_context()


# ---------------- data ----------------
def fetch(url, timeout):
    with urllib.request.urlopen(url, timeout=timeout, context=SSL_CTX) as r:
        return r.read().decode("utf-8-sig")


def parse(text):
    """CSV text -> {tank: [(ideal, correction), ...]}.
    A blank Tank cell means 'same tank as the row above'."""
    db, tank = {}, None
    for row in csv.DictReader(io.StringIO(text)):
        tank = (row.get("Tank") or "").strip() or tank
        try:
            point = (float(row["IdealOutput"]), float(row["Correction"]))
        except (KeyError, TypeError, ValueError):
            continue  # skip bad rows instead of crashing
        if tank:
            db.setdefault(tank, []).append(point)
    return {t: sorted(p) for t, p in db.items()}


def load_data():
    """Use saved CSV; refresh from Google Sheet only if its version changed."""
    folder = App.get_running_app().user_data_dir  # writable on Android
    os.makedirs(folder, exist_ok=True)
    data_file = os.path.join(folder, "tanks_data.csv")
    ver_file = os.path.join(folder, "local_version.txt")

    if not os.path.exists(data_file):  # first run: copy the CSV inside the APK
        bundled = os.path.join(HERE, "tanks_data.csv")
        if os.path.exists(bundled):
            shutil.copy(bundled, data_file)

    local_ver = "0"
    if os.path.exists(ver_file):
        with open(ver_file) as f:
            local_ver = f.read().strip()

    try:
        rows = list(csv.DictReader(io.StringIO(fetch(VERSION_CSV_URL, 3))))
        online_ver = rows[0]["Version"].strip()
        if online_ver != local_ver or not os.path.exists(data_file):
            text = fetch(ONLINE_CSV_URL, 5)
            if parse(text):  # save only if the download is valid
                with open(data_file, "w", encoding="utf-8") as f:
                    f.write(text)
                with open(ver_file, "w") as f:
                    f.write(online_ver)
    except Exception:
        pass  # no internet -> keep saved data

    if os.path.exists(data_file):
        with open(data_file, encoding="utf-8-sig") as f:
            return parse(f.read())
    return {}


# ---------------- look ----------------
def style_box(w, fill, line=None, radius=dp(10)):
    """Rounded background (and optional border) behind any widget.
    Returns the fill Color so it can be changed later."""
    with w.canvas.before:
        fill_color = Color(*get_color_from_hex(fill))
        rect = RoundedRectangle(radius=[radius])
        if line:
            Color(*get_color_from_hex(line))
            border = Line(width=1)

    def sync(*_):
        rect.pos, rect.size = w.pos, w.size
        if line:
            border.rounded_rectangle = (w.x, w.y, w.width, w.height, radius)

    w.bind(pos=sync, size=sync)
    sync()
    return fill_color


def add_chevron(w):
    """Small down arrow on the right side of the dropdown."""
    with w.canvas.after:
        Color(*get_color_from_hex(GRAY))
        arrow = Line(width=1.4, cap="round", joint="round")

    def sync(*_):
        cx, cy, s = w.right - dp(26), w.center_y, dp(5)
        arrow.points = [cx - s, cy + s / 2, cx, cy - s / 2, cx + s, cy + s / 2]

    w.bind(pos=sync, size=sync)
    sync()


def pad_left(w, size):
    w.text_size = (size[0] - dp(32), size[1])  # 16dp text margin each side


class Option(SpinnerOption):
    """White dropdown rows with dark text."""
    def __init__(self, **kw):
        super().__init__(**kw)
        self.background_normal = ""
        self.background_color = get_color_from_hex("#FFFFFF")
        self.color = get_color_from_hex(DARK)
        self.height = dp(44)


class ResultBox(Label):
    """Grey read-only box that shows a placeholder until a value is set."""
    def __init__(self, **kw):
        super().__init__(halign="left", valign="middle", font_size="16sp",
                         size_hint_y=None, height=dp(46), **kw)
        self.bind(size=pad_left)
        style_box(self, RESULT_BG, BORDER)
        self.clear()

    def clear(self):
        self.text, self.color = PLACEHOLDER, get_color_from_hex(GRAY)

    def show(self, value):
        self.text, self.color = value, get_color_from_hex(DARK)


def group(title, widget):
    """Label on top, field below."""
    box = BoxLayout(orientation="vertical", spacing=dp(6),
                    size_hint_y=None, height=dp(76))
    lbl = Label(text=title, color=get_color_from_hex(DARK), font_size="16sp",
                halign="left", valign="middle", size_hint_y=None, height=dp(24))
    lbl.bind(size=lambda w, s: setattr(w, "text_size", s))
    box.add_widget(lbl)
    box.add_widget(widget)
    return box


# ---------------- screen ----------------
class TankScreen(FloatLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.db = load_data()
        tanks = list(self.db) or ["No Data Found"]

        # background photo (export from Figma as background.png)
        self.add_widget(Image(source=os.path.join(HERE, "background.png"),
                              fit_mode="cover"))

        # white card
        card = BoxLayout(orientation="vertical", padding=dp(22), spacing=dp(14),
                         size_hint=(0.87, None),
                         pos_hint={"center_x": 0.5, "center_y": 0.5})
        card.bind(minimum_height=card.setter("height"))
        style_box(card, "#FFFFFF", radius=dp(12))

        # 1. tank dropdown
        self.tank = Spinner(text="Choose a tank", values=tanks, option_cls=Option,
                            halign="left", valign="middle", font_size="16sp",
                            color=get_color_from_hex(GRAY),
                            background_normal="", background_down="",
                            background_color=(0, 0, 0, 0),
                            size_hint_y=None, height=dp(46))
        self.tank.bind(size=pad_left, text=self.calculate)
        style_box(self.tank, FIELD_BG, BORDER)
        add_chevron(self.tank)

        # 2. volume input
        self.volume = TextInput(hint_text="Value", multiline=False,
                                input_filter="float", input_type="number",
                                font_size="16sp", padding=[dp(16), dp(12)],
                                background_normal="", background_active="",
                                background_color=(0, 0, 0, 0),
                                foreground_color=get_color_from_hex(DARK),
                                hint_text_color=get_color_from_hex(GRAY),
                                cursor_color=get_color_from_hex(RED),
                                size_hint_y=None, height=dp(46))
        style_box(self.volume, FIELD_BG, BORDER)
        self.volume.bind(text=self.calculate)

        # 3-4. results
        self.corr_box = ResultBox()
        self.final_box = ResultBox()

        card.add_widget(group("Select Tank", self.tank))
        card.add_widget(group("Input Volume", self.volume))
        card.add_widget(group("Correction", self.corr_box))
        card.add_widget(group("Final Volume", self.final_box))
        self.add_widget(card)

    def calculate(self, *_):
        pts = self.db.get(self.tank.text)
        self.tank.color = get_color_from_hex(DARK if pts else GRAY)
        try:
            vol = float(self.volume.text)
        except ValueError:
            pts = None
        if not pts:
            self.corr_box.clear()
            self.final_box.clear()
            return

        if vol <= pts[0][0]:
            corr = pts[0][1]
        elif vol >= pts[-1][0]:
            corr = pts[-1][1]
        else:
            corr = 0.0
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                if x0 <= vol <= x1 and x1 != x0:
                    corr = y0 + (vol - x0) * (y1 - y0) / (x1 - x0)
                    break

        self.corr_box.show(f"{corr:+.2f}")
        self.final_box.show(f"{vol + corr:,.2f}")


class TankInterpolationApp(App):
    def build(self):
        return TankScreen()


if __name__ == "__main__":
    TankInterpolationApp().run()
