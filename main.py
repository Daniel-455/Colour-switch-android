from random import choice

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget


COLORS = {
    "RED": (1, 0.2, 0.2, 1),
    "BLUE": (0.2, 0.4, 1, 1),
    "GREEN": (0.13, 0.67, 0.33, 1),
    "YELLOW": (0.9, 0.77, 0.0, 1),
}
COLOR_NAMES = list(COLORS)


class Ball(Widget):
    actual_color = StringProperty("RED")
    word_color = StringProperty("RED")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._draw, size=self._draw, actual_color=self._draw)
        self._draw()

    def _draw(self, *_):
        self.canvas.clear()
        with self.canvas:
            Color(*COLORS[self.actual_color])
            size = min(self.width, self.height) * 0.88
            x = self.x + (self.width - size) / 2
            y = self.y + (self.height - size) / 2
            Ellipse(pos=(x, y), size=(size, size))


class ColorSwitchApp(App):
    score = NumericProperty(0)
    best_score = NumericProperty(0)
    time_left = NumericProperty(5)
    instruction = StringProperty("Choose a mode")
    game_mode = ""
    easy_mode = ""
    correct_answer = ""
    timer_event = None
    next_round_event = None

    def build(self):
        Window.clearcolor = (1, 1, 1, 1)
        self.title = "COLOR SWITCH"
        try:
            with open("best_score.txt", "r", encoding="utf-8") as f:
                self.best_score = int(f.read().strip() or 0)
        except (OSError, ValueError):
            self.best_score = 0

        self.root = BoxLayout(orientation="vertical", padding=12, spacing=8)
        self.title_label = Label(text="COLOR SWITCH", font_size="24sp", bold=True, size_hint_y=None, height=48, color=(0, 0, 0, 1))
        self.score_label = Label(size_hint_y=None, height=30, color=(0, 0, 0, 1))
        self.best_label = Label(size_hint_y=None, height=30, color=(0, 0, 0, 1))
        self.timer_label = Label(size_hint_y=None, height=30, color=(0, 0, 0, 1))
        self.mode_label = Label(text="Choose a mode", font_size="16sp", bold=True, size_hint_y=None, height=42, color=(0, 0, 0, 1))

        self.root.add_widget(self.title_label)
        self.root.add_widget(self.score_label)
        self.root.add_widget(self.best_label)
        self.root.add_widget(self.timer_label)
        self.root.add_widget(self.mode_label)

        self.content = BoxLayout(orientation="vertical", spacing=8)
        self.root.add_widget(self.content)
        self.show_mode_menu()
        self.update_labels()
        return self.root

    def update_labels(self):
        self.score_label.text = f"Score: {self.score}"
        self.best_label.text = f"Best: {self.best_score}"
        self.timer_label.text = f"Time: {self.time_left}"

    def clear_content(self):
        self.stop_timers()
        self.content.clear_widgets()

    def make_button(self, text, callback):
        btn = Button(text=text, font_size="16sp", bold=True, size_hint_y=None, height=58)
        btn.bind(on_release=callback)
        return btn

    def show_mode_menu(self, *_):
        self.clear_content()
        self.mode_label.text = "Choose a mode"
        row = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=64)
        row.add_widget(self.make_button("EASY", lambda *_: self.start_game("EASY")))
        row.add_widget(self.make_button("HARD", lambda *_: self.start_game("HARD")))
        self.content.add_widget(row)
        self.update_labels()

    def start_game(self, mode):
        self.score = 0
        self.time_left = 5
        self.game_mode = mode
        self.easy_mode = ""
        self.update_labels()
        if mode == "EASY":
            self.show_easy_menu()
        else:
            self.mode_label.text = "HARD - COLOR or WORD changes"
            self.show_game()

    def show_easy_menu(self):
        self.clear_content()
        self.mode_label.text = "EASY: Choose COLOR or WORD"
        row = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=64)
        row.add_widget(self.make_button("COLOR", lambda *_: self.select_easy_mode("COLOR")))
        row.add_widget(self.make_button("WORD", lambda *_: self.select_easy_mode("WORD")))
        self.content.add_widget(row)

    def select_easy_mode(self, mode):
        self.easy_mode = mode
        self.mode_label.text = f"EASY - {mode}"
        self.show_game()

    def show_game(self):
        self.clear_content()
        self.mode_label.text = self.mode_label.text or "COLOR SWITCH"
        self.ball = Ball(size_hint_y=1)
        self.word_label = Label(font_size="16sp", bold=True, color=(1, 1, 1, 1), size_hint=(None, None), size=(100, 45))
        self.ball.add_widget(self.word_label)
        self.word_label.center = self.ball.center
        self.ball.bind(pos=self.center_word, size=self.center_word)
        self.content.add_widget(self.ball)

        self.instruction_label = Label(text="", font_size="17sp", bold=True, color=(0, 0, 0, 1), size_hint_y=None, height=42)
        self.content.add_widget(self.instruction_label)
        self.answer_grid = BoxLayout(orientation="vertical", spacing=8, size_hint_y=None, height=132)
        top = BoxLayout(spacing=8)
        bottom = BoxLayout(spacing=8)
        for name, row in (("RED", top), ("BLUE", top), ("GREEN", bottom), ("YELLOW", bottom)):
            row.add_widget(self.make_button(name, lambda btn, n=name: self.check_answer(n)))
        self.answer_grid.add_widget(top)
        self.answer_grid.add_widget(bottom)
        self.content.add_widget(self.answer_grid)
        self.new_round()

    def center_word(self, *_):
        if hasattr(self, "word_label"):
            self.word_label.center = self.ball.center

    def new_round(self, *_):
        self.stop_timers()
        self.time_left = max(2, 5 - (int(self.score) // 10))
        actual = choice(COLOR_NAMES)
        word = choice(COLOR_NAMES)
        mode = self.easy_mode if self.game_mode == "EASY" else choice(("COLOR", "WORD"))
        self.ball.actual_color = actual
        self.ball.word_color = word
        self.word_label.text = word
        self.correct_answer = actual if mode == "COLOR" else word
        self.instruction_label.text = "CHOOSE BALL COLOR" if mode == "COLOR" else "CHOOSE WORD"
        self.update_labels()
        self.timer_event = Clock.schedule_interval(self.countdown, 1)

    def countdown(self, _dt):
        self.time_left -= 1
        self.update_labels()
        if self.time_left <= 0:
            self.game_over("TIME'S UP!")

    def check_answer(self, answer):
        self.stop_timers()
        if answer == self.correct_answer:
            self.score += 1 if self.game_mode == "EASY" else 10
            if self.score > self.best_score:
                self.best_score = self.score
                try:
                    with open("best_score.txt", "w", encoding="utf-8") as f:
                        f.write(str(self.best_score))
                except OSError:
                    pass
            self.update_labels()
            self.next_round_event = Clock.schedule_once(self.new_round, 0.25)
        else:
            self.score = max(0, self.score - (1 if self.game_mode == "EASY" else 5))
            self.update_labels()
            self.game_over("WRONG ANSWER!")

    def stop_timers(self):
        if self.timer_event is not None:
            self.timer_event.cancel()
            self.timer_event = None
        if self.next_round_event is not None:
            self.next_round_event.cancel()
            self.next_round_event = None

    def game_over(self, reason):
        self.stop_timers()
        self.clear_content()
        self.mode_label.text = reason
        self.content.add_widget(Label(text=f"Your Score: {self.score}\nBest Score: {self.best_score}", font_size="22sp", bold=True, color=(0, 0, 0, 1)))
        self.content.add_widget(self.make_button("PLAY AGAIN", lambda *_: self.show_mode_menu()))


if __name__ == "__main__":
    ColorSwitchApp().run()
