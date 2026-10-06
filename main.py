"""
HUE STRIKE - Stroop-style brain game (Python + Kivy)
- No audio files needed: every sound effect and the background music are
  synthesized in code on first launch and cached in the app's data folder.
- Android: add VIBRATE to android.permissions in buildozer.spec.
"""
import os
import math
import wave
import array
import json
import random
import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.graphics import Color, Ellipse, Line
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.utils import platform

# ----------------------------------------------------------------------------
# Vibration (Android)
# ----------------------------------------------------------------------------
vibrator = None
VibrationEffect = None
SDK_INT = 0
if platform == 'android':
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        vibrator = PythonActivity.mActivity.getSystemService(Context.VIBRATOR_SERVICE)
        SDK_INT = autoclass('android.os.Build$VERSION').SDK_INT
        if SDK_INT >= 26:
            VibrationEffect = autoclass('android.os.VibrationEffect')
    except Exception as e:
        print(f"Vibration initialization failed: {e}")

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
BG = (0.07, 0.07, 0.09, 1)
TIME_LIMIT = 5.0
MAX_LIVES = 3

COLORS = {
    "RED": (1.0, 0.2, 0.2, 1),
    "BLUE": (0.1, 0.5, 1.0, 1),
    "GREEN": (0.1, 0.8, 0.3, 1),
    "YELLOW": (1.0, 0.85, 0.0, 1),
    "PURPLE": (0.7, 0.2, 0.9, 1),
    "ORANGE": (1.0, 0.5, 0.0, 1),
    "CYAN": (0.0, 0.85, 1.0, 1),
    "PINK": (1.0, 0.3, 0.7, 1),
}
COLOR_NAMES = list(COLORS.keys())

MILESTONES = {
    10: ("NICE!", (0.3, 1, 0.6, 1)),
    25: ("GREAT!", (0.3, 0.8, 1, 1)),
    50: ("AMAZING!", (1, 0.8, 0.2, 1)),
    75: ("UNSTOPPABLE!", (1, 0.4, 0.8, 1)),
    100: ("LEGENDARY!", (1, 0.3, 0.3, 1)),
}

BADGES = {
    "streak5": ("Hot Streak", "Get 5 correct answers in a row"),
    "streak15": ("On Fire", "Get 15 correct answers in a row"),
    "sharp25": ("Sharp Mind", "25 correct answers in one game"),
    "master50": ("Brain Master", "50 correct answers in one game"),
    "hard15": ("Hard Hitter", "15 correct answers in Hard mode"),
    "flawless": ("Flawless", "20 correct answers without losing a life"),
    "golden": ("Golden Touch", "Win a golden bonus round"),
    "smart": ("Smart Move", "Use a power-up"),
    "daily": ("Daily Done", "Complete the daily challenge"),
    "regular": ("Regular", "Play 10 games"),
}

# ----------------------------------------------------------------------------
# Sound synthesis (no audio files needed)
# ----------------------------------------------------------------------------
def ev(f0, start, dur, vol=0.5, f1=None, kind="sine", decay=4.0):
    """One note event: start/end frequency (glide), start time, duration..."""
    return (f0, f0 if f1 is None else f1, start, dur, vol, kind, decay)


def render(events, length, sr=22050, loop=False):
    n = int(length * sr)
    buf = [0.0] * n
    twopi = 2 * math.pi
    att = max(1, int(0.004 * sr))
    rel = max(1, int(0.01 * sr))
    for f0, f1, start, dur, vol, kind, decay in events:
        s = int(start * sr)
        m = max(1, int(dur * sr))
        phase = 0.0
        for i in range(m):
            t = i / m
            phase += twopi * (f0 + (f1 - f0) * t) / sr
            if kind == "sine":
                v = math.sin(phase) + 0.3 * math.sin(2 * phase) + 0.1 * math.sin(3 * phase)
            elif kind == "soft":
                v = math.sin(phase)
            elif kind == "saw":
                v = 2 * ((phase / twopi) % 1.0) - 1
            else:  # square
                v = 0.7 if math.sin(phase) > 0 else -0.7
            env = min(1.0, i / att) * min(1.0, (m - i) / rel) * math.exp(-decay * t)
            idx = s + i
            if idx >= n:
                if loop:
                    idx %= n
                else:
                    break
            buf[idx] += v * env * vol
    return array.array('h', [int(max(-1.0, min(1.0, x)) * 30000) for x in buf])


