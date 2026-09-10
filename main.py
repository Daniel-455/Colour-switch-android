import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.clock import Clock
from kivy.core.window import Window

# Dark Neon Background setup
Window.clearcolor = (0.07, 0.07, 0.09, 1)

COLORS = {
    "RED": (1.0, 0.2, 0.3, 1),
    "BLUE": (0.2, 0.5, 1.0, 1),
    "GREEN": (0.2, 0.8, 0.4, 1),
    "YELLOW": (1.0, 0.8, 0.1, 1)
}

COLOR_NAMES = ["RED", "BLUE", "GREEN", "YELLOW"]

class CircleWidget(Widget):
    def __init__(self, **kwargs):
        super(CircleWidget, self).__init__(**kwargs)
        self.circle_color = (1, 1, 1, 1)
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def set_color(self, color_tuple):
        self.circle_color = color_tuple
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(*self.circle_color)
            size = min(self.width, self.height) * 0.75
            x = self.center_x - size / 2
            y = self.center_y - size / 2
            Ellipse(pos=(x, y), size=(size, size))

class HueStrikeApp(App):
    def build(self):
        self.title = "Hue Strike"
        self.score = 0
        self.best_score = self.load_best_score()
        self.correct_count = 0
        self.time_left = 5
        self.game_mode = ""
        self.easy_mode = ""
        self.timer_event = None

        self.main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

        # Header Title
        self.title_label = Label(
            text="HUE STRIKE",
            font_size='28sp',
            bold=True,
            color=(0.1, 0.9, 0.9, 1),
            size_hint=(1, 0.08)
        )
        self.main_layout.add_widget(self.title_label)

        # Score & Timer Panel
        self.info_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.06))
        self.score_label = Label(text="Score: 0", font_size='18sp', color=(1, 1, 1, 1))
        self.best_label = Label(text=f"Best: {self.best_score}", font_size='18sp', color=(1, 0.8, 0.2, 1))
        self.timer_label = Label(text="Time: 5", font_size='18sp', color=(1, 0.3, 0.3, 1))

        self.info_layout.add_widget(self.score_label)
        self.info_layout.add_widget(self.best_label)
        self.info_layout.add_widget(self.timer_label)
        self.main_layout.add_widget(self.info_layout)

        # Mode Indicator
        self.mode_label = Label(
            text="CHOOSE A MODE",
            font_size='18sp',
            bold=True,
            color=(0.8, 0.8, 0.8, 1),
            size_hint=(1, 0.06)
        )
        self.main_layout.add_widget(self.mode_label)

        # Game Canvas Area
        self.circle_widget = CircleWidget(size_hint=(1, 0.45))
        self.main_layout.add_widget(self.circle_widget)

        # Color Name Overlay inside Ball
        self.word_label = Label(text="", font_size='24sp', bold=True, color=(1, 1, 1, 1), size_hint=(1, 0.05))
        self.main_layout.add_widget(self.word_label)

        # Buttons Panel (Raised Upwards)
        self.controls_layout = FloatLayout(size_hint=(1, 0.30))
        self.main_layout.add_widget(self.controls_layout)

        self.show_mode_selection()
        return self.main_layout

    def load_best_score(self):
        try:
            with open("best_score.txt", "r") as f:
                return int(f.read())
        except:
            return 0

    def save_best_score(self):
        try:
            with open("best_score.txt", "w") as f:
                f.write(str(self.best_score))
        except:
            pass

    def show_mode_selection(self):
        self.controls_layout.clear_widgets()
        grid = GridLayout(cols=2, spacing=15, size_hint=(0.8, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.5})

        btn_easy = Button(text="EASY", font_size='20sp', background_color=(0.2, 0.8, 0.4, 1), bold=True)
        btn_easy.bind(on_release=lambda x: self.choose_easy_mode())

        btn_hard = Button(text="HARD", font_size='20sp', background_color=(0.9, 0.2, 0.3, 1), bold=True)
        btn_hard.bind(on_release=lambda x: self.start_game("HARD"))

        grid.add_widget(btn_easy)
        grid.add_widget(btn_hard)
        self.controls_layout.add_widget(grid)

    def choose_easy_mode(self):
        self.game_mode = "EASY"
        self.mode_label.text = "EASY: CHOOSE COLOR OR WORD"
        self.controls_layout.clear_widgets()

        grid = GridLayout(cols=2, spacing=15, size_hint=(0.8, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.5})

        btn_color = Button(text="COLOR", font_size='18sp', background_color=(0.2, 0.6, 1.0, 1), bold=True)
        btn_color.bind(on_release=lambda x: self.select_easy_submode("COLOR"))

        btn_word = Button(text="WORD", font_size='18sp', background_color=(1.0, 0.6, 0.2, 1), bold=True)
        btn_word.bind(on_release=lambda x: self.select_easy_submode("WORD"))

        grid.add_widget(btn_color)
        grid.add_widget(btn_word)
        self.controls_layout.add_widget(grid)

    def select_easy_submode(self, mode):
        self.easy_mode = mode
        self.mode_label.text = f"EASY - {mode}"
        self.start_game("EASY")

    def start_game(self, mode):
        self.game_mode = mode
        self.score = 0
        self.correct_count = 0
        self.score_label.text = "Score: 0"
        self.setup_game_buttons()
        self.new_round()

    def setup_game_buttons(self):
        self.controls_layout.clear_widgets()
        grid = GridLayout(cols=2, spacing=10, size_hint=(0.9, 0.85), pos_hint={'center_x': 0.5, 'center_y': 0.55})

        self.answer_buttons = {}
        for name in COLOR_NAMES:
            btn = Button(
                text=name,
                font_size='18sp',
                bold=True,
                background_color=COLORS[name]
            )
            btn.bind(on_release=lambda instance, n=name: self.check_answer(n))
            self.answer_buttons[name] = btn
            grid.add_widget(btn)

        self.controls_layout.add_widget(grid)

    def new_round(self, *args):
        if self.timer_event:
            self.timer_event.cancel()

        self.time_left = max(2, 5 - (self.correct_count // 10))
        self.timer_label.text = f"Time: {self.time_left}"

        actual_color = random.choice(COLOR_NAMES)
        word_color = random.choice(COLOR_NAMES)

        if self.game_mode == "EASY":
            current_mode = self.easy_mode
        else:
            current_mode = random.choice(["COLOR", "WORD"])

        self.circle_widget.set_color(COLORS[actual_color])
        self.word_label.text = word_color

        if current_mode == "COLOR":
            self.mode_label.text = "MATCH BALL COLOR!"
            self.correct_answer = actual_color
        else:
            self.mode_label.text = "MATCH WRITTEN WORD!"
            self.correct_answer = word_color

        self.timer_event = Clock.schedule_interval(self.countdown, 1.0)

    def countdown(self, dt):
        self.time_left -= 1
        self.timer_label.text = f"Time: {self.time_left}"

        if self.time_left <= 0:
            if self.timer_event:
                self.timer_event.cancel()
            self.game_over("TIME'S UP!")

    def check_answer(self, answer):
        if self.timer_event:
            self.timer_event.cancel()

        if answer == self.correct_answer:
            self.correct_count += 1
            self.score += 1 if self.game_mode == "EASY" else 10
            self.score_label.text = f"Score: {self.score}"

            if self.score > self.best_score:
                self.best_score = self.score
                self.best_label.text = f"Best: {self.best_score}"
                self.save_best_score()

            Clock.schedule_once(self.new_round, 0.2)
        else:
            self.game_over("WRONG ANSWER!")

    def game_over(self, reason):
        if self.timer_event:
            self.timer_event.cancel()

        self.controls_layout.clear_widgets()
        layout = BoxLayout(orientation='vertical', spacing=10, size_hint=(0.8, 0.8), pos_hint={'center_x': 0.5, 'center_y': 0.5})

        lbl_reason = Label(text=reason, font_size='22sp', bold=True, color=(1, 0.2, 0.2, 1))
        lbl_score = Label(text=f"Final Score: {self.score}", font_size='18sp')

        btn_retry = Button(text="PLAY AGAIN", font_size='20sp', bold=True, background_color=(0.2, 0.8, 0.4, 1))
        btn_retry.bind(on_release=lambda x: self.reset_game())

        layout.add_widget(lbl_reason)
        layout.add_widget(lbl_score)
        layout.add_widget(btn_retry)

        self.controls_layout.add_widget(layout)

    def reset_game(self):
        self.mode_label.text = "CHOOSE A MODE"
        self.word_label.text = ""
        self.circle_widget.set_color((0.07, 0.07, 0.09, 1))
        self.show_mode_selection()

if __name__ == "__main__":
    HueStrikeApp().run()
            
