import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.storage.jsonstore import JsonStore

Window.clearcolor = (1, 1, 1, 1)

COLOR_MAP = {
    "RED": (1, 0.2, 0.2, 1),
    "BLUE": (0.2, 0.4, 1, 1),
    "GREEN": (0.13, 0.66, 0.33, 1),
    "YELLOW": (0.9, 0.77, 0, 1)
}

COLOR_NAMES = ["RED", "BLUE", "GREEN", "YELLOW"]

class HueStrikeGame(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=5, **kwargs)

        self.store = JsonStore('best_score.json')
        self.best_score = self.store.get('score')['best'] if self.store.exists('score') else 0

        self.score = 0
        self.correct_count = 0
        self.time_left = 5
        self.game_mode = ""
        self.easy_mode = ""
        self.timer_event = None
        self.correct_answer = ""
        self.bg_color = (1, 1, 1, 1)

        # Background canvas setup
        with self.canvas.before:
            self.bg_canvas_color = Color(*self.bg_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

        # Header Title
        self.title_label = Label(text="Hue strike", font_size='22sp', bold=True, color=(0, 0, 0, 1), size_hint=(1, 0.08))
        self.add_widget(self.title_label)

        # Score, Best, Timer
        self.score_label = Label(text="Score: 0", font_size='14sp', bold=True, color=(0, 0, 0, 1), size_hint=(1, 0.04))
        self.best_label = Label(text=f"Best: {self.best_score}", font_size='14sp', bold=True, color=(0, 0, 0, 1), size_hint=(1, 0.04))
        self.timer_label = Label(text="Time: 5", font_size='14sp', bold=True, color=(0, 0, 0, 1), size_hint=(1, 0.04))

        self.add_widget(self.score_label)
        self.add_widget(self.best_label)
        self.add_widget(self.timer_label)

        # Mode Selection Label
        self.mode_label = Label(text="Choose a mode", font_size='13sp', bold=True, color=(0, 0, 0, 1), size_hint=(1, 0.05))
        self.add_widget(self.mode_label)

        # Mode Selection Buttons (EASY / HARD)
        self.mode_frame = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.1), padding=[50, 0])
        self.btn_easy = Button(text="EASY", font_size='14sp', bold=True, on_release=lambda x: self.start_game("EASY"))
        self.btn_hard = Button(text="HARD", font_size='14sp', bold=True, on_release=lambda x: self.start_game("HARD"))
        self.mode_frame.add_widget(self.btn_easy)
        self.mode_frame.add_widget(self.btn_hard)
        self.add_widget(self.mode_frame)

        # Easy Sub-Choice Frame (COLOR / WORD)
        self.easy_choice_frame = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.1), padding=[50, 0])
        self.btn_easy_color = Button(text="COLOR", font_size='14sp', bold=True, on_release=lambda x: self.select_easy_mode("COLOR"))
        self.btn_easy_word = Button(text="WORD", font_size='14sp', bold=True, on_release=lambda x: self.select_easy_mode("WORD"))
        self.easy_choice_frame.add_widget(self.btn_easy_color)
        self.easy_choice_frame.add_widget(self.btn_easy_word)

        # Game Play Area
        self.game_frame = BoxLayout(orientation='vertical', spacing=5, size_hint=(1, 0.65))
        self.circle_container = BoxLayout(size_hint=(1, 0.6))
        self.circle_label = Label(text="", font_size='12sp', bold=True, color=(1, 1, 1, 1), halign='center', valign='middle')
        self.circle_container.add_widget(self.circle_label)
        self.circle_container.bind(pos=self.update_circle, size=self.update_circle)

        self.instruction_label = Label(text="", font_size='14sp', bold=True, color=(0, 0, 0, 1), size_hint=(1, 0.08))

        # Answer Grid
        self.answer_frame = GridLayout(cols=2, spacing=8, size_hint=(1, 0.32), padding=[20, 0])
        self.answer_buttons = {}
        for name in COLOR_NAMES:
            btn = Button(text=name, font_size='12sp', bold=True, on_release=self.check_answer)
            self.answer_buttons[name] = btn
            self.answer_frame.add_widget(btn)

        self.game_frame.add_widget(self.circle_container)
        self.game_frame.add_widget(self.instruction_label)
        self.game_frame.add_widget(self.answer_frame)

        # Game Over Area
        self.game_over_frame = BoxLayout(orientation='vertical', spacing=10, size_hint=(1, 0.5))
        self.go_title = Label(text="GAME OVER", font_size='24sp', bold=True, color=(0, 0, 0, 1))
        self.go_reason = Label(text="", font_size='15sp', bold=True, color=(0, 0, 0, 1))
        self.go_score = Label(text="", font_size='16sp', bold=True, color=(0, 0, 0, 1))
        self.go_best = Label(text="", font_size='15sp', bold=True, color=(0, 0, 0, 1))
        self.btn_play_again = Button(text="PLAY AGAIN", font_size='14sp', bold=True, size_hint=(0.6, 0.2), pos_hint={'center_x': 0.5}, on_release=self.reset_game)

        self.game_over_frame.add_widget(self.go_title)
        self.game_over_frame.add_widget(self.go_reason)
        self.game_over_frame.add_widget(self.go_score)
        self.game_over_frame.add_widget(self.go_best)
        self.game_over_frame.add_widget(self.btn_play_again)

        self.actual_color = "RED"

    def update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def set_bg_color(self, color):
        self.bg_canvas_color.rgba = color

    def update_circle(self, *args):
        self.circle_container.canvas.before.clear()
        with self.circle_container.canvas.before:
            Color(*COLOR_MAP[self.actual_color])
            size = min(self.circle_container.width, self.circle_container.height) * 0.85
            x = self.circle_container.center_x - size / 2
            y = self.circle_container.center_y - size / 2
            Ellipse(pos=(x, y), size=(size, size))

    def start_game(self, mode):
        self.score = 0
        self.correct_count = 0
        self.time_left = 5
        self.game_mode = mode

        self.score_label.text = "Score: 0"
        self.timer_label.text = "Time: 5"

        self.remove_widget(self.mode_frame)
        if self.easy_choice_frame in self.children:
            self.remove_widget(self.easy_choice_frame)
        if self.game_over_frame in self.children:
            self.remove_widget(self.game_over_frame)

        if mode == "EASY":
            self.mode_label.text = "EASY: Choose COLOR or WORD"
            self.add_widget(self.easy_choice_frame)
        else:
            self.mode_label.text = "HARD - COLOR or WORD changes"
            self.show_game()

    def select_easy_mode(self, mode):
        self.easy_mode = mode
        self.remove_widget(self.easy_choice_frame)
        self.mode_label.text = "EASY - " + mode
        self.show_game()

    def show_game(self):
        if self.game_frame not in self.children:
            self.add_widget(self.game_frame)
        self.new_round()

    def new_round(self):
        if self.timer_event:
            self.timer_event.cancel()

        for btn in self.answer_buttons.values():
            btn.disabled = False

        self.time_left = max(2, 5 - (self.correct_count // 10))
        self.timer_label.text = f"Time: {self.time_left}"

        self.actual_color = random.choice(COLOR_NAMES)
        word_color = random.choice(COLOR_NAMES)

        current_mode = self.easy_mode if self.game_mode == "EASY" else random.choice(["COLOR", "WORD"])

        self.update_circle()
        self.circle_label.text = word_color

        if current_mode == "COLOR":
            self.instruction_label.text = "CHOOSE BALL COLOR"
            self.correct_answer = self.actual_color
        else:
            self.instruction_label.text = "CHOOSE WORD"
            self.correct_answer = word_color

        self.timer_event = Clock.schedule_interval(self.countdown, 1)

    def countdown(self, dt):
        self.time_left -= 1
        self.timer_label.text = f"Time: {self.time_left}"

        if self.time_left <= 0:
            if self.timer_event:
                self.timer_event.cancel()
            for btn in self.answer_buttons.values():
                btn.disabled = True
            self.game_over("TIME'S UP!")

    def check_answer(self, instance):
        if self.timer_event:
            self.timer_event.cancel()

        for btn in self.answer_buttons.values():
            btn.disabled = True

        answer = instance.text
        if answer == self.correct_answer:
            self.correct_count += 1
            self.score += 1 if self.game_mode == "EASY" else 10
            self.score_label.text = f"Score: {self.score}"

            if self.score > self.best_score:
                self.best_score = self.score
                self.best_label.text = f"Best: {self.best_score}"
                self.store.put('score', best=self.best_score)

            Clock.schedule_once(lambda dt: self.new_round(), 0.3)
        else:
            self.score -= 1 if self.game_mode == "EASY" else 5
            if self.score < 0:
                self.score = 0
            self.score_label.text = f"Score: {self.score}"
            self.game_over("WRONG ANSWER!")

    def game_over(self, reason):
        if self.timer_event:
            self.timer_event.cancel()

        if self.game_frame in self.children:
            self.remove_widget(self.game_frame)

        self.go_reason.text = reason
        self.go_score.text = f"Your Score: {self.score}"
        self.go_best.text = f"Best Score: {self.best_score}"

        if self.game_over_frame not in self.children:
            self.add_widget(self.game_over_frame)

        self.blink(0)

    def blink(self, count):
        if count >= 6:
            self.set_bg_color((1, 1, 1, 1))
            return

        if count % 2 == 0:
            self.set_bg_color((1, 0, 0, 1))
        else:
            self.set_bg_color((1, 1, 1, 1))

        Clock.schedule_once(lambda dt: self.blink(count + 1), 0.12)

    def reset_game(self, instance):
        if self.timer_event:
            self.timer_event.cancel()

        self.score = 0
        self.correct_count = 0
        self.time_left = 5

        self.score_label.text = "Score: 0"
        self.timer_label.text = "Time: 5"

        if self.game_over_frame in self.children:
            self.remove_widget(self.game_over_frame)
        if self.game_frame in self.children:
            self.remove_widget(self.game_frame)

        self.set_bg_color((1, 1, 1, 1))
        self.mode_label.text = "Choose a mode"

        if self.mode_frame not in self.children:
            self.add_widget(self.mode_frame)

class HueStrikeApp(App):
    def build(self):
        return HueStrikeGame()

if __name__ == '__main__':
    HueStrikeApp().run()
        
