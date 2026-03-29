from aoslib.gui import HandlerBase
from pyglet import gl
from pyglet.window import key
from pyglet.window import mouse
from aoslib.draw import draw_quad, draw_line
from aoslib.images import global_images
from shared.constants import MENU_FONT_COLOR
from aoslib.common import multiply_color
from aoslib.text import draw_text_with_alignment_and_size_validation, small_standard_ui_font, medium_standard_ui_font
from shared.hud_constants import UI_CONTROL_SPACING, EDIT_BOX_BACKGROUND_COLOUR, MINIMUM_HEIGHT_FOR_MEDIUM_FONT, TEXT_BACKGROUND_SPACING
from shared.common import clamp
import time, copy

class EditBoxControl(HandlerBase):
    focus = over = False
    on_return_callback = None
    allow_over_typing = False
    visible_text = ''
    is_over_typing = False
    characters_to_keep_beyond_caret = 3
    max_characters = None

    def initialize(self, value, x, y, width, height, typ=unicode, center=True, empty_text='', draw_background=True, profanity_manager=None, replacement_words=u'#*%!', max_characters=None, return_on_focus_loss=True):
        self.caret_index = 0
        self.min_index = 0
        self.max_index = 0
        self.min_visible_index = 0
        self.max_visible_index = 0
        self.profanity_manager = profanity_manager
        self.replacement_words = replacement_words
        self.update_position(x, y, width, height)
        self.type = typ
        self.center = center
        self.empty_text = empty_text
        self.set(value)
        self.initialise_caret_index()
        self.draw_background = draw_background
        self.max_characters = max_characters
        self.return_on_focus_loss = return_on_focus_loss
        self.is_password = False

    def initialise_caret_index(self):
        if len(self.visible_text) > 0:
            self.caret_index = self.max_visible_index
        else:
            self.caret_index = 0

    def initialise_text(self, value):
        self.set(value)
        self.initialise_caret_index()

    def update_position(self, x, y, width, height):
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.caret_height = self.height - UI_CONTROL_SPACING * 2
        if self.height >= MINIMUM_HEIGHT_FOR_MEDIUM_FONT:
            self.font = medium_standard_ui_font
        else:
            self.font = small_standard_ui_font

    def move_caret_back(self):
        if self.caret_index - 1 < 0:
            return
        self.caret_index -= 1
        if self.caret_index < self.min_visible_index + self.characters_to_keep_beyond_caret and self.min_visible_index > 0:
            self.set(self.text, min_visible_index=self.min_visible_index - 1)

    def move_caret_forward(self):
        if self.caret_index + 1 > self.max_index:
            return
        self.caret_index += 1
        if self.caret_index > self.max_visible_index - self.characters_to_keep_beyond_caret and self.max_visible_index < self.max_index:
            self.set(self.text, max_visible_index=self.max_visible_index + 1)

    def delete_current_caret_pos(self):
        if self.caret_index >= self.max_index or self.max_index == 0:
            return
        if self.max_visible_index == self.max_index:
            new_max_visible_index = self.max_visible_index - 1
        else:
            new_max_visible_index = self.max_visible_index
        self.set(self.text[:self.caret_index] + self.text[self.caret_index + 1:], max_visible_index=new_max_visible_index)

    def delete_previous_caret_pos(self):
        if self.caret_index <= self.min_index:
            return
        if self.caret_index == self.max_index:
            self.set(self.text[:-1], False)
        else:
            if self.min_visible_index > 0 and (self.caret_index - 1 < self.min_visible_index + self.characters_to_keep_beyond_caret or self.max_visible_index == self.max_index):
                new_min_visible_index = self.min_visible_index - 1
            else:
                new_min_visible_index = self.min_visible_index
            self.set(self.text[:self.caret_index - 1] + self.text[self.caret_index:], min_visible_index=new_min_visible_index)
        self.caret_index -= 1

    def display_first_index(self):
        self.caret_index = 0
        self.set(self.text, min_visible_index=0)

    def display_last_index(self):
        self.caret_index = self.max_index
        self.set(self.text, max_visible_index=self.max_index)

    def update_over(self, x, y):
        self.over = x >= self.x and x <= self.x + self.width and y >= self.y and y <= self.y + self.height

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        self.update_over(x, y)

    def on_mouse_motion(self, x, y, dx, dy):
        self.update_over(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if not self.enabled:
            return
        if button != mouse.LEFT:
            return
        self.update_over(x, y)
        self.set_focus(self.over)

    def set_focus(self, value):
        old_focus = self.focus
        self.focus = value
        if not value and old_focus:
            self.set(self.value)
            if self.return_on_focus_loss:
                self.on_return()
            self.fire_handlers()

    def on_text_motion(self, motion):
        if not self.focus:
            return
        text_length = len(self.text)
        if motion is key.MOTION_BACKSPACE and text_length > 0:
            self.delete_previous_caret_pos()
        elif motion is key.MOTION_DELETE and text_length > 0:
            self.delete_current_caret_pos()
        elif motion in (key.ENTER, key.RETURN):
            self.fire_handlers()
        elif motion is key.MOTION_LEFT:
            self.move_caret_back()
        elif motion is key.MOTION_RIGHT:
            self.move_caret_forward()

    def set(self, value, fire=False, min_visible_index=None, max_visible_index=None):
        text = unicode(value)
        width = max(1, self.width - UI_CONTROL_SPACING * 2)
        self.min_index = 0
        self.max_index = len(text)
        self.min_visible_index = 0
        self.max_visible_index = self.max_index
        if not self.allow_over_typing:
            while self.font.get_line_width(text) > width:
                text = text[:-1]
                self.move_caret_back()

            visible_text = text
        if self.max_characters and len(text) > self.max_characters:
            while len(text) > self.max_characters:
                text = text[:-1]
                self.move_caret_back()

            visible_text = text
        self.is_over_typing = False
        if self.allow_over_typing:
            visible_text = copy.copy(text)
            if self.font.get_line_width(visible_text) <= width:
                self.is_over_typing = False
            elif min_visible_index is not None:
                self.is_over_typing = True
                self.min_visible_index = clamp(min_visible_index, 0, len(text))
                visible_text = visible_text[min_visible_index:]
                while self.font.get_line_width(visible_text) > width:
                    visible_text = visible_text[:-1]
                    self.max_visible_index -= 1

            elif max_visible_index is not None:
                self.is_over_typing = True
                self.max_visible_index = clamp(max_visible_index, 0, len(text))
                visible_text = visible_text[:max_visible_index]
                self.min_visible_index = 0
                while self.font.get_line_width(visible_text) > width:
                    visible_text = visible_text[1:]
                    self.min_visible_index += 1

            else:
                self.is_over_typing = True
                self.min_visible_index = 0
                while self.font.get_line_width(visible_text) > width:
                    visible_text = visible_text[1:]
                    self.min_visible_index += 1

        try:
            self.value = self.type(text or self.type())
        except ValueError:
            return

        self.text = text
        self.visible_text = visible_text
        if fire:
            self.fire_handlers()
        return

    def on_key_press(self, button, modifiers):
        if not self.enabled:
            return
        if self.focus == False:
            return
        if button == key.END:
            self.display_last_index()
            return
        if button == key.HOME:
            self.display_first_index()
            return

    def on_return(self):
        if self.profanity_manager is not None:
            self.text = self.profanity_manager.sanitise_string(self.text, self.replacement_words)
        self.set(self.text)
        self.set_focus(False)
        if self.on_return_callback:
            self.on_return_callback()
        return

    def on_text(self, value):
        if not self.focus:
            return
        else:
            if value == u'\r':
                self.on_return()
                return
            if len(self.text) >= 200:
                return
            text_length = len(self.visible_text)
            if self.caret_index >= self.max_visible_index - self.characters_to_keep_beyond_caret:
                new_min_index = None
                new_max_index = self.max_visible_index + 1
            else:
                new_min_index = self.min_visible_index
                new_max_index = None
            if text_length > 0:
                text = self.text[0:self.caret_index] + value + self.text[self.caret_index:]
                self.caret_index += 1
            else:
                text = value
                self.caret_index = 1
            if self.caret_index == len(text):
                self.set(text, False)
            else:
                self.set(text, False, min_visible_index=new_min_index, max_visible_index=new_max_index)
            return

    def draw(self):
        if not self.visible:
            return
        else:
            gl.glColor4f(1.0, 1.0, 1.0, 1.0)
            if self.draw_background:
                draw_quad(self.x, self.y, self.width, self.height, EDIT_BOX_BACKGROUND_COLOUR)
            text_to_draw = self.visible_text
            if self.is_password:
                text_to_draw = ''
                for i in range(len(self.visible_text)):
                    text_to_draw = text_to_draw + '*'

            if text_to_draw == '' and not self.focus and self.empty_text != '':
                text_to_draw = self.empty_text
            text_width = 0 if self.font is None else self.font.get_line_width(self.visible_text)
            text_y = self.y + self.height / 2.0 - float(self.font.get_ascender() + self.font.get_descender()) / 2.0
            if self.is_over_typing:
                text_x = self.x + self.width - text_width - UI_CONTROL_SPACING
            elif self.center:
                text_x = self.x + self.width / 2 - text_width / 2
            else:
                text_x = self.x
                if text_to_draw == self.text or text_to_draw == self.empty_text:
                    text_x += UI_CONTROL_SPACING
            if len(self.visible_text) > 0:
                visible_text_to_caret = self.text[self.min_visible_index:self.caret_index]
                text_width_to_caret = 0 if self.font is None else self.font.get_line_width(visible_text_to_caret)
            else:
                text_width_to_caret = 0
            if self.enabled and self.focus and time.time() % 1.0 < 0.5:
                caret_x = text_x + text_width_to_caret
                draw_quad(caret_x, self.y + UI_CONTROL_SPACING, 2, self.caret_height, MENU_FONT_COLOR)
            color = MENU_FONT_COLOR
            if self.over and not self.focus:
                color = multiply_color(color[:-1], 0.7) + (255, )
            self.font.draw(text_to_draw, text_x, text_y, color, center=False)
            return
