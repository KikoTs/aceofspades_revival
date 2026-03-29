from pyglet import gl
from aoslib.gui import HandlerBase
from aoslib.draw import draw_quad, draw_line
from aoslib.text import draw_text_with_alignment_and_size_validation, medium_aldo_ui_font, small_aldo_ui_font
from aoslib.images import global_images
from aoslib import strings
from shared.constants import MENU_FONT_COLOR
from aoslib.common import draw_image_scaled
from shared.hud_constants import UI_CONTROL_SPACING, TOGGLE_OPTION_DISABLED_COLOUR, TOGGLE_OPTION_BACKGROUND_COLOUR, TOGGLE_OPTION_NORMAL_COLOUR, TOGGLE_OPTION_HOVERED_COLOUR, MINIMUM_HEIGHT_FOR_MEDIUM_FONT, TOGGLE_OPTION_ENABLED_SELECTED_COLOUR, BLACK_COLOUR
import math

class ToggleOptionControl(HandlerBase):
    over_on = None
    over_off = None
    over = None
    index = 0

    def initialize(self, initial_value, x, y, width, height):
        self.options = (
         (
          strings.OFF, False), (strings.ON, True))
        self.update_position(x, y, width, height)
        self.set(initial_value)

    def get_value(self):
        if self.index >= 0 and self.index < len(self.options):
            return self.options[self.index]
        else:
            return

    def set(self, new_value):
        for index, (name, value) in enumerate(self.options):
            if new_value == value:
                self.index = index
                break

    def set_enabled(self, enabled):
        self.enabled = enabled

    def update_position(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.box_width = float(self.width / 2.0) - UI_CONTROL_SPACING / 2
        self.off_box_x = self.x
        self.on_box_x = self.x + self.width - self.box_width
        self.image_size = self.height - UI_CONTROL_SPACING * 2
        self.inner_box_width = self.box_width - UI_CONTROL_SPACING * 3 - self.image_size
        self.inner_box_height = self.image_size
        self.inner_box_y = self.y + UI_CONTROL_SPACING
        self.off_inner_box_x = self.off_box_x + UI_CONTROL_SPACING * 2 + self.image_size
        self.on_inner_box_x = self.on_box_x + UI_CONTROL_SPACING * 2 + self.image_size
        self.scale_x = float(self.image_size) / float(global_images.bullet_hole.width)
        self.scale_y = float(self.image_size) / float(global_images.bullet_hole.height)

    def on_mouse_motion(self, x, y, button, modifiers):
        if self.enabled == False:
            return
        self.over_off = x >= self.off_box_x and x <= self.off_box_x + self.box_width and y >= self.y and y <= self.y + self.height
        self.over_on = x >= self.on_box_x and x <= self.on_box_x + self.box_width and y >= self.y and y <= self.y + self.height
        self.over = self.over_off or self.over_on

    def on_mouse_press(self, x, y, button, modifiers):
        if self.enabled == False:
            return
        self.over_off = x >= self.off_box_x and x <= self.off_box_x + self.box_width and y >= self.y and y <= self.y + self.height
        self.over_on = x >= self.on_box_x and x <= self.on_box_x + self.box_width and y >= self.y and y <= self.y + self.height
        if self.over_off:
            self.index = 0
            self.fire_handlers(self.options[self.index][1])
        elif self.over_on:
            self.index = 1
            self.fire_handlers(self.options[self.index][1])

    def draw(self):
        draw_quad(self.off_box_x, self.y, self.box_width, self.height, TOGGLE_OPTION_BACKGROUND_COLOUR)
        draw_quad(self.on_box_x, self.y, self.box_width, self.height, TOGGLE_OPTION_BACKGROUND_COLOUR)
        if self.enabled:
            selected_colour = TOGGLE_OPTION_ENABLED_SELECTED_COLOUR
            not_selected_colour = TOGGLE_OPTION_NORMAL_COLOUR
        else:
            selected_colour = TOGGLE_OPTION_DISABLED_COLOUR
            not_selected_colour = TOGGLE_OPTION_NORMAL_COLOUR
        off_selected = self.index == 0
        if off_selected:
            off_box_colour = selected_colour
            on_box_colour = TOGGLE_OPTION_HOVERED_COLOUR if self.over_on else not_selected_colour
        else:
            on_box_colour = selected_colour
            off_box_colour = TOGGLE_OPTION_HOVERED_COLOUR if self.over_off else not_selected_colour
        draw_quad(self.off_inner_box_x, self.inner_box_y, self.inner_box_width, self.inner_box_height, off_box_colour)
        draw_quad(self.on_inner_box_x, self.inner_box_y, self.inner_box_width, self.inner_box_height, on_box_colour)
        if off_selected:
            image_x = self.off_box_x + UI_CONTROL_SPACING
        else:
            image_x = self.on_box_x + UI_CONTROL_SPACING
        image_y = self.y + UI_CONTROL_SPACING
        image = global_images.bullet_hole if self.enabled else global_images.bullet_hole_disabled
        draw_image_scaled(image, image_x, image_y, self.scale_x, self.scale_y, 'bottom', True)
        if self.height >= MINIMUM_HEIGHT_FOR_MEDIUM_FONT:
            font = medium_aldo_ui_font
        else:
            font = small_aldo_ui_font
        width = self.inner_box_width - UI_CONTROL_SPACING * 2
        text_x = [self.off_inner_box_x + UI_CONTROL_SPACING, self.on_inner_box_x + UI_CONTROL_SPACING]
        for index, (name, value) in enumerate(self.options):
            x = text_x[index]
            draw_text_with_alignment_and_size_validation(name, x, self.inner_box_y, width, self.inner_box_height, BLACK_COLOUR, font, 'center', 'center')
