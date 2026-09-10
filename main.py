import random
import json
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse
from kivy.clock import Clock
from kivy.core.window import Window

Window.clearcolor = (0.07, 0.07, 0.09, 1)

COLORS = {
    "RED": (1.0, 0.2, 0.3, 1),
    "BLUE": (0.2, 0.5, 1.0, 1),
    "GREEN": (0.2, 0.8, 0.4, 1),
    "YELLOW": (1.0, 0.8, 0.1, 1),
    "PURPLE": (0.7, 0.3, 0.9, 1),
    "ORANGE": (1.0, 0.5, 0.1, 1),
    "CYAN": (0.1, 0.9, 0.9, 1),
    "PINK": (1.0, 0.4, 0.7, 1)
}

COLOR_NAMES = list(COLORS.keys())

class CircleWidget(Widget):
    def __init__(self, **kwargs):
        super(CircleWidget, self).__init__(**kwargs)
        self.circle_color = (1, 1, 1, 1)
        self.text = ""
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def set_data(self, color_tuple, text_str):
        self.circle_color = color_tuple
        self.text = text_str
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(*self.circle_color)
            # Reduced circle diameter to fit inside properly
            size = min(self.width, self.height) * 0.65
            x = self.center_x - size / 2
            y = self.center_y - size / 2
            Ellipse(pos=(x, y), size=(size, size))

