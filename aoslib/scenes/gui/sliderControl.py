from aoslib.gui import HandlerBase
from pyglet import gl
from aoslib.scenes.gui.editBoxFloatControl import EditBoxFloatControl
from aoslib.draw import draw_quad, draw_line
from aoslib.images import global_images
from shared.constants import MENU_FONT_COLOR
from aoslib.common import draw_image_resized
from shared.common import clamp
from aoslib.text import draw_text_with_alignment_and_size_validation, small_standard_ui_font
from shared.hud_constants import UI_CONTROL_SPACING, SLIDER_CONTROL_BACKGROUND_COLOUR, SLIDER_CONTROL_LINE_COLOUR, SLIDER_CONTROL_EDIT_BOX_BACKGROUND_COLOUR, SLIDER_CONTROL_BULLET_WIDTH
import math

class SliderControl(HandlerBase):

    def initialize(self, value, x, y, width, height, has_edit_box=True, min_value=0.0, max_value=1.0, decimal_places=2):
        if has_edit_box:
            self.edit_box = EditBoxFloatControl(str(value), x, y, width, height, min_value, max_value, decimal_places)
            self.edit_box.add_handler(self.on_edit_box_value_changed)
            self.edit_box.on_return_callback = self.on_edit_box_value_changed
            self.elements = [self.edit_box]
        else:
            self.edit_box = None
            self.elements = []
        self.min_value = min_value
        self.max_value = max_value
        self.enabled = True
        self.value = value
        if self.value < self.min_value:
            self.value = self.min_value
        elif self.value > self.max_value:
            self.value = self.max_value
        self.update_position(x, y, width, height)
        return

    def on_edit_box_value_changed(self):
        self.set(float(self.edit_box.text), True)

    def update_press(self, x, y, is_click=True):
        if y < self.y or y > self.y + self.height:
            return
        if x < self.x - UI_CONTROL_SPACING or x > self.slider_x + self.slider_width + UI_CONTROL_SPACING:
            return
        new_value = clamp((x - self.slider_x) / self.slider_width) * (self.max_value - self.min_value) + self.min_value
        self.set(new_value, fire=True, on_click=is_click)

    def update_position(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        noof_control_spacing = 4 if self.edit_box is None else 5
        edit_box_width = 0 if self.edit_box is None else self.width / 6
        edit_box_x = self.x + self.width - UI_CONTROL_SPACING - edit_box_width
        self.slider_width = self.width - edit_box_width - UI_CONTROL_SPACING * noof_control_spacing
        self.slider_x = self.x + UI_CONTROL_SPACING * 2
        self.slider_y = self.y + UI_CONTROL_SPACING
        self.slider_height = self.height - UI_CONTROL_SPACING * 2
        if self.edit_box is not None:
            self.edit_box.update_position(edit_box_x, self.slider_y, edit_box_width, self.slider_height)
            self.edit_box.set(str(round(self.value, self.edit_box.decimal_places)))
        self.__set_bullet_position()
        return

    def on_text(self, value):
        if self.edit_box is not None:
            self.edit_box.on_text(value)
        return

    def on_text_motion(self, motion):
        if self.edit_box is not None:
            self.edit_box.on_text_motion(motion)
        return

    def __set_bullet_position(self):
        value = float(self.value - self.min_value) / float(self.max_value - self.min_value)
        self.bullet_x = max(self.slider_x + self.slider_width * value, self.slider_x)
        self.bullet_x = min(self.bullet_x, self.slider_x + self.slider_width)

    def set(self, value, fire=False, on_click=True):
        self.value = value
        self.__set_bullet_position()
        if self.edit_box is not None:
            self.edit_box.set(str(round(self.value, self.edit_box.decimal_places)))
        if fire:
            self.fire_handlers(on_click)
        return

    def on_mouse_press(self, x, y, button, modifiers):
        if not self.enabled:
            return
        self.update_press(x, y, True)
        for element in self.elements:
            element.on_mouse_press(x, y, button, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        if not self.enabled:
            return
        self.update_press(x, y, False)
        for element in self.elements:
            element.on_mouse_drag(x, y, dx, dy, button, modifiers)

    def draw(self):
        line_height = math.floor((self.height - UI_CONTROL_SPACING * 2) / 2)
        line_size = 2
        draw_quad(self.x, self.y, self.width, self.height, SLIDER_CONTROL_BACKGROUND_COLOUR)
        draw_quad(self.slider_x, self.slider_y, self.slider_width, line_size, SLIDER_CONTROL_LINE_COLOUR)
        draw_quad(self.slider_x, self.slider_y, line_size, line_height, SLIDER_CONTROL_LINE_COLOUR)
        draw_quad(self.slider_x + self.slider_width, self.slider_y, line_size, line_height, SLIDER_CONTROL_LINE_COLOUR)
        y = self.y + self.height - UI_CONTROL_SPACING - line_height / 2
        draw_text_with_alignment_and_size_validation(str(self.min_value), self.slider_x - UI_CONTROL_SPACING + line_height / 2, y, line_height, line_height, MENU_FONT_COLOR, small_standard_ui_font, alignment_x='center', alignment_y='center')
        draw_text_with_alignment_and_size_validation(str(self.max_value), self.slider_x + self.slider_width - UI_CONTROL_SPACING - line_height / 2, y, line_height, line_height, MENU_FONT_COLOR, small_standard_ui_font, alignment_x='center', alignment_y='center')
        height = UI_CONTROL_SPACING * 2 + line_size
        draw_image_resized(global_images.bullet_slider, self.bullet_x, self.y + height - line_size, SLIDER_CONTROL_BULLET_WIDTH, height, clear_colours=True)
        for element in self.elements:
            element.draw()
