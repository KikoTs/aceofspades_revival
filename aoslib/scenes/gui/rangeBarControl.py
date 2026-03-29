from pyglet import gl
from aoslib.gui import HandlerBase
from aoslib.draw import draw_quad
from aoslib.images import global_images
from aoslib.common import draw_image_scaled
from aoslib.gui import SquareButton
from aoslib.common import collides
from aoslib.common import draw_image_resized
from shared.common import clamp
from shared.hud_constants import RANGE_BAR_OPTION_SPACING, UI_CONTROL_BAR_BUTTON_SPACING, BLACK_COLOUR, RANGE_BAR_SPACING, RANGE_BAR_WIDTH
import math

class RangeBarControl(HandlerBase):

    def initialize(self, value, x, y, width, height, step=0.2):
        self.button_size = 25
        self.left_button = SquareButton(global_images.left_arrow, x, y, self.button_size)
        self.left_button.add_handler(self.on_click, -1)
        self.right_button = SquareButton(global_images.right_arrow, x + width, y, self.button_size)
        self.right_button.add_handler(self.on_click, 1)
        self.elements = (self.left_button, self.right_button)
        self.value = value
        self.step = step
        y_pad = 5
        self.update_position(x, y, width, height)
        self.update_buttons_enabled_state()

    def update_position(self, x, y, width, height):
        self.width = width
        self.height = height
        self.button_size = self.height - RANGE_BAR_OPTION_SPACING * 2.0
        self.x = x
        self.y = y
        self.x1 = x + RANGE_BAR_OPTION_SPACING + self.button_size + UI_CONTROL_BAR_BUTTON_SPACING
        self.x2 = x + width - (RANGE_BAR_OPTION_SPACING + self.button_size + UI_CONTROL_BAR_BUTTON_SPACING)
        self.y1 = y + RANGE_BAR_OPTION_SPACING
        self.y2 = y + height - RANGE_BAR_OPTION_SPACING * 2
        self.left_button.size = self.button_size
        self.right_button.size = self.button_size
        button_left_x = self.x + RANGE_BAR_OPTION_SPACING + self.button_size / 2.0
        button_right_x = self.x + self.width - self.button_size - RANGE_BAR_OPTION_SPACING + self.button_size / 2.0
        button_y = self.y + RANGE_BAR_OPTION_SPACING + self.button_size / 2.0
        self.left_button.set_position(button_left_x, button_y)
        self.right_button.set_position(button_right_x, button_y)

    def on_click(self, value):
        self.set(self.value + self.step * value, True, True)

    def update_buttons_enabled_state(self):
        self.right_button.enabled = self.value < 1.0
        self.left_button.enabled = self.value > 0

    def set(self, value, fire=False, on_click=False):
        self.value = clamp(value)
        if self.value < 0.01:
            self.value = 0.0
        self.update_buttons_enabled_state()
        if fire:
            self.fire_handlers(on_click, self.value)

    def update_press(self, x, y, is_click):
        if not collides(self.x1, self.y1, self.x2, self.y2, x, y, x, y):
            return
        self.set((x - self.x1) / float(self.x2 - self.x1), fire=True, on_click=is_click)

    def on_mouse_press(self, x, y, button, modifiers):
        self.update_press(x, y, True)
        for element in self.elements:
            element.on_mouse_press(x, y, button, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        self.update_press(x, y, False)
        for element in self.elements:
            element.on_mouse_drag(x, y, dx, dy, button, modifiers)

    def on_mouse_motion(self, *arg, **kw):
        for element in self.elements:
            element.on_mouse_motion(*arg, **kw)

    def on_mouse_release(self, *arg, **kw):
        for element in self.elements:
            element.on_mouse_release(*arg, **kw)

    def draw(self):
        draw_quad(self.x, self.y, self.width, self.height, BLACK_COLOUR)
        bar_width = RANGE_BAR_WIDTH + RANGE_BAR_SPACING
        total_width = self.width - self.button_size * 2 - RANGE_BAR_OPTION_SPACING * 2 - UI_CONTROL_BAR_BUTTON_SPACING * 2
        total_count = int(math.ceil(total_width / float(bar_width)))
        count = int(math.ceil(self.value * total_count))
        x = self.x1 + RANGE_BAR_WIDTH / 2
        for bar in xrange(total_count):
            if bar < count:
                mul = 1.0
            else:
                mul = 0.5
            gl.glColor4f(mul, mul, mul, 1.0)
            draw_image_resized(global_images.volume_bar, x, self.y + RANGE_BAR_OPTION_SPACING + self.button_size / 2, RANGE_BAR_WIDTH, self.button_size)
            x += bar_width

        for element in self.elements:
            element.draw()
