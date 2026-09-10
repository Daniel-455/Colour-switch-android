import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Ellipse
from kivy.clock import Clock
from kivy.core.window import Window

# Screen size adjustment for mobile view
Window.clearcolor = (0.1, 0.1, 0.1, 1)

COLOR_MAP = {
    "RED": (1, 0, 0, 1),
    "GREEN": (0, 1, 0, 1),
    "BLUE": (0, 0.5, 1, 1),
    "YELLOW": (1, 1, 0, 1),
    "ORANGE": (1, 0.5, 0, 1),
    "PURPLE": (0.6, 0.1, 0.9, 1)
}

COLOR_NAMES = list(COLOR_MAP.keys())

class ColorSwitchGame(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=15, padding=20, **kwargs)
        
        self.score = 0
        self.time_left = 30
        self.target_color_name = ""
        self.display_text = ""
        self.text_color_rgb = (1, 1, 1, 1)

        # Top Bar: Score and Timer
        top_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        self.score_label = Label(text="Score: 0", font_size='22sp', bold=True)
        self.timer_label = Label(text="Time: 30s", font_size='22sp', bold=True)
        top_bar.add_widget(self.score_label)
        top_bar.add_widget(self.timer_label)
        self.add_widget(top_bar)

        # Circle Display Area with Large Text Overlay
        self.circle_container = BoxLayout(size_hint=(1, 0.5), orientation='vertical')
        self.circle_label = Label(text="", font_size='36sp', bold=True, halign='center', valign='middle')
        self.circle_container.bind(pos=self.update_circle, size=self.update_circle)
        self.circle_container.add_widget(self.circle_label)
        self.add_widget(self.circle_container)

        # Instruction Label
        self.instruction_label = Label(
            text="Tap the color matching the TEXT word!", 
            font_size='16sp', 
            size_hint=(1, 0.08),
            color=(0.8, 0.8, 0.8, 1)
        )
        self.add_widget(self.instruction_label)

        # Bottom Grid for Bigger Color Buttons
        self.buttons_grid = GridLayout(cols=2, spacing=15, size_hint=(1, 0.32))
        self.color_buttons = {}
        
        for name in COLOR_NAMES:
            btn = Button(
                text=name, 
                font_size='20sp', 
                bold=True, 
                background_normal='', 
                background_color=COLOR_MAP[name]
            )
            btn.bind(on_release=self.check_answer)
            self.buttons_grid.add_widget(btn)
            self.color_buttons[name] = btn

        self.add_widget(self.buttons_grid)

        # Start Game Loop
        self.next_round()
        Clock.schedule_interval(self.update_timer, 1)

    def update_circle(self, *args):
        self.circle_container.canvas.before.clear()
        with self.circle_container.canvas.before:
            # Draw Circle In Background
            Color(*self.text_color_rgb)
            size = min(self.circle_container.width, self.circle_container.height) * 0.85
            x = self.circle_container.center_x - size / 2
            y = self.circle_container.center_y - size / 2
            Ellipse(pos=(x, y), size=(size, size))

    def next_round(self):
        # Pick Random Target Color and Fake Text
        self.target_color_name = random.choice(COLOR_NAMES)
        self.display_text = random.choice(COLOR_NAMES)
        
        # Background Circle Color
        self.text_color_rgb = COLOR_MAP[self.target_color_name]
        
        # Center Text - Contrast Color for Visibility (Black or White)
        if self.target_color_name in ["YELLOW", "GREEN"]:
            self.circle_label.color = (0, 0, 0, 1)
        else:
            self.circle_label.color = (1, 1, 1, 1)

        self.circle_label.text = self.display_text
        self.update_circle()

    def check_answer(self, instance):
        if instance.text == self.display_text:
            self.score += 10
        else:
            self.score = max(0, self.score - 5)
        
        self.score_label.text = f"Score: {self.score}"
        self.next_round()

    def update_timer(self, dt):
        if self.time_left > 0:
            self.time_left -= 1
            self.timer_label.text = f"Time: {self.time_left}s"
        else:
            self.circle_label.text = "GAME OVER"
            self.circle_label.color = (1, 0, 0, 1)
            self.buttons_grid.disabled = True
            return False

class ColorApp(App):
    def build(self):
        return ColorSwitchGame()

if __name__ == '__main__':
    ColorApp().run()