def write_wav(path, data, sr=22050):
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(data.tobytes())


def sfx_defs():
    d = {}
    d["click"] = ([ev(1000, 0, .05, .4, decay=7)], .08)
    d["tick"] = ([ev(1200, 0, .05, .3, kind="square", decay=9)], .08)
    for k in range(5):  # correct sound gets higher with the combo multiplier
        r = 2 ** (2 * k / 12.0)
        d["correct%d" % k] = ([ev(523.25 * r, 0, .10, .5), ev(659.25 * r, .07, .10, .5),
                               ev(783.99 * r, .14, .20, .5, decay=5)], .4)
    d["wrong"] = ([ev(260, 0, .35, .35, f1=90, kind="saw", decay=3)], .4)
    d["gameover"] = ([ev(392, 0, .3, .5, kind="soft", decay=3), ev(329.6, .25, .3, .5, kind="soft", decay=3),
                      ev(261.6, .5, .3, .5, kind="soft", decay=3), ev(196, .75, .7, .5, kind="soft", decay=2.5)], 1.5)
    d["freeze"] = ([ev(2093, 0, .5, .3, kind="soft", decay=5), ev(2637, .08, .5, .25, kind="soft", decay=5),
                    ev(3136, .16, .6, .22, kind="soft", decay=5), ev(800, 0, .3, .2, f1=300, kind="soft", decay=4)], .9)
    d["fifty"] = ([ev(500, 0, .12, .3, f1=1000, kind="square", decay=4),
                   ev(1000, .1, .12, .28, f1=500, kind="square", decay=4)], .3)
    d["skip"] = ([ev(400, 0, .22, .4, f1=1200, kind="soft", decay=3)], .25)
    d["recharge"] = ([ev(659, 0, .1, .4, kind="soft"), ev(880, .08, .1, .4, kind="soft"),
                      ev(1318, .16, .25, .4, kind="soft", decay=4)], .5)
    d["combo"] = ([ev(784, 0, .1, .5), ev(988, .08, .1, .5), ev(1175, .16, .1, .5),
                   ev(1568, .24, .3, .5, decay=4)], .6)
    d["milestone"] = ([ev(523, 0, .12, .5), ev(659, .1, .12, .5), ev(784, .2, .12, .5), ev(1046, .3, .12, .5)] +
                      [ev(f, .42, .7, .3, decay=3) for f in (523, 659, 784, 1046)], 1.2)
    d["newbest"] = ([ev(1046, 0, .1, .45), ev(1318, .08, .1, .45), ev(1568, .16, .1, .45),
                     ev(2093, .24, .1, .45), ev(1568, .34, .5, .4, decay=3)], .9)
    d["golden"] = ([ev(1319, 0, .4, .4, kind="soft", decay=3), ev(1760, 0, .4, .3, kind="soft", decay=3),
                    ev(2637, .05, .3, .2, kind="soft", decay=4)], .5)
    d["badge"] = ([ev(784, 0, .12, .45), ev(1046, .1, .12, .45), ev(1318, .2, .12, .45),
                   ev(1568, .3, .45, .45, decay=3)], .8)
    return d


def music_def():
    chords = [(220, 261.6, 329.6, 440), (174.6, 220, 261.6, 349.2),
              (261.6, 329.6, 392, 523.3), (196, 246.9, 293.7, 392)]
    pattern = [0, 1, 2, 3, 2, 1, 2, 1]
    events = []
    for c, ch in enumerate(chords):
        t0 = c * 2.0
        events.append(ev(ch[0] / 2, t0, 2.0, .32, kind="soft", decay=1.2))
        for j, p in enumerate(pattern):
            events.append(ev(ch[p], t0 + j * .25, .5, .2, kind="soft", decay=3))
    return events, 8.0


# ----------------------------------------------------------------------------
# Widgets
# ----------------------------------------------------------------------------
class CircleWidget(Widget):
    def __init__(self, **kwargs):
        super(CircleWidget, self).__init__(**kwargs)
        self.circle_color = (1, 1, 1, 1)
        self.golden = False
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def set_data(self, color_tuple, golden=False):
        self.circle_color = color_tuple
        self.golden = golden
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(*self.circle_color)
            size = min(self.width, self.height) * 0.72
            Ellipse(pos=(self.center_x - size / 2, self.center_y - size / 2), size=(size, size))
            if self.golden:
                Color(1, 0.84, 0, 1)
                Line(circle=(self.center_x, self.center_y, size / 2 + 8), width=3.5)


