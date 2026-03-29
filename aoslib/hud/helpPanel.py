from pyglet.gl import *
from aoslib.images import global_images
from shared.constants import *
from aoslib.text import help_font, draw_text_with_size_validation, draw_text_with_alignment_and_size_validation, split_text_to_fit_screen, translate_controls_in_message, HELP_FONT_SIZE, draw_text_lines, get_resized_font_and_formatted_text_to_fit_boundaries, get_line_scale_from_text_and_width
from aoslib import strings
import math
from aoslib.draw import draw_quad
TRANSITION_SPEED = 8

class HelpPanel(object):

    def __init__(self, hud):
        self.scene = hud.scene
        self.text = None
        self.transition_percentage = 0
        self.next_text = None
        self.delay = 0.0
        self.line_spacing = 5
        self.open = False
        self.padding = 20
        window = self.scene.window
        self.max_width = window.width * 0.3
        self.text_width = self.max_width
        self.text_height = 300
        self.split_text = None
        self.biggest_width = 0
        self.enabled = True
        self.close_text = None
        self.override = False
        self.window_height = 0
        self.window_width = 0
        self.total_text_height = 0
        self.ugc = False
        self.split_text = None
        self.font_to_use = None
        return

    def set_max_width(self, width):
        self.max_width = width

    def set_ugc_size_position(self):
        self.ugc = True

    def init_scroll_from_top(self, from_update=False):
        window = self.scene.window
        if window.height != self.window_height or window.width != self.window_width:
            if not self.ugc:
                self.text_width = self.max_width
                self.text_offset_x_start = window.width * 0.5 - self.text_width * 0.5
            else:
                width = window.width * 0.5
                end_space = width - width * 0.6
                if end_space < 290:
                    width = width - (290 - end_space) * 0.5
                self.text_width = width
                self.text_offset_x_start = window.width * 0.46 - width * 0.5 * 0.5
            self.window_width = window.width
            self.window_height = window.height
        elif from_update:
            return
        self.font_to_use, self.split_text = get_resized_font_and_formatted_text_to_fit_boundaries(self.text, self.text_width, self.text_height, help_font, 2)
        if not self.split_text:
            return
        self.line_scale = 1.0
        for text_line in self.split_text:
            line_scale = get_line_scale_from_text_and_width(text_line, self.text_width, help_font)
            if line_scale < self.line_scale:
                self.line_scale = line_scale

        self.line_height = (self.font_to_use.get_ascender() + self.font_to_use.get_descender() + self.line_spacing) * self.line_scale
        self.total_text_height = (len(self.split_text) + 2) * self.line_height
        self.biggest_width = 0
        for line in self.split_text:
            width = self.font_to_use.get_line_width(line)
            if width > self.biggest_width:
                self.biggest_width = width

        if not self.ugc:
            self.text_offset_x_start = window.width * 0.5 - self.biggest_width * 0.5
        self.text_offset_x_end = 0
        self.text_offset_y_start = window.height + self.total_text_height + self.padding * 2.0
        self.text_offset_y_end = window.height - self.total_text_height - self.padding * 2.0 - 10
        self.text_move_amount_x = 0
        self.text_move_amount_y = self.total_text_height + self.padding * 2.0 + 50

    def init_scroll_from_left(self):
        window = self.scene.window
        self.text_offset_x_start = -self.text_width
        self.text_offset_x_end = 10
        self.text_offset_y_start = window.height * 0.5 + self.total_text_height * 0.5
        self.text_offset_y_end = 0
        self.text_move_amount_x = self.text_width + self.text_offset_x_end + self.padding
        self.text_move_amount_y = 0

    def set_text(self, message_ids, delay, override=False, play_sound=True):
        if not self.enabled:
            return
        if self.override and not override:
            return
        self.override = override
        self.delay = delay
        self.text = ('\n').join(translate_controls_in_message(self.scene, strings.get_by_id(message_id)) for message_id in message_ids)
        self.close_text = translate_controls_in_message(self.scene, strings.TOOL_HELP_PANEL_CLOSE)
        if self.text and play_sound:
            self.scene.media.play('tutorial_disapp')
        self.init_scroll_from_top()

    def toggle_show(self):
        if self.open:
            self.open = False
            self.override = False
        else:
            self.open = True

    def cancel_override(self):
        self.override = False

    def force_close(self):
        self.open = False
        self.override = False

    def force_open(self):
        self.open = True

    def update(self):
        self.init_scroll_from_top(from_update=True)

    def draw(self):
        if not self.enabled:
            return
        if not self.split_text:
            return
        if self.text and self.open:
            if self.delay > 0:
                self.delay -= UPDATE_INTERVAL
                if self.delay <= 0:
                    self.scene.media.play('tutorial_app')
            elif self.transition_percentage < 100:
                self.transition_percentage = min(self.transition_percentage + TRANSITION_SPEED, 100)
        elif self.text and not self.open:
            if self.transition_percentage >= 0:
                self.transition_percentage = max(self.transition_percentage - TRANSITION_SPEED, 0)
        else:
            self.transition_percentage = max(self.transition_percentage - TRANSITION_SPEED, 0)
        if self.transition_percentage <= 0:
            return
        x_offset = self.text_offset_x_start - math.sin(self.transition_percentage * 0.01 * math.pi * 0.5) * self.text_move_amount_x
        y_offset = self.text_offset_y_start - math.sin(self.transition_percentage * 0.01 * math.pi * 0.5) * self.text_move_amount_y
        draw_quad(x_offset - self.padding, y_offset + self.line_height - self.total_text_height - self.padding, self.biggest_width + self.padding * 2.0, self.total_text_height + self.padding * 2.0, (0,
                                                                                                                                                                                                       0,
                                                                                                                                                                                                       0,
                                                                                                                                                                                                       150))
        extra_offset = 0
        SHADOW_COLOUR = (0, 0, 0, 80)
        draw_text_lines(self.split_text, x_offset, y_offset + extra_offset, self.text_width, self.total_text_height, self.font_to_use, 2, MENU_FONT_COLOR, force_line_scale=self.line_scale, shadowed=True)
        if self.close_text and self.biggest_width > 0:
            extra_offset -= self.line_height * (len(self.split_text) + 1)
            draw_text_lines([self.close_text], x_offset, y_offset + extra_offset, self.biggest_width, self.total_text_height, self.font_to_use, 2, MENU_FONT_COLOR, 'right', 'bottom', force_line_scale=self.line_scale, shadowed=True)
