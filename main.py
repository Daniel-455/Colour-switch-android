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
            S(3.2, lambda: b.say("[color=ff9922][b]SKIP[/b][/color]: jump to a new round. No points, but [b]no life lost[/b] and your combo is safe!"),
              lambda: b.show("PINK", "CYAN", "MATCH WRITTEN WORD!")),
            S(.8, lambda: b.tap_power("skip")),
            S(2.5, lambda: b.skip(), lambda: b.show("RED", "GREEN", "MATCH BALL COLOR!")),
            S(1.0, lambda: b.say("Each power-up works [b]once per game[/b].\nEvery 20 correct answers, one used power-up [color=33ff88]recharges[/color]!")),
            S(3.6, lambda: b.recharge()),
        ]),
        ("BONUS, BEST & BADGES", [
            S(3.6, lambda: b.say("A [color=ffd700][b]GOLDEN RING[/b][/color] around the ball means a bonus round: [b]DOUBLE[/b] points!"),
              lambda: b.show("ORANGE", "RED", "MATCH BALL COLOR! BONUS x2", True)),
            S(1.0, lambda: b.tap("ORANGE")),
            S(1.6, lambda: b.good("+2")),
            S(3.2, lambda: b.say("Hit milestones (10, 25, 50, 75, 100 correct) and the game cheers for you!"),
              lambda: b.float("AMAZING!", (1, .8, .2, 1), '34sp'), lambda: b.app.sfx("milestone")),
            S(3.6, lambda: b.say("Beat your high score for [b]NEW BEST![/b]\nFinish the [b]DAILY CHALLENGE[/b] and collect [b]BADGES[/b]!"),
              lambda: b.float("NEW BEST!", (1, .5, .9, 1), '30sp'), lambda: b.app.sfx("newbest")),
            S(3.0, lambda: b.say("That's everything. Tap CLOSE and strike!")),
        ]),
    ]


class Tutorial(BoxLayout):
    def __init__(self, app, **kwargs):
        super(Tutorial, self).__init__(orientation='vertical', spacing=6, padding=6, **kwargs)
        self.app = app
        self.gen = 0
        self.page = 0
        self.title_lbl = Label(text="", font_size='15sp', bold=True, color=(.1, .9, .9, 1), size_hint=(1, .06))
        self.board = DemoBoard(app, size_hint=(1, .78))
        self.pages = build_pages(self.board)
        nav = BoxLayout(size_hint=(1, .1), spacing=6)
        btn_prev = Button(text="< PREV", bold=True, background_normal='', background_color=(.25, .25, .35, 1))
        btn_next = Button(text="NEXT >", bold=True, background_normal='', background_color=(.2, .6, 1, 1))
        self.close_btn = Button(text="CLOSE", bold=True, background_normal='', background_color=(.8, .25, .25, 1))
        btn_prev.bind(on_release=lambda x: self.goto(self.page - 1))
        btn_next.bind(on_release=lambda x: self.goto(self.page + 1))
        for w in (btn_prev, btn_next, self.close_btn):
            nav.add_widget(w)
        self.add_widget(self.title_lbl)
        self.add_widget(self.board)
        self.add_widget(nav)

    def goto(self, i):
        self.page = i % len(self.pages)
        self.play()

    def play(self):
        self.gen += 1
        title, steps = self.pages[self.page]
        self.title_lbl.text = "%d/%d  %s" % (self.page + 1, len(self.pages), title)
        self.board.reset()
        self.run(steps, 0, self.gen)

    def run(self, steps, i, g):
        if g != self.gen:
            return
        if i >= len(steps):
            Clock.schedule_once(lambda dt: self.goto(self.page + 1) if g == self.gen else None, 2.0)
            return
        wait, fn = steps[i]
        fn()
        Clock.schedule_once(lambda dt: self.run(steps, i + 1, g), wait)

    def stop(self):
        self.gen += 1
        Animation.cancel_all(self.board.bar)