class LivesWidget(Widget):
    def __init__(self, **kwargs):
        super(LivesWidget, self).__init__(**kwargs)
        self.lives = 0
        self.total = 0
        self.bind(pos=self.redraw, size=self.redraw)

    def set_lives(self, lives, total=None):
        self.lives = lives
        if total is not None:
            self.total = total
        self.redraw()

    def redraw(self, *args):
        self.canvas.clear()
        if self.total <= 0:
            return
        d = min(self.height * 0.6, self.width / (self.total * 1.6))
        gap = d * 0.5
        x0 = self.center_x - (self.total * d + (self.total - 1) * gap) / 2
        with self.canvas:
            for i in range(self.total):
                x = x0 + i * (d + gap)
                if i < self.lives:
                    Color(1, 0.25, 0.35, 1)
                    Ellipse(pos=(x, self.center_y - d / 2), size=(d, d))
                else:
                    Color(0.35, 0.35, 0.4, 1)
                    Line(circle=(x + d / 2, self.center_y, d / 2), width=1.2)


def blink_widget(w):
    Animation.cancel_all(w)
    (Animation(opacity=.25, duration=.12) + Animation(opacity=1, duration=.12) +
     Animation(opacity=.25, duration=.12) + Animation(opacity=1, duration=.12)).start(w)


def S(wait, *fns):
    """A tutorial step: run all fns now, then wait `wait` seconds."""
    return (wait, lambda: [f() for f in fns])


