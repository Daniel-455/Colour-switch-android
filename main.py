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
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Ellipse
from kivy.clock import Clock
from kivy.core.window import Window

Window.clearcolor = (0.07, 0.07, 0.09, 1)

# Circle மற்றும் Buttons இரண்டிற்கும் ஒரே சீரான வண்ணங்கள் (Exact Bright Colors)
COLORS = {
    "RED": (1.0, 0.2, 0.2, 1),
    "BLUE": (0.1, 0.5, 1.0, 1),
    "GREEN": (0.1, 0.8, 0.3, 1),
    "YELLOW": (1.0, 0.85, 0.0, 1),
    "PURPLE": (0.7, 0.2, 0.9, 1),
    "ORANGE": (1.0, 0.5, 0.0, 1),
    "CYAN": (0.0, 0.85, 1.0, 1),
    "PINK": (1.0, 0.3, 0.7, 1)
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

        # Top Bar (Score, Best, Time)
        self.info_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.06))
        self.score_label = Label(text="Score: 0", font_size='15sp', color=(1, 1, 1, 1))
        self.best_label = Label(text="Best: 0", font_size='15sp', color=(1, 0.8, 0.2, 1))
        self.timer_label = Label(text="Time: 5", font_size='15sp', color=(1, 0.3, 0.3, 1))
        
        self.info_layout.add_widget(self.score_label)
        self.info_layout.add_widget(self.best_label)
        self.info_layout.add_widget(self.timer_label)
        self.main_layout.add_widget(self.info_layout)

        # Game Canvas
        self.circle_container = FloatLayout(size_hint=(1, 0.38))
        self.circle_widget = CircleWidget(size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.circle_container.add_widget(self.circle_widget)
        
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

        # Controls Layout
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
        self.best_label.text = "Best: -"

        layout = BoxLayout(orientation='vertical', spacing=10, size_hint=(0.85, 0.9), pos_hint={'center_x': 0.5, 'center_y': 0.5})

        btn_easy = Button(text="EASY MODE", font_size='18sp', bold=True, background_color=(0.2, 0.8, 0.4, 1), background_normal='')
        btn_easy.bind(on_release=lambda x: self.choose_easy_mode())

        btn_hard = Button(text="HARD MODE", font_size='18sp', bold=True, background_color=(0.9, 0.2, 0.3, 1), background_normal='')
        btn_hard.bind(on_release=lambda x: self.start_game("HARD"))

        btn_instructions = Button(text="GAME INSTRUCTIONS", font_size='16sp', bold=True, background_color=(0.2, 0.6, 1.0, 1), background_normal='')
        btn_instructions.bind(on_release=lambda x: self.show_instructions_popup())

        btn_best_score = Button(text="BEST SCORE", font_size='16sp', bold=True, background_color=(1.0, 0.6, 0.1, 1), background_normal='')
        btn_best_score.bind(on_release=lambda x: self.show_best_score_popup())

        layout.add_widget(btn_easy)
        layout.add_widget(btn_hard)
        layout.add_widget(btn_instructions)
        layout.add_widget(btn_best_score)

        self.controls_layout.add_widget(layout)

    def show_instructions_popup(self):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        scroll = ScrollView(size_hint=(1, 0.8))
        text = (
            "[b]HUE STRIKE INSTRUCTIONS[/b]\n\n"
            "1. [color=3388ff]EASY MODE:[/color]\nChoose MATCH COLOR or MATCH WORD.\n\n"
            "2. [color=ff3333]HARD MODE:[/color]\nCheck instruction below ball:\n"
            " - 'MATCH BALL COLOR': Tap button matching Ball color.\n"
            " - 'MATCH WRITTEN WORD': Tap button matching text inside.\n\n"
            "3. [color=ffcc00]TIME RULES:[/color]\n"
            " [b]Easy:[/b] 0-10 (5s) -> 11-20 (4s) -> 21-30 (3s) -> 31-40 (2s) -> 40+ (1s)\n"
            " [b]Hard:[/b] 0-15 (5s) -> 16-30 (4s) -> 31-45 (3s) -> 46-60 (2s) -> 60+ (1s)"
        )
        lbl = Label(text=text, markup=True, font_size='14sp', size_hint_y=None, halign='left', valign='top')
        lbl.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
        lbl.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        
        scroll.add_widget(lbl)
        btn = Button(text="CLOSE", size_hint=(1, 0.18), bold=True)

        content.add_widget(scroll)
        content.add_widget(btn)

        popup = Popup(title="Instructions", content=content, size_hint=(0.9, 0.75))
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

        btn_color = Button(text="MATCH COLOR", font_size='18sp', bold=True, background_color=(0.2, 0.6, 1.0, 1), background_normal='')
        btn_color.bind(on_release=lambda x: self.select_easy_submode("COLOR"))

        btn_word = Button(text="MATCH WORD", font_size='18sp', bold=True, background_color=(1.0, 0.6, 0.2, 1), background_normal='')
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
        self.best_label.text = f"Best: {self.scores_data.get(mode, 0)}"
        self.setup_game_buttons()
        self.new_round()

    def setup_game_buttons(self):
        self.controls_layout.clear_widgets()
        grid = GridLayout(cols=4, spacing=8, size_hint=(0.98, 0.85), pos_hint={'center_x': 0.5, 'center_y': 0.55})

        self.answer_buttons = {}
        for name in COLOR_NAMES:
            btn = Button(
                text=name,
                font_size='11sp',
                bold=True,
                background_normal='',  # Default gray image removal for pure exact color
                background_color=COLORS[name]
            )
            btn.bind(on_release=lambda instance, n=name: self.check_answer(n))
            self.answer_buttons[name] = btn
            grid.add_widget(btn)

        self.controls_layout.add_widget(grid)

    def calculate_time(self):
        if self.game_mode == "EASY":
            if self.correct_count <= 10: return 5
            elif self.correct_count <= 20: return 4
            elif self.correct_count <= 30: return 3
            elif self.correct_count <= 40: return 2
            else: return 1
        else:
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
            self.trigger_game_over("TIME'S UP!")

    def check_answer(self, answer):
        if self.timer_event:
            self.timer_event.cancel()

        if answer == self.correct_answer:
            self.correct_count += 1
            self.score += 1 if self.game_mode == "EASY" else 10
            self.score_label.text = f"Score: {self.score}"

            current_best = self.scores_data.get(self.game_mode, 0)
            if self.score > current_best:
                self.scores_data[self.game_mode] = self.score
                self.best_label.text = f"Best: {self.score}"
                self.save_scores()

            Clock.schedule_once(self.new_round, 0.15)
        else:
            self.trigger_game_over("WRONG ANSWER!")

    def trigger_game_over(self, reason):
        # 4 Times Red Screen Blink Animation
        def blink(count):
            if count >= 8:  # 4 complete blinks (red on/off x 4)
                Window.clearcolor = (0.07, 0.07, 0.09, 1)
                self.game_over(reason)
                return
            if count % 2 == 0:
                Window.clearcolor = (0.7, 0.05, 0.05, 1)
            else:
                Window.clearcolor = (0.07, 0.07, 0.09, 1)
            Clock.schedule_once(lambda dt: blink(count + 1), 0.1)

        blink(0)

    def game_over(self, reason):
        if self.timer_event:
            self.timer_event.cancel()

        self.controls_layout.clear_widgets()
        layout = BoxLayout(orientation='vertical', spacing=10, size_hint=(0.85, 0.85), pos_hint={'center_x': 0.5, 'center_y': 0.5})

        lbl_reason = Label(text=reason, font_size='22sp', bold=True, color=(1, 0.2, 0.2, 1))
        lbl_score = Label(text=f"Score: {self.score}", font_size='18sp')

        btn_retry = Button(text="PLAY AGAIN", font_size='18sp', bold=True, background_color=(0.2, 0.8, 0.4, 1), background_normal='')
        btn_retry.bind(on_release=lambda x: self.start_game(self.game_mode))

        btn_menu = Button(text="MAIN MENU", font_size='16sp', bold=True, background_color=(0.2, 0.6, 1.0, 1), background_normal='')
        btn_menu.bind(on_release=lambda x: self.show_main_menu())

        layout.add_widget(lbl_reason)
        layout.add_widget(lbl_score)
        layout.add_widget(btn_retry)
        layout.add_widget(btn_menu)

        self.controls_layout.add_widget(layout)

if __name__ == "__main__":
    HueStrikeApp().run()
        