# ----------------------------------------------------------------------------
# Main app
# ----------------------------------------------------------------------------
class HueStrikeApp(App):
    # ------------------------------------------------------------------ setup
    def build(self):
        self.title = "Hue Strike"
        self.data = self.load_data()
        self.scores = self.data["scores"]
        self.sfx_on = self.data["settings"].get("sfx", True)
        self.music_on = self.data["settings"].get("music", True)
        self.sounds = {}
        self.music = None
        self.popups = 0

        self.state = "menu"      # menu | easy_select | playing | over
        self.game_id = 0
        self.accepting = False
        self.timer_event = None
        self.menu_event = None
        self.game_mode = "EASY"
        self.easy_mode = "COLOR"
        self.score = self.correct_count = self.streak = self.lives = 0
        self.time_left = TIME_LIMIT
        self.freeze_left = 0.0
        self.golden = False
        self.last_pair = None
        self.correct_answer = ""
        self.pu = {}
        self.prev_best = 0
        self.newbest_shown = False
        self.no_life_lost = True
        self.answer_buttons = {}
        self.power_buttons = {}

        self.make_sounds()
        self.check_daily()

        self.main_layout = BoxLayout(orientation='vertical', padding=[12, 10, 12, 10], spacing=5)

        header = FloatLayout(size_hint=(1, 0.08))
        self.btn_back = Button(text="BACK", font_size='13sp', bold=True, size_hint=(0.2, 0.65),
                               pos_hint={'x': 0.01, 'center_y': 0.5}, background_normal='',
                               background_color=(0.25, 0.25, 0.35, 1), opacity=0, disabled=True)
        self.btn_back.bind(on_release=self.go_back_to_menu)
        self.title_label = Label(text="HUE STRIKE", font_size='19sp', bold=True, color=(0.1, 0.9, 0.9, 1),
                                 pos_hint={'center_x': 0.41, 'center_y': 0.5})
        self.btn_sfx = Button(text="SFX ON", font_size='11sp', bold=True, size_hint=(0.17, 0.65),
                              pos_hint={'right': 0.78, 'center_y': 0.5}, background_normal='')
        self.btn_sfx.bind(on_release=self.toggle_sfx)
        self.btn_music = Button(text="MUSIC ON", font_size='11sp', bold=True, size_hint=(0.2, 0.65),
                                pos_hint={'right': 0.99, 'center_y': 0.5}, background_normal='')
        self.btn_music.bind(on_release=self.toggle_music)
        for w in (self.btn_back, self.title_label, self.btn_sfx, self.btn_music):
            header.add_widget(w)
        self.refresh_audio_buttons()
        self.main_layout.add_widget(header)

        info = BoxLayout(orientation='horizontal', size_hint=(1, 0.05))
        self.score_label = Label(text="Score: 0", font_size='15sp', color=(1, 1, 1, 1))
        self.best_label = Label(text="Best: -", font_size='15sp', color=(1, 0.8, 0.2, 1))
        self.timer_label = Label(text="Time: -", font_size='15sp', color=(1, 0.3, 0.3, 1))
        for w in (self.score_label, self.best_label, self.timer_label):
            info.add_widget(w)
        self.main_layout.add_widget(info)

        row2 = BoxLayout(orientation='horizontal', size_hint=(1, 0.05))
        self.lives_widget = LivesWidget(size_hint=(0.4, 1))
        self.combo_label = Label(text="", font_size='14sp', bold=True, color=(1, 0.7, 0.2, 1), size_hint=(0.6, 1))
        row2.add_widget(self.lives_widget)
        row2.add_widget(self.combo_label)
        self.main_layout.add_widget(row2)

        self.bar = ProgressBar(max=1, value=0, size_hint=(1, 0.012))
        self.main_layout.add_widget(self.bar)

        self.circle_container = FloatLayout(size_hint=(1, 0.33))
        self.circle_widget = CircleWidget(size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.55})
        self.circle_container.add_widget(self.circle_widget)
        self.word_label = Label(text="", font_size='32sp', bold=True, color=(1, 1, 1, 1),
                                pos_hint={'center_x': 0.5, 'center_y': 0.55})
        self.circle_container.add_widget(self.word_label)
        self.mode_label = Label(text="", font_size='20sp', bold=True, color=(1, 0.9, 0.2, 1), markup=True,
                                size_hint=(1, 0.15), pos_hint={'center_x': 0.5, 'y': 0.02},
                                halign='center', valign='center')
        self.circle_container.add_widget(self.mode_label)
        self.main_layout.add_widget(self.circle_container)

        self.controls_layout = FloatLayout(size_hint=(1, 0.45))
        self.main_layout.add_widget(self.controls_layout)

        Window.bind(on_keyboard=self.on_key)
        self.show_main_menu(silent=True)
        Clock.schedule_once(self.init_music, 0.6)
        return self.main_layout

    # ------------------------------------------------------------------ data
    def data_path(self):
        return os.path.join(self.user_data_dir, "hue_strike_data.json")

    def load_data(self):
        default = {"scores": {}, "stats": {"games": 0, "correct": 0, "wrong": 0, "best_streak": 0},
                   "badges": [], "daily": {}, "settings": {"sfx": True, "music": True}}
        try:
            with open(self.data_path(), "r") as f:
                loaded = json.load(f)
            for k, v in default.items():
                loaded.setdefault(k, v)
            for k, v in default["stats"].items():
                loaded["stats"].setdefault(k, v)
            return loaded
        except Exception:
            return default

    def save_data(self):
        try:
            os.makedirs(self.user_data_dir, exist_ok=True)
            self.data["settings"] = {"sfx": self.sfx_on, "music": self.music_on}
            with open(self.data_path(), "w") as f:
                json.dump(self.data, f)
        except Exception as e:
            print(f"Save error: {e}")

    def check_daily(self):
        today = datetime.date.today().isoformat()
        if self.data["daily"].get("date") != today:
            goal = random.Random(today).choice([30, 40, 50, 60])
            self.data["daily"] = {"date": today, "goal": goal, "count": 0, "done": False}

    def daily_text(self):
        d = self.data["daily"]
        if d.get("done"):
            return "[color=33ff88]DAILY CHALLENGE DONE![/color]"
        return "DAILY CHALLENGE: %d/%d correct" % (d.get("count", 0), d.get("goal", 0))

    def best_key(self):
        return "EASY_" + self.easy_mode if self.game_mode == "EASY" else self.game_mode

    # ----------------------------------------------------------------- audio
    def make_sounds(self):
        d = self.user_data_dir
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass
        for name, (events, length) in sfx_defs().items():
            path = os.path.join(d, "hs_v1_%s.wav" % name)
            try:
                if not os.path.exists(path):
                    write_wav(path, render(events, length))
                self.sounds[name] = SoundLoader.load(path)
            except Exception as e:
                print(f"Sound error ({name}): {e}")
                self.sounds[name] = None

    def init_music(self, dt):
        path = os.path.join(self.user_data_dir, "hs_v1_music.wav")
        try:
            if not os.path.exists(path):
                events, length = music_def()
                write_wav(path, render(events, length, sr=11025, loop=True), sr=11025)
            self.music = SoundLoader.load(path)
            if self.music:
                self.music.loop = True
                self.music.volume = 0.3
                if self.music_on:
                    self.music.play()
        except Exception as e:
            print(f"Music error: {e}")

    def sfx(self, name):
        if not self.sfx_on:
            return
        s = self.sounds.get(name)
        if s:
            try:
                s.stop()
                s.play()
            except Exception as e:
                print(f"Sound play error: {e}")

    def toggle_sfx(self, *args):
        self.sfx_on = not self.sfx_on
        self.refresh_audio_buttons()
        self.sfx("click")
        self.save_data()

    def toggle_music(self, *args):
        self.music_on = not self.music_on
        self.refresh_audio_buttons()
        if self.music:
            try:
                self.music.play() if self.music_on else self.music.stop()
            except Exception:
                pass
        self.save_data()

    def refresh_audio_buttons(self):
        on, off = (0.15, 0.5, 0.2, 1), (0.6, 0.2, 0.2, 1)
        self.btn_sfx.text = "SFX ON" if self.sfx_on else "SFX OFF"
        self.btn_sfx.background_color = on if self.sfx_on else off
        self.btn_music.text = "MUSIC ON" if self.music_on else "MUSIC OFF"
        self.btn_music.background_color = on if self.music_on else off

    def vibrate(self, duration=30):
        if vibrator:
            try:
                if VibrationEffect is not None:
                    vibrator.vibrate(VibrationEffect.createOneShot(duration, VibrationEffect.DEFAULT_AMPLITUDE))
                else:
                    vibrator.vibrate(duration)
            except Exception as e:
                print(f"Vibrate error: {e}")

    # ------------------------------------------------------------- lifecycle
    def on_pause(self):
        self.save_data()
        if self.music:
            try:
                self.music.stop()
            except Exception:
                pass
        return True

    def on_resume(self):
        if self.music and self.music_on:
            try:
                self.music.play()
            except Exception:
                pass

    def on_stop(self):
        self.save_data()

    def on_key(self, window, key, *args):
        if key == 27:  # Android back / Esc
            if self.popups > 0:
                return False
            if self.state != "menu":
                self.go_back_to_menu()
                return True
        return False

    # --------------------------------------------------------------- helpers
    def later(self, fn, delay):
        gid = self.game_id
        Clock.schedule_once(lambda dt: fn() if gid == self.game_id else None, delay)

    def cancel_timer(self):
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None

    def stop_menu_anim(self):
        if self.menu_event:
            self.menu_event.cancel()
            self.menu_event = None

    def open_popup(self, title, content, size=(0.9, 0.8), on_close=None):
        p = Popup(title=title, content=content, size_hint=size)
        self.popups += 1

        def closed(*a):
            self.popups = max(0, self.popups - 1)
            if on_close:
                on_close()
        p.bind(on_dismiss=closed)
        p.open()
        return p

    def float_text(self, text, color, size='26sp', y0=0.55, y1=0.85, dur=0.8):
        lbl = Label(text=text, font_size=size, bold=True, color=color, size_hint=(1, 0.2),
                    pos_hint={'center_x': 0.5, 'center_y': y0})
        self.circle_container.add_widget(lbl)
        anim = Animation(pos_hint={'center_x': 0.5, 'center_y': y1}, opacity=0, duration=dur, t='in_quad')
        anim.bind(on_complete=lambda a, w: self.circle_container.remove_widget(lbl))
        anim.start(lbl)

    def announce(self, text, color, slot=0):
        y0 = 0.3 + 0.14 * slot
        self.float_text(text, color, '34sp', y0, y0 + 0.2, 1.1)

    def unlock(self, bid):
        if bid in self.data["badges"]:
            return
        self.data["badges"].append(bid)
        self.save_data()
        self.sfx("badge")
        self.float_text("BADGE: " + BADGES[bid][0], (1, 0.84, 0, 1), '17sp', 0.93, 0.8, 1.6)

    def blink(self, total, done):
        def step(n):
            if n >= total:
                self.update_dynamic_theme()
                done()
                return
            Window.clearcolor = (0.7, 0.05, 0.05, 1) if n % 2 == 0 else BG
            self.later(lambda: step(n + 1), 0.1)
        step(0)

    def update_dynamic_theme(self):
        if self.state != "playing":
            Window.clearcolor = BG
        elif self.correct_count >= 25:
            Window.clearcolor = (0.12, 0.05, 0.15, 1)
        elif self.correct_count >= 10:
            Window.clearcolor = (0.05, 0.1, 0.15, 1)
        else:
            Window.clearcolor = BG

    def set_back(self, visible):
        self.btn_back.opacity = 1 if visible else 0
        self.btn_back.disabled = not visible

    # ------------------------------------------------------------------ menu
    def go_back_to_menu(self, *args):
        self.save_data()
        self.show_main_menu()

    def show_main_menu(self, silent=False):
        self.game_id += 1
        self.cancel_timer()
        self.stop_menu_anim()
        self.state = "menu"
        self.accepting = False
        if not silent:
            self.sfx("click")
            self.vibrate(20)
        self.set_back(False)
        self.controls_layout.clear_widgets()
        self.word_label.text = ""
        self.mode_label.font_size = '15sp'
        self.mode_label.text = self.daily_text()
        self.score_label.text = "Score: 0"
        self.best_label.text = "Best: -"
        self.timer_label.text = "Time: -"
        self.combo_label.text = ""
        self.lives_widget.set_lives(0, 0)
        self.bar.value = 0
        Window.clearcolor = BG
        self.menu_tick(0)
        self.menu_event = Clock.schedule_interval(self.menu_tick, 0.9)

        layout = BoxLayout(orientation='vertical', spacing=8, size_hint=(0.85, 0.95),
                           pos_hint={'center_x': 0.5, 'center_y': 0.5})

        def mk(text, color, cb, size='16sp'):
            b = Button(text=text, font_size=size, bold=True, background_color=color, background_normal='')
            b.bind(on_release=lambda x: cb())
            return b
        layout.add_widget(mk("EASY MODE", (0.2, 0.8, 0.4, 1), self.choose_easy_mode))
        layout.add_widget(mk("HARD MODE", (0.9, 0.2, 0.3, 1), lambda: self.start_game("HARD")))
        layout.add_widget(mk("PRACTICE (NO TIMER)", (0.6, 0.3, 0.9, 1), lambda: self.start_game("PRACTICE"), '14sp'))
        layout.add_widget(mk("HOW TO PLAY (DEMO)", (0.2, 0.6, 1.0, 1), self.show_tutorial, '14sp'))
        row = BoxLayout(spacing=8)
        row.add_widget(mk("SCORES", (1.0, 0.6, 0.1, 1), self.show_scores_popup, '14sp'))
        row.add_widget(mk("BADGES", (0.9, 0.75, 0.1, 1), self.show_badges_popup, '14sp'))
        layout.add_widget(row)
        self.controls_layout.add_widget(layout)

    def menu_tick(self, dt):
        self.circle_widget.set_data(random.choice(list(COLORS.values())), False)

    def choose_easy_mode(self):
        self.sfx("click")
        self.vibrate(20)
        self.state = "easy_select"
        self.set_back(True)
        self.controls_layout.clear_widgets()
        self.mode_label.text = "EASY: CHOOSE A STYLE"
        layout = BoxLayout(orientation='vertical', spacing=10, size_hint=(0.85, 0.6),
                           pos_hint={'center_x': 0.5, 'center_y': 0.5})
        for label, mode, col in (("MATCH COLOR\n(tap the BALL color)", "COLOR", (0.2, 0.6, 1.0, 1)),
                                 ("MATCH WORD\n(tap the WRITTEN word)", "WORD", (1.0, 0.6, 0.2, 1))):
            b = Button(text=label, font_size='17sp', bold=True, halign='center',
                       background_color=col, background_normal='')
            b.bind(on_release=lambda x, m=mode: self.select_easy_submode(m))
            layout.add_widget(b)
        self.controls_layout.add_widget(layout)

    def select_easy_submode(self, mode):
        self.easy_mode = mode
        self.start_game("EASY")

    # ---------------------------------------------------------------- popups
    def show_tutorial(self):
        self.sfx("click")
        t = Tutorial(self)
        p = self.open_popup("How to Play", t, (0.97, 0.93), on_close=t.stop)
        t.close_btn.bind(on_release=lambda x: p.dismiss())
        t.goto(0)

    def show_scores_popup(self):
        self.sfx("click")
        sc, st = self.scores, self.data["stats"]
        total = st["correct"] + st["wrong"]
        acc = round(100 * st["correct"] / total) if total else 0
        text = ("[size=20sp][b]HIGH SCORES[/b][/size]\n\n"
                "[color=33ff88]EASY - COLOR:[/color] %d\n[color=33ccff]EASY - WORD:[/color] %d\n"
                "[color=ff3366]HARD:[/color] %d\n[color=aa55ff]PRACTICE:[/color] %d\n\n"
                "[size=20sp][b]YOUR STATS[/b][/size]\n\nGames played: %d\nAccuracy: %d%%\nBest streak: %d") % (
            sc.get("EASY_COLOR", 0), sc.get("EASY_WORD", 0), sc.get("HARD", 0), sc.get("PRACTICE", 0),
            st["games"], acc, st["best_streak"])
        content = BoxLayout(orientation='vertical', padding=12, spacing=10)
        content.add_widget(Label(text=text, markup=True, font_size='16sp', halign='center'))
        btn = Button(text="CLOSE", size_hint=(1, 0.14), bold=True)
        content.add_widget(btn)
        p = self.open_popup("Scores & Stats", content, (0.85, 0.75))
        btn.bind(on_release=lambda x: p.dismiss())

    def show_badges_popup(self):
        self.sfx("click")
        content = BoxLayout(orientation='vertical', padding=8, spacing=8)
        scroll = ScrollView(size_hint=(1, 0.85))
        grid = GridLayout(cols=1, spacing=6, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        for bid, (title, desc) in BADGES.items():
            got = bid in self.data["badges"]
            if got:
                txt = "[color=ffd700][b]%s[/b][/color]\n[size=12sp]%s[/size]" % (title, desc)
            else:
                txt = "[color=777777][b]%s (locked)[/b]\n[size=12sp]%s[/size][/color]" % (title, desc)
            lbl = Label(text=txt, markup=True, font_size='15sp', size_hint_y=None, height=dp(56), halign='left', valign='middle')
            lbl.bind(width=lambda i, v: setattr(i, 'text_size', (v - 10, None)))
            grid.add_widget(lbl)
        scroll.add_widget(grid)
        btn = Button(text="CLOSE", size_hint=(1, 0.13), bold=True)
        content.add_widget(scroll)
        content.add_widget(btn)
        p = self.open_popup("Badges (%d/%d)" % (len(self.data["badges"]), len(BADGES)), content, (0.9, 0.8))
        btn.bind(on_release=lambda x: p.dismiss())

    # ------------------------------------------------------------------ game
    def start_game(self, mode):
        self.stop_menu_anim()
        self.cancel_timer()
        self.game_id += 1
        self.sfx("click")
        self.vibrate(20)
        self.set_back(True)

        self.game_mode = mode
        self.state = "playing"
        self.score = 0
        self.correct_count = 0
        self.streak = 0
        self.lives = MAX_LIVES if mode != "PRACTICE" else 0
        self.pu = {"freeze": True, "fifty": True, "skip": True}
        self.freeze_left = 0.0
        self.golden = False
        self.last_pair = None
        self.newbest_shown = False
        self.no_life_lost = True
        self.prev_best = self.scores.get(self.best_key(), 0)

        self.score_label.text = "Score: 0"
        self.best_label.text = "Best: %d" % self.prev_best
        self.combo_label.text = ""
        self.lives_widget.set_lives(self.lives, self.lives)
        self.mode_label.font_size = '20sp'
        self.bar.opacity = 0 if mode == "PRACTICE" else 1
        self.bar.value = 1

        self.data["stats"]["games"] += 1
        if self.data["stats"]["games"] >= 10:
            self.unlock("regular")

        self.setup_game_buttons()
        self.new_round()

    def setup_game_buttons(self):
        self.controls_layout.clear_widgets()
        self.power_buttons = {}
        if self.game_mode != "PRACTICE":
            row = BoxLayout(spacing=6, size_hint=(0.98, 0.15), pos_hint={'center_x': 0.5, 'top': 1.0})
            for key, txt, col in (("freeze", "FREEZE (3s)", (0.0, 0.7, 0.9, 1)),
                                  ("fifty", "50/50", (0.6, 0.3, 0.9, 1)),
                                  ("skip", "SKIP", (1.0, 0.55, 0.1, 1))):
                b = Button(text=txt, font_size='13sp', bold=True, background_color=col, background_normal='')
                b.bind(on_release=lambda x, k=key: self.use_power(k))
                self.power_buttons[key] = b
                row.add_widget(b)
            self.controls_layout.add_widget(row)

        grid = GridLayout(cols=4, spacing=6, size_hint=(0.98, 0.8), pos_hint={'center_x': 0.5, 'y': 0.0})
        self.answer_buttons = {}
        for name in COLOR_NAMES:
            btn = Button(text=name, font_size='11sp', bold=True, background_normal='', background_color=COLORS[name])
            btn.bind(on_release=lambda instance, n=name: self.check_answer(n))
            self.answer_buttons[name] = btn
            grid.add_widget(btn)
        self.controls_layout.add_widget(grid)

    def new_round(self, *args):
        if self.state != "playing":
            return
        self.cancel_timer()
        self.update_dynamic_theme()
        for b in self.answer_buttons.values():
            Animation.cancel_all(b)
            b.disabled = False
            b.opacity = 1

        while True:
            ball, word = random.choice(COLOR_NAMES), random.choice(COLOR_NAMES)
            if (ball, word) != self.last_pair:
                break
        self.last_pair = (ball, word)

        sub = self.easy_mode if self.game_mode == "EASY" else random.choice(["COLOR", "WORD"])
        self.golden = (self.game_mode != "PRACTICE" and self.correct_count >= 5 and random.random() < 0.12)

        self.circle_widget.set_data(COLORS[ball], self.golden)
        self.word_label.text = word
        if sub == "COLOR":
            prompt, self.correct_answer = "MATCH BALL COLOR!", ball
        else:
            prompt, self.correct_answer = "MATCH WRITTEN WORD!", word
        if self.golden:
            self.mode_label.font_size = '16sp'
            self.mode_label.text = prompt + "  [color=ffd700]BONUS x2![/color]"
            self.sfx("golden")
        else:
            self.mode_label.font_size = '20sp'
            self.mode_label.text = prompt

        self.accepting = True
        self.freeze_left = 0.0
        if self.game_mode == "PRACTICE":
            self.timer_label.text = "Time: \u221e"
        else:
            self.time_left = TIME_LIMIT
            self.bar.value = 1
            self.timer_label.text = "Time: %d" % TIME_LIMIT
            self.timer_event = Clock.schedule_interval(self.tick, 0.1)

    def tick(self, dt):
        if self.state != "playing" or not self.accepting:
            return
        if self.freeze_left > 0:
            self.freeze_left = max(0.0, self.freeze_left - dt)
            self.timer_label.text = "Time: %d [FROZEN]" % math.ceil(self.time_left)
            return
        prev = math.ceil(self.time_left)
        self.time_left -= dt
        cur = math.ceil(max(self.time_left, 0))
        self.bar.value = max(0.0, self.time_left / TIME_LIMIT)
        self.timer_label.text = "Time: %d" % cur
        if cur < prev and 0 < cur <= 2:
            self.sfx("tick")
        if self.time_left <= 0:
            self.cancel_timer()
            self.accepting = False
            self.handle_wrong("TIME'S UP!")

    # ----------------------------------------------------------- power-ups
    def use_power(self, name):
        if self.state != "playing" or not self.accepting or not self.pu.get(name):
            return
        self.pu[name] = False
        self.vibrate(30)
        self.unlock("smart")
        btn = self.power_buttons[name]
        btn.disabled = True
        btn.opacity = 0.35
        if name == "freeze":
            self.freeze_left = 3.0
            self.sfx("freeze")
            self.float_text("FROZEN 3s", (0, 0.9, 1, 1), '26sp', 0.5, 0.8)
        elif name == "fifty":
            wrong = [n for n in COLOR_NAMES if n != self.correct_answer]
            for n in random.sample(wrong, 4):
                b = self.answer_buttons[n]
                b.disabled = True
                b.opacity = 0.15
            self.sfx("fifty")
        elif name == "skip":
            self.accepting = False
            self.cancel_timer()
            self.sfx("skip")
            self.float_text("SKIPPED", (1, 0.6, 0.2, 1), '26sp', 0.5, 0.8)
            self.later(self.new_round, 0.25)

    def recharge_power(self):
        used = [k for k, v in self.pu.items() if not v]
        if not used:
            return False
        k = random.choice(used)
        self.pu[k] = True
        b = self.power_buttons.get(k)
        if b:
            b.disabled = False
            b.opacity = 1
        return True

    # -------------------------------------------------------------- answers
    def check_answer(self, name):
        if self.state != "playing" or not self.accepting:
            return
        self.accepting = False
        self.cancel_timer()
        if name == self.correct_answer:
            self.handle_correct()
        else:
            self.handle_wrong("WRONG ANSWER!")

    def handle_correct(self):
        self.streak += 1
        self.correct_count += 1
        c = self.correct_count
        st = self.data["stats"]
        st["correct"] += 1
        st["best_streak"] = max(st["best_streak"], self.streak)

        mult = min(1 + self.streak // 5, 5)
        base = 10 if self.game_mode == "HARD" else 1
        pts = base * mult * (2 if self.golden else 1)
        self.score += pts
        self.score_label.text = "Score: %d" % self.score
        self.combo_label.text = ("STREAK %d  x%d" % (self.streak, mult)) if self.streak >= 2 else ""
        self.vibrate(40)
        self.float_text("+%d" % pts, (0.3, 1, 0.6, 1))

        snd = "correct%d" % (mult - 1)
        msgs = []

        newbest = False
        key = self.best_key()
        if self.score > self.scores.get(key, 0):
            self.scores[key] = self.score
            self.best_label.text = "Best: %d" % self.score
            if self.prev_best > 0 and not self.newbest_shown:
                self.newbest_shown = True
                newbest = True

        if self.game_mode != "PRACTICE":
            d = self.data["daily"]
            if not d.get("done"):
                d["count"] += 1
                if d["count"] >= d["goal"]:
                    d["done"] = True
                    msgs.append(("DAILY DONE!", (0.3, 1, 0.6, 1)))
                    self.unlock("daily")
            if c % 20 == 0 and self.recharge_power():
                msgs.append(("POWER-UP RECHARGED!", (0.3, 1, 0.8, 1)))
                snd = "recharge"

        if self.streak % 5 == 0:
            msgs.append(("COMBO x%d!" % mult, (1, 0.7, 0.2, 1)))
            snd = "combo"
        if newbest:
            msgs.append(("NEW BEST!", (1, 0.5, 0.9, 1)))
            snd = "newbest"
        if c in MILESTONES:
            msgs.append(MILESTONES[c])
            snd = "milestone"
        for i, (t, col) in enumerate(msgs[:3]):
            self.announce(t, col, i)
        self.sfx(snd)

        if self.golden:
            self.unlock("golden")
        self.check_badges()
        self.later(self.new_round, 0.25)

    def check_badges(self):
        if self.game_mode == "PRACTICE":
            return
        c = self.correct_count
        if self.streak >= 5:
            self.unlock("streak5")
        if self.streak >= 15:
            self.unlock("streak15")
        if c >= 25:
            self.unlock("sharp25")
        if c >= 50:
            self.unlock("master50")
        if self.game_mode == "HARD" and c >= 15:
            self.unlock("hard15")
        if self.no_life_lost and c >= 20:
            self.unlock("flawless")

    def handle_wrong(self, reason):
        self.streak = 0
        self.combo_label.text = ""
        self.data["stats"]["wrong"] += 1
        self.sfx("wrong")
        self.vibrate(200)
        ans = self.answer_buttons.get(self.correct_answer)
        if ans:
            blink_widget(ans)  # show the right answer

        if self.game_mode == "PRACTICE":
            self.float_text("WRONG!", (1, 0.3, 0.3, 1))
            self.later(self.new_round, 0.9)
            return

        self.lives -= 1
        self.no_life_lost = False
        self.lives_widget.set_lives(self.lives)
        if self.lives > 0:
            self.float_text("-1 LIFE", (1, 0.3, 0.35, 1), '28sp')
            self.blink(4, self.new_round)
        else:
            self.blink(8, lambda: self.game_over(reason))

    def game_over(self, reason):
        self.cancel_timer()
        self.state = "over"
        self.accepting = False
        self.save_data()
        Window.clearcolor = BG
        self.sfx("gameover")
        self.mode_label.text = ""
        self.controls_layout.clear_widgets()

        layout = BoxLayout(orientation='vertical', spacing=8, size_hint=(0.85, 0.9),
                           pos_hint={'center_x': 0.5, 'center_y': 0.5})
        layout.add_widget(Label(text=reason, font_size='22sp', bold=True, color=(1, 0.2, 0.2, 1)))
        new_best = self.score > self.prev_best and self.score > 0
        score_text = "Score: %d" % self.score + ("   [color=ff66cc]NEW BEST![/color]" if new_best else "")
        layout.add_widget(Label(text=score_text, font_size='19sp', markup=True))
        layout.add_widget(Label(text="Correct: %d     Best streak: %d" % (
            self.correct_count, self.data["stats"]["best_streak"]), font_size='13sp', color=(0.8, 0.8, 0.8, 1)))

        btn_retry = Button(text="PLAY AGAIN", font_size='18sp', bold=True,
                           background_color=(0.2, 0.8, 0.4, 1), background_normal='')
        btn_retry.bind(on_release=lambda x: self.start_game(self.game_mode))
        btn_menu = Button(text="MAIN MENU", font_size='16sp', bold=True,
                          background_color=(0.2, 0.6, 1.0, 1), background_normal='')
        btn_menu.bind(on_release=lambda x: self.show_main_menu())
        layout.add_widget(btn_retry)
        layout.add_widget(btn_menu)
        self.controls_layout.add_widget(layout)


if __name__ == "__main__":
    HueStrikeApp().run()