# ----------------------------------------------------------------------------
# Tutorial (self-playing demo game)
# ----------------------------------------------------------------------------
class DemoBoard(BoxLayout):
    def __init__(self, app, **kwargs):
        super(DemoBoard, self).__init__(orientation='vertical', spacing=4, **kwargs)
        self.app = app
        self.caption = Label(text="", font_size='15sp', markup=True, halign='center',
                             valign='middle', size_hint=(1, .2))
        self.caption.bind(size=lambda i, v: setattr(i, 'text_size', (v[0] - 10, v[1])))
        self.add_widget(self.caption)

        top = BoxLayout(size_hint=(1, .07))
        self.lives = LivesWidget(size_hint=(.3, 1))
        self.combo = Label(text="", font_size='13sp', bold=True, color=(1, .7, .2, 1), size_hint=(.4, 1))
        self.tlabel = Label(text="Time: 5", font_size='13sp', color=(1, .3, .3, 1), size_hint=(.3, 1))
        for w in (self.lives, self.combo, self.tlabel):
            top.add_widget(w)
        self.add_widget(top)

        self.bar = ProgressBar(max=1, value=1, size_hint=(1, .03))
        self.add_widget(self.bar)

        self.area = FloatLayout(size_hint=(1, .28))
        self.ball = CircleWidget(size_hint=(1, 1), pos_hint={'center_x': .5, 'center_y': .6})
        self.word = Label(text="", font_size='26sp', bold=True, pos_hint={'center_x': .5, 'center_y': .6})
        self.prompt = Label(text="", font_size='16sp', bold=True, color=(1, .9, .2, 1),
                            size_hint=(1, .18), pos_hint={'center_x': .5, 'y': 0})
        for w in (self.ball, self.word, self.prompt):
            self.area.add_widget(w)
        self.add_widget(self.area)

        powers = BoxLayout(size_hint=(1, .09), spacing=4)
        self.pw = {}
        for key, txt, col in (("freeze", "FREEZE", (0, .7, .9, 1)), ("fifty", "50/50", (.6, .3, .9, 1)),
                              ("skip", "SKIP", (1, .55, .1, 1))):
            b = Button(text=txt, font_size='12sp', bold=True, background_normal='', background_color=col)
            self.pw[key] = b
            powers.add_widget(b)
        self.add_widget(powers)

        grid = GridLayout(cols=4, spacing=4, size_hint=(1, .33))
        self.btns = {}
        for n in COLOR_NAMES:
            b = Button(text=n, font_size='10sp', bold=True, background_normal='', background_color=COLORS[n])
            self.btns[n] = b
            grid.add_widget(b)
        self.add_widget(grid)

    # --- helpers used by the script ---
    def reset(self):
        Animation.cancel_all(self.bar)
        self.bar.value = 1
        self.bar.opacity = 1
        self.lives.set_lives(3, 3)
        self.combo.text = ""
        self.tlabel.text = "Time: 5"
        for b in list(self.btns.values()) + list(self.pw.values()):
            Animation.cancel_all(b)
            b.opacity = 1
        self.ball.set_data((.3, .3, .35, 1), False)
        self.word.text = ""
        self.prompt.text = ""
        self.caption.text = ""

    def say(self, text):
        self.caption.text = text

    def show(self, ball, word, prompt, golden=False):
        Animation.cancel_all(self.bar)
        self.bar.value = 1
        self.bar.opacity = 1
        self.tlabel.text = "Time: 5"
        for b in self.btns.values():
            Animation.cancel_all(b)
            b.opacity = 1
        self.ball.set_data(COLORS[ball], golden)
        self.word.text = word
        self.prompt.text = prompt
        if golden:
            self.app.sfx("golden")

    def practice(self):
        self.bar.opacity = 0
        self.tlabel.text = "Time: \u221e"
        self.lives.set_lives(0, 0)

    def tap(self, name):
        blink_widget(self.btns[name])
        self.app.sfx("click")

    def tap_power(self, key):
        b = self.pw[key]
        Animation.cancel_all(b)
        (Animation(opacity=.25, duration=.12) + Animation(opacity=1, duration=.12) +
         Animation(opacity=.25, duration=.12) + Animation(opacity=1, duration=.12) +
         Animation(opacity=.35, duration=.1)).start(b)
        self.app.sfx("click")

    def float(self, text, color, size='24sp', y0=.5, y1=.85):
        lbl = Label(text=text, font_size=size, bold=True, color=color, size_hint=(1, .3),
                    pos_hint={'center_x': .5, 'center_y': y0})
        self.area.add_widget(lbl)
        anim = Animation(pos_hint={'center_x': .5, 'center_y': y1}, opacity=0, duration=1.0, t='in_quad')
        anim.bind(on_complete=lambda a, w: self.area.remove_widget(lbl))
        anim.start(lbl)

    def good(self, text="+1", snd="correct0"):
        self.float(text, (.3, 1, .5, 1))
        self.app.sfx(snd)

    def drain(self, to, sec):
        Animation.cancel_all(self.bar)
        Animation(value=to, duration=sec).start(self.bar)

    def hold(self):
        Animation.cancel_all(self.bar)

    def lose_life(self, left):
        self.hold()
        self.lives.set_lives(left, 3)
        self.float("-1 LIFE", (1, .3, .35, 1))
        self.app.sfx("wrong")

    def streak(self, n):
        mult = min(1 + n // 5, 5)
        self.combo.text = "STREAK %d  x%d" % (n, mult)
        if n % 5 == 0:
            self.float("COMBO x%d!" % mult, (1, .7, .2, 1), '28sp')
            self.app.sfx("combo")
        else:
            self.float("+1", (.3, 1, .5, 1))
            self.app.sfx("correct%d" % (mult - 1))

    def freeze_on(self):
        self.hold()
        self.tlabel.text = "FROZEN 3s"
        self.float("FROZEN!", (0, .85, 1, 1), '28sp')
        self.app.sfx("freeze")

    def freeze_off(self):
        self.tlabel.text = "Time: 3"
        self.drain(.2, 1.5)

    def fifty(self, correct):
        wrong = [n for n in COLOR_NAMES if n != correct][:4]
        for n in wrong:
            Animation(opacity=.12, duration=.3).start(self.btns[n])
        self.app.sfx("fifty")

    def skip(self):
        self.float("SKIPPED", (1, .6, .2, 1), '26sp')
        self.app.sfx("skip")

    def recharge(self):
        for b in self.pw.values():
            b.opacity = .35
        Animation(opacity=1, duration=.4).start(self.pw["fifty"])
        self.float("RECHARGED!", (.3, 1, .6, 1), '26sp')
        self.app.sfx("recharge")


def build_pages(b):
    return [
        ("THE BASICS", [
            S(3.2, lambda: b.say("You see a [b]BALL[/b] with a [b]WORD[/b] on it.\nTheir colors are often [color=ff5555]different[/color]!"),
              lambda: b.show("BLUE", "RED", "")),
            S(3.2, lambda: b.say("The yellow prompt tells you [b]what to match[/b].\nHere: the BALL color."),
              lambda: b.show("BLUE", "RED", "MATCH BALL COLOR!")),
            S(1.0, lambda: b.say("The ball is BLUE, so tap [b]BLUE[/b]!"), lambda: b.tap("BLUE")),
            S(1.8, lambda: b.good("+1")),
            S(3.2, lambda: b.say("New round! The prompt now says [b]WORD[/b].\nRead the word and ignore the ball."),
              lambda: b.show("GREEN", "PINK", "MATCH WRITTEN WORD!")),
            S(1.0, lambda: b.say("The word says PINK, so tap [b]PINK[/b]!"), lambda: b.tap("PINK")),
            S(1.8, lambda: b.good("+1")),
            S(3.0, lambda: b.say("Correct answer = points.\nWrong answer = you lose a life!")),
        ]),
        ("GAME MODES", [
            S(3.8, lambda: b.say("[color=3388ff][b]EASY[/b][/color]: you pick COLOR or WORD once and the prompt stays the same all game. 1 point per answer."),
              lambda: b.show("RED", "BLUE", "MATCH BALL COLOR!")),
            S(2.0, lambda: b.show("GREEN", "ORANGE", "MATCH BALL COLOR!")),
            S(3.8, lambda: b.say("[color=ff3333][b]HARD[/b][/color]: the prompt changes every round, so stay sharp! 10 points per answer."),
              lambda: b.show("PURPLE", "CYAN", "MATCH WRITTEN WORD!")),
            S(2.0, lambda: b.show("ORANGE", "GREEN", "MATCH BALL COLOR!")),
            S(3.8, lambda: b.say("[color=aa55ff][b]PRACTICE[/b][/color]: no timer and no lives. Relax and train your instincts!"),
              lambda: b.show("PINK", "YELLOW", "MATCH WRITTEN WORD!"), lambda: b.practice()),
        ]),
        ("TIMER, LIVES & COMBO", [
            S(2.6, lambda: b.say("Every round has a [b]5 second[/b] timer.\nWatch the bar drain!"),
              lambda: b.show("CYAN", "RED", "MATCH BALL COLOR!"), lambda: b.drain(.3, 3.0)),
            S(1.2, lambda: b.say("Time runs out or you tap the wrong color: you lose a [color=ff4455]life[/color]. You get 3 lives."),
              lambda: b.tap("RED")),
            S(3.0, lambda: b.lose_life(2)),
            S(2.5, lambda: b.say("Answer correctly in a row to build a [color=ffaa33]COMBO[/color]!"),
              lambda: b.show("BLUE", "GREEN", "MATCH BALL COLOR!")),
            S(.6, lambda: b.streak(1)), S(.6, lambda: b.streak(2)), S(.6, lambda: b.streak(3)),
            S(.6, lambda: b.streak(4)), S(2.0, lambda: b.streak(5)),
            S(3.8, lambda: b.say("Every 5 in a row raises your multiplier: x2, x3, x4, x5!\nOne mistake resets it.")),
        ]),
        ("POWER-UPS", [
            S(2.2, lambda: b.say("[color=00ccee][b]FREEZE[/b][/color]: stops the timer for 3 seconds. Use it when you need time to think!"),
              lambda: b.show("YELLOW", "PURPLE", "MATCH BALL COLOR!"), lambda: b.drain(.5, 2.2)),
            S(1.0, lambda: b.tap_power("freeze")),
            S(3.0, lambda: b.freeze_on(), lambda: b.say("The timer is paused. Take your time!")),
            S(1.2, lambda: b.freeze_off(), lambda: b.tap("YELLOW")),
            S(1.5, lambda: b.good("+1")),
            S(3.2, lambda: b.say("[color=aa55ff][b]50/50[/b][/color]: removes 4 wrong answers, so only 4 colors are left!"),
              lambda: b.show("ORANGE", "PINK", "MATCH BALL COLOR!")),
            S(.8, lambda: b.tap_power("fifty")),
            S(2.5, lambda: b.fifty("ORANGE")),
            S(1.0, lambda: b.tap("ORANGE")),
            S(1.5, lambda: b.good("+1")),
            S(3.2, lambda: b.say("[color=ff9922][b]SKIP[/b][/color]: jump to a new round. No points, but [b]no life lost[/b] and your combo 
