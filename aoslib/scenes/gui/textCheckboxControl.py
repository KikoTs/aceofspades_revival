from aoslib.gui import TextCheckbox
from pyglet import gl
from pyglet.window import mouse
from aoslib.gui import HandlerBase
from aoslib.draw import draw_quad
from aoslib.images import global_images
from aoslib.common import draw_image_scaled
from aoslib.common import collides
from shared.common import clamp
from shared.constants import MENU_FONT_COLOR
from aoslib.text import draw_text_with_alignment_and_size_validation, small_standard_ui_font, medium_standard_ui_font
from shared.hud_constants import UI_CONTROL_SPACING, DISABLE_TEXT_COLOUR, TEXT_BACKGROUND_SPACING, MINIMUM_HEIGHT_FOR_MEDIUM_FONT, BLACK_COLOUR
import math

class TextCheckboxControl(TextCheckbox):

    def initialize(self, text, value, x, y, width, height):
        self.text = text
        self.update_position(x, y, width, height)
        self.value = value
        self.images = {}
        self.set_images(global_images.checkmark, None)
        return

    def set(self, selected):
        self.value = selected

    def set_images(self, checked, unchecked):
        self.images[True] = checked
        self.images[False] = unchecked

    def set_text(self, text):
        self.text = text

    def update_position(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.check_size = self.height - UI_CONTROL_SPACING * 2
        self.check_x1 = self.x + self.width - (UI_CONTROL_SPACING + self.check_size)
        self.check_x2 = self.check_x1 + self.check_size
        self.check_y1 = self.y + UI_CONTROL_SPACING
        self.check_y2 = self.check_y1 + self.check_size

    def on_mouse_press(self, x, y, button, modifiers):
        if self.enabled == False:
            return
        if button != mouse.LEFT:
            return
        if collides(self.x, self.check_y1, self.check_x2, self.check_y2, x, y, x, y):
            self.value = not self.value
            self.fire_handlers(self.value)

    def draw(self):
        draw_quad(self.x, self.y, self.width, self.height, BLACK_COLOUR)
        if self.enabled:
            text_color = MENU_FONT_COLOR
            check_color = (1.0, 1.0, 1.0, 1.0)
        else:
            text_color = DISABLE_TEXT_COLOUR
            check_color = (83.0 / 255.0, 83.0 / 255.0, 83.0 / 255.0, 1.0)
        if self.height >= MINIMUM_HEIGHT_FOR_MEDIUM_FONT:
            font = medium_standard_ui_font
        else:
            font = small_standard_ui_font
        text_x = self.x + TEXT_BACKGROUND_SPACING
        text_width = self.width - UI_CONTROL_SPACING - TEXT_BACKGROUND_SPACING * 2 - self.check_size
        draw_text_with_alignment_and_size_validation(self.text, text_x, self.y + UI_CONTROL_SPACING, text_width, self.check_size, text_color, font, alignment_x='center', alignment_y='center')
        gl.glColor4f(*check_color)
        if self.images[self.value]:
            self.images[self.value].blit(self.check_x1, self.check_y1, width=self.check_size, height=self.check_size)
