from aoslib.scenes import Scene, ElementScene, MenuScene
from aoslib.images import global_images
from aoslib.gui import TextButton, create_large_navbar
from aoslib.media import HUD_AUDIO_ZONE
from aoslib.text import draw_text_with_size_validation, title_font
from shared.constants import MENU_FONT_COLOR
from pyglet import gl

class ListPreviewMenuBase(MenuScene):

    def initialize(self, title):
        self.elements = []
        self.title = title
        self.list_panel = None
        self.preview_panel = None
        self.navigation_bar = create_large_navbar()
        self.navigation_bar.add_handler(self.back_pressed)
        self.buttons = []
        self.selected_row = None
        return

    def open_parent_menu(self):
        pass

    def on_row_selected(self, index, row):
        pass

    def get_button_with_text(self, text):
        text_to_find = text.lower()
        for button in self.buttons:
            if button.text is not None and button.text.lower() == text_to_find:
                return button

        return

    def back_pressed(self, is_back):
        if is_back:
            self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
            self.open_parent_menu()

    def draw_background(self):
        mid_x = 400
        mix_y = 300
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        global_images.large_frame.blit(mid_x, mix_y)
        title_x = 120
        title_y = 525
        title_width = global_images.large_frame.width - 190
        title_height = 50
        draw_text_with_size_validation(self.title.upper(), title_x, title_y, title_width, title_height, MENU_FONT_COLOR, font=title_font)

    def draw_buttons_background(self):
        pass

    def draw_elements(self):
        for element in self.elements:
            element.draw()

    def draw(self):
        self.draw_background()
        self.draw_buttons_background()
        self.draw_elements()

    def create_button(self, text, x, y, width, height, font_size, on_button_press):
        button = TextButton(text, x, y, width, height, font_size)
        button.add_handler(on_button_press)
        self.buttons.append(button)
        self.elements.append(button)
        return button