class HueStrikeApp(App):
    def build(self):
        self.title = "Hue Strike"
        self.score = 0
        self.correct_count = 0
        self.time_left = 5
        self.game_mode = ""
        self.easy_mode = ""
        self.timer_event = None
        self.scores_data = self.load_scores()

        self.main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

        # Title
        self.title_label = Label(
            text="HUE STRIKE",
            font_size='28sp',
            bold=True,
            color=(0.1, 0.9, 0.9, 1),
            size_hint=(1, 0.08)
        )
        self.main_layout.add_widget(self.title_label)

        # Top Bar (Score & Timer)
        self.info_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.06))
        self.score_label = Label(text="Score: 0", font_size='18sp', color=(1, 1, 1, 1))
        self.timer_label = Label(text="Time: 5", font_size='18sp', color=(1, 0.3, 0.3, 1))
        self.info_layout.add_widget(self.score_label)
        self.info_layout.add_widget(self.timer_label)
        self.main_layout.add_widget(self.info_layout)

        # Game Canvas (Circle Container)
        self.circle_container = FloatLayout(size_hint=(1, 0.38))
        self.circle_widget = CircleWidget(size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.circle_container.add_widget(self.circle_widget)
        
        # Word text inside Circle
        self.word_label = Label(
            text="", font_size='32sp', bold=True,
            color=(1, 1, 1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.circle_container.add_widget(self.word_label)
        self.main_layout.add_widget(self.circle_container)

        # Instruction Below Ball
        self.mode_label = Label(
            text="", font_size='20sp', bold=True,
            color=(1, 0.9, 0.2, 1), size_hint=(1, 0.08)
        )
        self.main_layout.add_widget(self.mode_label)

        # Interactive Area (Buttons)
        self.controls_layout = FloatLayout(size_hint=(1, 0.40))
        self.main_layout.add_widget(self.controls_layout)

        self.show_main_menu()
        return self.main_layout

    def load_scores(self):
        try:
            with open("best_scores.json", "r") as f:
                return json.load(f)
        except:
            return {"EASY": 0, "HARD": 0}

    def save_scores(self):
        try:
            with open("best_scores.json", "w") as f:
                json.dump(self.scores_data, f)
        except:
            pass

    def show_main_menu(self):
        self.controls_layout.clear_widgets()
        self.mode_label.text = ""
        self.word_label.text = ""
        self.circle_widget.set_data((0.07, 0.07, 0.09, 1), "")

        layout = BoxLayout(orientation='vertical', spacing=10, size_hint=(0.85, 0.9), pos_hint={'center_x': 0.5, 'center_y': 0.5})

        btn_easy = Button(text="EASY MODE", font_size='18sp', bold=True, background_color=(0.2, 0.8, 0.4, 1))
        btn_easy.bind(on_release=lambda x: self.choose_easy_mode())

        btn_hard = Button(text="HARD MODE", font_size='18sp', bold=True, background_color=(0.9, 0.2, 0.3, 1))
        btn_hard.bind(on_release=lambda x: self.start_game("HARD"))

        btn_instructions = Button(text="GAME INSTRUCTIONS", font_size='16sp', bold=True, background_color=(0.2, 0.6, 1.0, 1))
        btn_instructions.bind(on_release=lambda x: self.show_instructions_popup())

        btn_best_score = Button(text="BEST SCORE", font_size='16sp', bold=True, background_color=(1.0, 0.6, 0.1, 1))
        btn_best_score.bind(on_release=lambda x: self.show_best_score_popup())

        layout.add_widget(btn_easy)
        layout.add_widget(btn_hard)
        layout.add_widget(btn_instructions)
        layout.add_widget(btn_best_score)

        self.controls_layout.add_widget(layout)

    def show_instructions_popup(self):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        text = (
            "[b]HUE STRIKE INSTRUCTIONS[/b]\n\n"
            "1. [color=3388ff]EASY MODE:[/color] Choose either Color or Word matching.\n"
            "2. [color=ff3333]HARD MODE:[/color] Check instruction below the ball!\n"
            "   - 'MATCH BALL COLOR': Tap button with Ball's color.\n"
            "   - 'MATCH WRITTEN WORD': Tap button matching the text inside.\n\n"
            "3. Beat the timer before it hits zero!"
        )
        lbl = Label(text=text, markup=True, font_size='14sp', halign='center')
        btn = Button(text="CLOSE", size_hint=(1, 0.2), bold=True)

        content.add_widget(lbl)
        content.add_widget(btn)

        popup = Popup(title="Instructions", content=content, size_hint=(0.9, 0.6))
        btn.bind(on_release=popup.dismiss)
        popup.open()

    def show_best_score_popup(self):
        content = BoxLayout(orientation='vertical', padding=15, spacing=15)
        text = (
            f"[size=20sp][b]HIGH SCORES[/b][/size]\n\n"
            f"[color=33ff88]EASY MODE:[/color] {self.scores_data.get('EASY', 0)}\n"
            f"[color=ff3366]HARD MODE:[/color] {self.scores_data.get('HARD', 0)}"
        )
        lbl = Label(text=text, markup=True, font_size='18sp', halign='center')
        btn = Button(text="CLOSE", size_hint=(1, 0.25), bold=True)

        content.add_widget(lbl)
        content.add_widget(btn)

        popup = Popup(title="Best Scores", content=content, size_hint=(0.8, 0.45))
        btn.bind(on_release=popup.dismiss)
        popup.open()

    def choose_easy_mode(self):
        self.controls_layout.clear_widgets()
        layout = BoxLayout(orientation='vertical', spacing=10, size_hint=(0.85, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.5})

        self.mode_label.text = "EASY: CHOOSE SUB-MODE"

        btn_color = Button(text="MATCH COLOR", font_size='18sp', bold=True, background_color=(0.2, 0.6, 1.0, 1))
        btn_color.bind(on_release=lambda x: self.select_easy_submode("COLOR"))

        btn_word = Button(text="MATCH WORD", font_size='18sp', bold=True, background_color=(1.0, 0.6, 0.2, 1))
        btn_word.bind(on_release=lambda x: self.select_easy_submode("WORD"))

        layout.add_widget(btn_color)
        layout.add_widget(btn_word)
        self.controls_layout.add_widget(layout)

    def select_easy_submode(self, mode):
        self.easy_mode = mode
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
        grid = GridLayout(cols=4, spacing=8, size_hint=(0.98, 0.85), pos_hint={'center_x': 0.5, 'center_y': 0.55})

        self.answer_buttons = {}
        for name in COLOR_NAMES:
            btn = Button(
                text=name,
                font_size='12sp',
                bold=True,
                background_color=COLORS[name]
            )
            btn.bind(on_release=lambda instance, n=name: self.check_answer(n))
            self.answer_buttons[name] = btn
            grid.add_widget(btn)

        self.controls_layout.add_widget(grid)

    def calculate_time(self):
        # Time logic configuration
        if self.game_mode == "EASY":
            if self.correct_count <= 10: return 5
            elif self.correct_count <= 20: return 4
            elif self.correct_count <= 30: return 3
            elif self.correct_count <= 40: return 2
            else: return 1
        else: # HARD Mode
            if self.correct_count <= 15: return 5
            elif self.correct_count <= 30: return 4
            elif self.correct_count <= 45: return 3
            elif self.correct_count <= 60: return 2
            else: return 1

    def new_round(self, *args):
        if self.timer_event:
            self.timer_event.cancel()

        self.time_left = self.calculate_time()
        self.timer_label.text = f"Time: {self.time_left}"

        actual_color = random.choice(COLOR_NAMES)
        word_color = random.choice(COLOR_NAMES)

        if self.game_mode == "EASY":
            current_mode = self.easy_mode
        else:
            current_mode = random.choice(["COLOR", "WORD"])

        self.circle_widget.set_data(COLORS[actual_color], word_color)
        self.word_label.text = word_color

        # Instruction positioned cleanly under color ball
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

            # High Score Update Logic
            current_best = self.scores_data.get(self.game_mode, 0)
            if self.score > current_best:
                self.scores_data[self.game_mode] = self.score
                self.save_scores()

            Clock.schedule_once(self.new_round, 0.15)
        else:
            self.game_over("WRONG ANSWER!")

    def game_over(self, reason):
        if self.timer_event:
            self.timer_event.cancel()

        self.controls_layout.clear_widgets()
        layout = BoxLayout(orientation='vertical', spacing=10, size_hint=(0.85, 0.85), pos_hint={'center_x': 0.5, 'center_y': 0.5})

        lbl_reason = Label(text=reason, font_size='22sp', bold=True, color=(1, 0.2, 0.2, 1))
        lbl_score = Label(text=f"Score: {self.score}", font_size='18sp')

        btn_retry = Button(text="PLAY AGAIN", font_size='18sp', bold=True, background_color=(0.2, 0.8, 0.4, 1))
        btn_retry.bind(on_release=lambda x: self.start_game(self.game_mode))

        btn_menu = Button(text="MAIN MENU", font_size='16sp', bold=True, background_color=(0.2, 0.6, 1.0, 1))
        btn_menu.bind(on_release=lambda x: self.show_main_menu())

        layout.add_widget(lbl_reason)
        layout.add_widget(lbl_score)
        layout.add_widget(btn_retry)
        layout.add_widget(btn_menu)

        self.controls_layout.add_widget(layout)

if __name__ == "__main__":
    HueStrikeApp().run()
        
