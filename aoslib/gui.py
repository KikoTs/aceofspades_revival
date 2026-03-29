from aoslib.text import EDO_FONT, START_FONT, CHAT_FONT, DEFAULT_FONT_SIZE, BUTTON_FONT, ALDO_FONT, Label, brushed_font, list_font, CATEGORY_FONT, CATEGORY_FONT_SIZE, navigation_font, draw_text_with_alignment_and_size_validation, draw_text_lines, get_resized_font_and_formatted_text_to_fit_boundaries, option_font, settings_value_font, key_input_font, edit_font, draw_text_with_size_validation, small_aldo_ui_font, medium_aldo_ui_font, big_aldo_ui_font, medium_button_aldo_font, big_button_aldo_font, small_standard_ui_font, small_edo_ui_font, medium_edo_ui_font
from aoslib.draw import draw_quad, draw_line, draw_frame, draw_quad_gradient
from aoslib.common import collides, multiply_color, multiply_float_color, draw_image_resized
from aoslib.images import global_images
from aoslib.shape import Rectangle
from shared.constants import MENU_FONT_COLOR, MENU_FONT_COLOR2, BUTTON_COLOR, IMAGE_CENTRE, IMAGE_LEFT, IMAGE_RIGHT
from shared.hud_constants import *
from shared.common import clamp
from pyglet.window import key
from pyglet.window import mouse
from pyglet import gl
import string, math, time
from aoslib import strings
import copy
from aoslib.media import HUD_AUDIO_ZONE
from aoslib.common import draw_image_scaled
LINE_PAD = 8
ITEM_COLOR = (27, 224, 66)
CHECKBOX_COLOR = (
 128, 128, 128, 100)
CHECKBOX_COLOR2 = (30, 30, 30, 100)
CHECKBOX_CROSS_COLOR = (255, 255, 255, 255)
CHECKBOX_CROSS_SIZE = 4
RECT_RADIUS = 10

class ControlBase(object):
    enabled = True
    visible = True

    def on_mouse_motion(self, x, y, dx, dy):
        pass

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        pass

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def on_double_click(self, x, y, button, modifiers):
        pass

    def on_mouse_release(self, x, y, button, modifiers):
        pass

    def on_key_press(self, button, modifiers):
        pass

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        pass

    def on_key_release(self, button, modifiers):
        pass

    def on_text_motion_select(self, motion):
        pass

    def on_text_motion(self, motion):
        pass

    def on_text(self, value):
        pass


class HandlerBase(ControlBase):

    def __init__(self, *arg, **kw):
        self.handlers = []
        self.initialize(*arg, **kw)

    def add_handler(self, handler, *arg, **kw):
        self.handlers.append((handler, arg, kw))

    def fire_handlers(self, *narg):
        for handler, arg, kw in self.handlers:
            handler(*(narg + arg), **kw)

    def set_enabled(self, enabled):
        self.enabled = enabled


class Checkbox(HandlerBase):

    def initialize(self, value, x, y, size=32):
        self.size = size
        self.update_position(x, y)
        self.value = value

    def update_position(self, x, y):
        self.x1 = x - self.size / 2.0
        self.x2 = self.x1 + self.size
        self.y1 = y
        self.y2 = self.y1 + self.size

    def on_mouse_press(self, x, y, button, modifiers):
        if self.enabled:
            if button != mouse.LEFT:
                return
            if collides(self.x1, self.y1, self.x2, self.y2, x, y, x, y):
                self.value = not self.value
                self.fire_handlers()

    def draw(self):
        if not self.value:
            return
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        global_images.checkmark.blit(self.x1 + 4, self.y1 + 2)


class TextCheckbox(Checkbox):

    def initialize(self, text, value, x, y, width, size=26, font_name=START_FONT, font_size=DEFAULT_FONT_SIZE):
        self.x = x
        self.y = y
        self.checkbox = Checkbox.initialize(self, value, x, y, size)
        self.text = text

    def draw(self):
        brushed_font.draw(self.text, self.x - 30, self.y + 10, MENU_FONT_COLOR, right=True)
        Checkbox.draw(self)


class SquareButton(HandlerBase):
    over = pressed = False
    image = global_images.button_square
    hover_image = global_images.button_square_hover
    press_image = global_images.button_square_press

    def initialize(self, texture, x, y, size=None, texture_colour=(1.0, 1.0, 1.0, 1.0)):
        self.texture = texture
        self.size = size or global_images.button_square.width
        self.set_position(x, y)
        self.enabled = True
        self.draw_background_image = True
        self.texture_colour = texture_colour

    def set_images(self, image, hover, press, change_size=True):
        self.image = image
        self.hover_image = hover
        self.press_image = press
        if change_size:
            self.size = self.image.width

    def set_position(self, x, y):
        self.x, self.y = x, y
        self.x1 = x - self.size / 2
        self.x2 = self.x1 + self.size
        self.y1 = y - self.size / 2
        self.y2 = self.y1 + self.size

    def update_over(self, x, y):
        self.over = collides(self.x1, self.y1, self.x2, self.y2, x, y, x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.enabled:
            self.pressed = True

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        self.update_over(x, y)

    def on_mouse_motion(self, x, y, dx, dy):
        self.update_over(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        if self.pressed and self.over and self.enabled:
            self.fire_handlers()
        if self.pressed:
            self.pressed = False

    def draw(self):
        add_y = 0.0
        if self.pressed and self.over:
            image = self.press_image
            add_y = math.floor(-4.0 * (self.size / float(image.width)))
        elif self.over:
            image = self.hover_image
        else:
            image = self.image
        if self.enabled:
            gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        else:
            gl.glColor4ub(*BUTTON_DISABLED_COLOUR)
        if self.draw_background_image:
            scale_x = float(self.size) / float(image.width)
            scale_y = float(self.size) / float(image.height)
            y = self.y1 + add_y
            x = self.x1
            draw_image_scaled(image, x, y, scale_x, scale_y, 'bottom')
        if self.texture:
            if self.texture.width >= self.size:
                scale_x = float(self.size) / float(self.texture.width)
            else:
                scale_x = 1.0
            if self.texture.height >= self.size:
                scale_y = float(self.size) / float(self.texture.height)
            else:
                scale_y = 1.0
            if self.enabled:
                gl.glColor4f(self.texture_colour[0], self.texture_colour[1], self.texture_colour[2], self.texture_colour[3])
            else:
                gl.glColor4f(self.texture_colour[0] * BUTTON_DISABLED_COLOUR[0] / 255.0, self.texture_colour[1] * BUTTON_DISABLED_COLOUR[1] / 255.0, self.texture_colour[2] * BUTTON_DISABLED_COLOUR[2] / 255.0, self.texture_colour[3] * BUTTON_DISABLED_COLOUR[3] / 255.0)
            draw_image_scaled(self.texture, self.x1, self.y1 + add_y, scale_x, scale_y, 'bottom')
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)


class ImageButton(HandlerBase):
    over = False
    label = None

    def initialize(self, texture, x, y, text=None, font_size=15):
        self.texture = texture
        self.x, self.y = x, y
        x -= texture.anchor_x
        y -= texture.anchor_y
        self.x1, self.y1 = x, y
        self.x2, self.y2 = x + texture.width, y + texture.height
        if text is not None:
            self.label = Label(text, font_name=BUTTON_FONT, font_size=font_size, x=self.x1, y=self.y1 + 40, width=texture.width, height=texture.height, color=BUTTON_COLOR, anchor_y='bottom')
            self.label.set_horizontal_align('center')
            self.label.set_vertical_align('center')
        return

    def update_over(self, x, y):
        self.over = collides(self.x1, self.y1, self.x2, self.y2, x, y, x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.over:
            self.fire_handlers()

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        self.update_over(x, y)

    def on_mouse_motion(self, x, y, dx, dy):
        self.update_over(x, y)

    def draw(self):
        if self.over:
            gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        else:
            mul = 0.7
            gl.glColor4f(mul, mul, mul, 1.0)
        self.texture.blit(self.x, self.y)
        if self.label:
            self.label.draw()


KEY_TRANSLATIONS = {'LCTRL_REAL': 'CTRL', 
   'LSHIFT': 'SHIFT', 
   'PAGEDOWN': 'PAGE_DOWN', 
   'PAGEUP': 'PAGE_UP', 
   'NUMLOCK': 'NUM_LOCK', 
   'CAPSLOCK': 'CAPS_LOCK'}

def translate_key(value):
    new = key.symbol_string(value)
    if new.startswith('_'):
        new = new[1:]
    elif new.startswith('NUM_'):
        new = new[4:]
    if new in KEY_TRANSLATIONS:
        new = KEY_TRANSLATIONS.get(new, new)
    text = strings.get_by_id(new.upper())
    if 'Missing string ' in text:
        text = KEY_TRANSLATIONS.get(new, new)
    return text


class KeyControl(HandlerBase):
    focus = over = False
    enabled = True
    init_text = ''
    text = None

    def initialize(self, value, text, x, y, width, height):
        self.init_text = text
        self.update_position(x, y, width, height)
        if value is not None:
            self.set(value, False)
        return

    def update_position(self, x, y, width, height):
        self.width = width
        self.height = height
        self.x1 = x
        self.y1 = y
        self.x2 = x + self.width
        self.y2 = y + self.height

    def set(self, value, fire=False):
        self.value = value
        if self.init_text is not None and self.value is None:
            self.text = self.init_text
        elif self.value is not None and self.init_text is not None:
            self.text = strings.DOUBLE_KEY_BINDING.format(self.init_text, translate_key(value))
        else:
            self.text = translate_key(value)
        if fire:
            self.fire_handlers()
        return

    def update_over(self, x, y):
        self.over = x >= self.x1 and x <= self.x2 and y >= self.y1 and y <= self.y2

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        if not self.enabled:
            return
        self.update_over(x, y)

    def on_mouse_motion(self, x, y, dx, dy):
        if not self.enabled:
            return
        self.update_over(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if not self.enabled:
            return
        if button == mouse.LEFT:
            self.focus = self.over

    def on_key_press(self, symbol, modifiers):
        if not self.focus or not self.enabled:
            return
        self.set(symbol, True)
        self.focus = False

    def draw(self):
        text_width = self.width - TEXT_BACKGROUND_SPACING * 2
        if self.focus:
            text = strings.PRESS_KEY
            colour = MENU_FONT_COLOR
            draw_quad(self.x1, self.y1, self.width, self.height, BLACK_COLOUR)
        else:
            if self.text is None or self.text == '':
                text = strings.NONE
            else:
                text = self.text
            colour = BUTTON_COLOR if self.enabled else MENU_FONT_COLOR
        if self.height >= MINIMUM_HEIGHT_FOR_MEDIUM_FONT:
            font = medium_edo_ui_font
        else:
            font = small_edo_ui_font
        draw_text_with_alignment_and_size_validation(text, self.x1 + TEXT_BACKGROUND_SPACING, self.y1, text_width, self.height, colour, font, alignment_x='center', alignment_y='center')
        return


class KeyDisplay(HandlerBase):
    pressed = False

    def initialize(self, x, y, key_string, size=None):
        self.set_position(x, y)
        self.visible = True
        self.image = global_images.key_images[key_string][0]
        self.pressed_image = global_images.key_images[key_string][1]
        self.size = size if size is not None else self.pressed_image.width
        self.key = {'1': (key._1), '2': (key._2), '3': (key._3), '4': (key._4), '5': (key._5), '6': (key._6), '7': (key._7), '8': (key._8), '9': (key._9), '10': (key._0)}[key_string]
        self.scale = float(self.size) / self.image.width
        return

    def on_key_press(self, symbol, modifiers):
        if symbol != self.key:
            return
        self.pressed = True

    def on_key_release(self, symbol, modifiers):
        if symbol != self.key or not self.pressed:
            return
        self.fire_handlers()
        self.pressed = False

    def set_visible(self, value):
        self.visible = value

    def set_position(self, x, y):
        self.x = x
        self.y = y

    def draw(self):
        if not self.visible:
            return
        if self.pressed:
            image = self.pressed_image
        else:
            image = self.image
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        gl.glPushMatrix()
        gl.glTranslatef(self.x, self.y, 0.0)
        gl.glScalef(self.scale, self.scale, 1.0)
        image.blit(0.0, 0.0)
        gl.glPopMatrix()


class RangeControl(HandlerBase):
    value = None
    focus = False
    over = False
    width = 200
    height = 100
    normal_color = (127, 127, 127, 180)
    over_color = (140, 140, 140, 180)
    selected_color = (160, 160, 160, 180)
    characters = string.digits

    def initialize(self, value, x, y, width, size=15, start=0, end=99, step=1):
        self.step = step
        if isinstance(step, float):
            self.data_type = float
            self.characters += '.'
        else:
            self.data_type = int
        sign_width = 20
        self.x1 = x
        self.y1 = y
        self.x2 = x + width - sign_width
        self.width = width
        x_pad = 10
        x += x_pad
        self.label = label = Label(' ', x=x, y=y, font_name=START_FONT, font_size=size, anchor_x='left', anchor_y='bottom', width=width - x_pad * 2)
        self.label.set_horizontal_align('center')
        self.height = self.label.content_height
        self.y2 = self.y1 + self.height
        sign_size = 20
        sign_x = self.x1 + self.width - sign_width / 2.0
        self.sign_x1 = self.x1 + self.width - sign_width
        self.sign_x2 = self.sign_x1 + sign_width
        y += 4
        sign_y = y + 20
        self.forward_sign = global_images.up_arrow.copy()
        self.forward_sign.x = sign_x
        self.forward_sign.y = sign_y
        sign_y = y
        self.backward_sign = global_images.down_arrow.copy()
        self.backward_sign.x = sign_x
        self.backward_sign.y = sign_y
        self.backward_y1 = self.y1
        self.backward_y2 = self.y1 + self.height / 2.0
        self.forward_y1 = self.backward_y2
        self.forward_y2 = self.y2
        self.start = start
        self.end = end
        self.set_value(value)

    def set_value(self, value):
        old_value = self.value
        self.value = max(self.start, min(self.end, value))
        self.label.text = str(self.value)
        if self.value == self.end:
            self.forward_sign.opacity = 140
        else:
            self.forward_sign.opacity = 255
        if self.value == self.start:
            self.backward_sign.opacity = 140
        else:
            self.backward_sign.opacity = 255
        if old_value is not None:
            self.fire_handlers()
        return

    def update_over(self, x, y):
        self.over = collides(x, y, x, y, self.x1, self.y1, self.x2, self.y2)

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        self.update_over(x, y)

    def on_mouse_motion(self, x, y, dx, dy):
        self.update_over(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == mouse.LEFT:
            self.set_focus(self.over)
            if collides(x, y, x, y, self.sign_x1, self.forward_y1, self.sign_x2, self.forward_y2):
                self.set_value(self.value + self.step)
            elif collides(x, y, x, y, self.sign_x1, self.backward_y1, self.sign_x2, self.backward_y2):
                self.set_value(self.value - self.step)

    def on_text_motion(self, motion):
        if not self.focus:
            return
        if motion in (key.MOTION_BACKSPACE, key.MOTION_DELETE):
            self.label.text = self.label.text[:-1]

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if not self.over:
            return
        if scroll_y > 0:
            add = self.step
        elif scroll_y < 0:
            add = -self.step
        else:
            return
        self.set_value(self.value + add)

    def on_text(self, value):
        if not self.focus:
            return
        if value == u'\r':
            self.set_focus(False)
            return
        if value not in self.characters:
            return
        self.label.text += value
        if self.label.content_width > self.label.width:
            self.label.text = self.label.text[:-1]

    def set_focus(self, value):
        if self.focus == value:
            return
        self.focus = value
        if not self.focus:
            try:
                value = self.data_type(self.label.text)
            except ValueError:
                value = self.value

            self.set_value(value)

    def draw(self):
        if self.focus:
            color = self.selected_color
        elif self.over:
            color = self.over_color
        else:
            color = self.normal_color
        y_pad = 5
        draw_quad(self.x1, self.y1 - y_pad, self.width, self.height + y_pad * 2, color)
        self.label.draw()
        self.forward_sign.draw()
        self.backward_sign.draw()


class TextButton(HandlerBase):
    alpha = 255
    pressed = over = False

    def initialize(self, text, x, y, width, height, size=15, background=True, image=None, image_scale=1.0, border_scale=[1.0, 1.0], image_anchor=IMAGE_CENTRE, image_color=None, scale_on_hover=0.0):
        self.enabled = True
        self.visible = True
        self.draw_border = False
        self.border_scale = border_scale
        self.text = text.upper()
        self.x = x
        self.y = y
        if background:
            font_name = BUTTON_FONT
            color = BUTTON_COLOR
        else:
            font_name = ALDO_FONT
            color = MENU_FONT_COLOR2
        self.width = width
        self.height = height
        self.text_width = self.width - TEXT_BACKGROUND_SPACING * 2.0
        self.text_height = self.height - UI_CONTROL_SPACING * 2.0
        self.text_colour = color
        self.set_text(text)
        self.background = background
        self.image = image
        self.image_anchor = image_anchor
        self.image_scale = image_scale
        self.image_color = image_color
        self.scale_on_hover = scale_on_hover
        if self.image_color is not None:
            self.image_color = (
             self.image_color[0] / 255.0, self.image_color[1] / 255.0, self.image_color[2] / 255.0)
        self.glow = False
        self.add_glow = False
        self.glow_timer = None
        self.constant_glow = False
        self.tint = (1.0, 1.0, 1.0)
        return

    def set_text(self, text):
        self.text = text
        if self.text_height > 30:
            font = big_button_aldo_font
        else:
            font = medium_button_aldo_font
        self.font_to_use, self.lines = get_resized_font_and_formatted_text_to_fit_boundaries(text, self.text_width, self.text_height, font, 2)

    def set_constant_glow(self, value):
        self.constant_glow = value
        if self.constant_glow:
            self.glow = False

    def set_glow(self, value):
        self.glow = value
        if self.glow:
            self.glow_timer = time.time()
        else:
            self.glow_timer = None
        return

    def update(self):
        if self.glow_timer is not None:
            delta = time.time() - self.glow_timer
            if delta > 0.4:
                self.add_glow = not self.add_glow
                self.glow_timer = time.time()
        return

    def set_draw_border(self, value):
        self.draw_border = value

    def set_enabled(self, value):
        self.enabled = value
        if not value:
            self.pressed = self.over = False

    def set_visible(self, value):
        self.visible = value
        if not value:
            self.pressed = self.over = False

    def update_over(self, x, y):
        if not self.visible:
            return
        x1 = self.x
        y2 = self.y
        x2 = x1 + self.width
        y1 = y2 - self.height
        self.over = collides(x1, y1, x2, y2, x, y, x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.enabled and self.visible:
            self.pressed = True

    def on_mouse_motion(self, x, y, dx, dy):
        self.update_over(x, y)

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        self.update_over(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        if self.enabled and self.visible:
            self.update_over(x, y)
        if self.over and self.enabled and self.visible and self.pressed:
            self.fire_handlers()
        self.pressed = False

    def draw_button_border(self):
        pass

    def draw_button_background(self):
        pass

    def draw_image(self, add_y=0.0):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        if self.text is None or self.text == ' ':
            half_width = self.width * 0.5
            half_height = self.height * 0.5
            quarter_width = half_width * 0.5
            gl.glPushMatrix()
            if self.image_anchor == IMAGE_LEFT:
                gl.glTranslatef(self.x + half_width + quarter_width, self.y - half_height, 0.0)
            elif self.image_anchor == IMAGE_RIGHT:
                gl.glTranslatef(self.x + quarter_width, self.y - half_height, 0.0)
            else:
                gl.glTranslatef(self.x + half_width, self.y - half_height, 0.0)
            gl.glPushMatrix()
            if self.over or self.draw_border:
                gl.glScalef(self.image_scale + self.scale_on_hover, self.image_scale + self.scale_on_hover, 1.0)
            else:
                gl.glScalef(self.image_scale, self.image_scale, 1.0)
            if self.image_color is not None:
                gl.glColor4f(self.image_color[0], self.image_color[1], self.image_color[2], 1.0)
            self.image.blit(0.0, 0.0)
            gl.glPopMatrix()
            gl.glPopMatrix()
        else:
            width = self.text_width
            x = self.x + self.width / 2 - width / 2
            y1 = self.y - self.height
            self.image.blit(x - 2, y1 + self.height / 2 + 1 + add_y)
        return

    def draw(self):
        if not self.visible:
            return
        x1 = self.x
        y1 = self.y - self.height
        add_y = 0.0
        self.draw_button_background()
        if self.glow:
            left_image = global_images.button_ready_left
            mid_image = global_images.button_ready_mid
            right_image = global_images.button_ready_right
            if self.pressed and self.over:
                add_y = -2.0 * (self.height / float(mid_image.height))
        elif self.pressed and self.over:
            if self.constant_glow:
                left_image = global_images.button_glow_press_left
                mid_image = global_images.button_glow_press_mid
                right_image = global_images.button_glow_press_right
            else:
                left_image = global_images.button_press_left
                mid_image = global_images.button_press_mid
                right_image = global_images.button_press_right
            add_y = -2.0 * (self.height / float(mid_image.height))
        elif self.over:
            if self.constant_glow:
                left_image = global_images.button_glow_hover_left
                mid_image = global_images.button_glow_hover_mid
                right_image = global_images.button_glow_hover_right
            else:
                left_image = global_images.button_hover_left
                mid_image = global_images.button_hover_mid
                right_image = global_images.button_hover_right
        elif self.constant_glow:
            left_image = global_images.button_glow_left
            mid_image = global_images.button_glow_mid
            right_image = global_images.button_glow_right
        else:
            left_image = global_images.button_left
            mid_image = global_images.button_mid
            right_image = global_images.button_right
        if self.background:
            if self.enabled:
                mul = 1.0
            else:
                mul = 0.7
            tint = self.tint
            gl.glColor4f(tint[0] * mul, tint[1] * mul, tint[2] * mul, 1.0)
            height = self.height
            element_width = int(global_images.button_left.width / float(global_images.button_left.height) * height)
            left_image.blit(x1, y1, width=element_width + 1, height=height)
            x1 += element_width
            width = self.width - element_width * 2
            mid_image.blit(x1, y1, width=width + 1, height=height)
            x1 += width
            right_image.blit(x1, y1, width=element_width + 1, height=height)
            if self.glow and self.add_glow and self.constant_glow == False:
                scale_x = float(self.width + self.width * 0.2) / float(global_images.button_glow.width)
                scale_y = float(self.height + self.height * 0.75) / float(global_images.button_glow.height)
                gl.glPushMatrix()
                gl.glTranslatef(self.x + self.width / 2.0, self.y - self.text_height / 2.0, 0.0)
                gl.glScalef(scale_x, scale_y, 1.0)
                global_images.button_glow.blit(0, 0)
                gl.glPopMatrix()
        self.draw_button_border()
        if self.image:
            add_x = self.image.width * 0.5
            self.draw_image(add_y)
        else:
            add_x = 0
        x = self.x + TEXT_BACKGROUND_SPACING + add_x
        y = self.y - self.height + add_y + UI_CONTROL_SPACING
        draw_text_lines(self.lines, x, y, self.text_width, self.text_height, self.font_to_use, 2.0, self.text_colour, 'center', 'center')


class CustomButton(TextButton):

    def initialize(self, x, y, width, height, image=None, image_scale=1.0, border_scale=[1.0, 1.0], border_image=global_images.class_selected_frame, background_scale=[1.0, 1.0], background_image=global_images.loadout_item_background, button_image_colour=None, scale_image_on_hover=0.0, image_offset=[0.0, 0.0], background_image_disabled=global_images.loadout_item_background_disabled):
        super(CustomButton, self).initialize(' ', x, y, width, height, 15, False, image, image_scale, border_scale, image_color=button_image_colour, scale_on_hover=scale_image_on_hover)
        self.draw_background_image = False
        self.background_image = background_image
        self.background_image_disabled = background_image_disabled
        self.border_image = border_image
        self.image_offset = image_offset

    def draw_image(self, add_y=0.0):
        if self.image is None:
            return
        else:
            scale = self.image_scale
            if self.over or self.draw_border:
                scale += self.scale_on_hover
            gl.glColor4f(1.0, 1.0, 1.0, 1.0)
            gl.glPushMatrix()
            gl.glTranslatef(self.x + self.width * 0.5 + self.image_offset[0], self.y - self.height * 0.5 + self.image_offset[1], 0.0)
            gl.glScalef(scale, scale, 1.0)
            self.image.blit(0.0, 0.0)
            gl.glPopMatrix()
            return

    def draw_button_background(self):
        if self.draw_background_image == False or self.background_image is None:
            return
        x = self.x + self.width * 0.5
        y = self.y - self.height * 0.5
        if self.enabled:
            draw_image_resized(self.background_image, x, y, self.width, self.height, clear_colours=True)
        else:
            draw_image_resized(self.background_image_disabled, x, y, self.width, self.height, clear_colours=True)
        return

    def draw_button_border(self):
        if self.draw_border == False or self.border_image is None:
            return
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        x = self.x + self.width * 0.5
        y = self.y - self.height * 0.5
        gl.glPushMatrix()
        gl.glTranslatef(x, y, 0.0)
        gl.glScalef(self.border_scale[0], self.border_scale[1], 1.0)
        self.border_image.blit(0.0, 0.0)
        gl.glPopMatrix()
        return


NAVIGATION_BAR_PAD = 5
NAVBAR_MIDDLE = 0
NAVBAR_LEFT = 1
NAVBAR_RIGHT = 2

class NavigationBar(HandlerBase):
    over_middle = over_left = over_right = False
    pressed_middle = pressed_left = pressed_right = False
    left_button_text = None
    left_button_icon = None
    right_button_text = None
    right_button_icon = None
    middle_button_text = None
    middle_button_icon = None
    has_left_button = False
    has_right_button = False
    has_middle_button = False

    def initialize(self, x, y, width, height, middle_button=True, right_button=False, left_button=True):
        self.x, self.y = x, y
        self.width, self.height = width, height
        if middle_button:
            self.add_middle_button()
        if right_button:
            self.add_right_button()
        if left_button:
            self.add_left_button()

    def add_left_button(self, text=strings.BACK, image=global_images.back_icon):
        self.left_button_text = text
        self.left_button_icon = image
        self.has_left_button = True

    def add_right_button(self, text=strings.SELECT, image=global_images.right_icon):
        self.right_button_text = text
        self.right_button_icon = image
        self.has_right_button = True

    def add_middle_button(self, text=strings.MAIN_MENU, image=global_images.main_menu_icon):
        self.middle_button_text = text
        self.middle_button_icon = image
        self.has_middle_button = True

    def draw(self):
        mid_y = self.y + self.height / 2
        if self.has_left_button:
            left_y_add = -1 if self.over_left and self.pressed_left else 0
            y = mid_y + left_y_add
            width = self.get_width(self.left_button_text, self.left_button_icon)
            self.draw_item(self.left_button_text, self.left_button_icon, y, width, NAVBAR_LEFT, self.over_left)
        if self.has_middle_button:
            width = self.get_width(self.middle_button_text, self.middle_button_icon)
            self.draw_item(self.middle_button_text, self.middle_button_icon, mid_y, width, NAVBAR_MIDDLE, self.over_middle)
        if self.has_right_button:
            right_y_add = -1 if self.over_right and self.pressed_right else 0
            y = mid_y + right_y_add
            width = self.get_width(self.right_button_text, self.right_button_icon)
            self.draw_item(self.right_button_text, self.right_button_icon, y, width, NAVBAR_RIGHT, self.over_right)

    def update_over(self, x, y):
        self.over_middle = False
        self.over_left = False
        self.over_right = False
        y1 = self.y
        y2 = self.y + self.height
        if self.enabled == False:
            return
        if self.has_middle_button:
            width = self.get_width(self.middle_button_text, self.middle_button_icon)
            x1 = self.x + self.width / 2.0 - width / 2.0
            x2 = x1 + width
            self.over_middle = collides(x1, y1, x2, y2, x, y, x, y)
            if self.over_middle:
                return
        if self.has_left_button:
            width = self.get_width(self.left_button_text, self.left_button_icon)
            x1 = self.x
            x2 = x1 + width
            self.over_left = collides(x1, y1, x2, y2, x, y, x, y)
            if self.over_left:
                return
        if self.has_right_button:
            width = self.get_width(self.right_button_text, global_images.back_icon)
            x1 = self.x + self.width - width
            x2 = x1 + width
            self.over_right = collides(x1, y1, x2, y2, x, y, x, y)

    def on_mouse_motion(self, x, y, dx, dy):
        self.update_over(x, y)

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        self.update_over(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.over_left:
            self.pressed_left = True
        elif self.over_middle:
            self.pressed_middle = True
        elif self.has_right_button and self.over_right:
            self.pressed_right = True

    def on_mouse_release(self, x, y, button, modifiers):
        if self.over_left and self.pressed_left:
            self.fire_handlers(NAVBAR_LEFT)
        elif self.has_middle_button and self.over_middle and self.pressed_middle:
            self.fire_handlers(NAVBAR_MIDDLE)
        elif self.has_right_button and self.over_right and self.pressed_right:
            self.fire_handlers(NAVBAR_RIGHT)
        self.pressed_middle = self.pressed_left = self.pressed_right = False

    def get_width(self, name, image):
        font_width = navigation_font.get_content_width(name)
        width = font_width + NAVIGATION_BAR_PAD
        image_width = 0 if image is None else image.width
        return width + image_width

    def draw_item(self, name, image, y, width, button_position, over):
        name = name.upper() if name is not None else ''
        mul = 0.7
        if over:
            gl.glColor4f(1.0, 1.0, 1.0, 1.0)
            color = MENU_FONT_COLOR2
        else:
            gl.glColor4f(mul, mul, mul, 1.0)
            color = multiply_color(MENU_FONT_COLOR2[:-1], mul) + (255, )
        text_x = self.x
        text_y = self.y
        image_x = self.x
        image_y = y
        image_width = 0 if image is None else image.width
        if button_position == NAVBAR_MIDDLE:
            x = self.x + self.width / 2.0
            if image is None:
                text_x = x - width / 2.0
            else:
                image_x = x - width / 2.0
                text_x = image_x + image_width + NAVIGATION_BAR_PAD / 2.0
        elif button_position == NAVBAR_RIGHT:
            x = self.x + self.width
            if image is None:
                text_x = x - NAVIGATION_BAR_PAD - width
            else:
                image_x = x - NAVIGATION_BAR_PAD - image_width
                text_x = image_x - NAVIGATION_BAR_PAD / 2.0 - (width - image_width)
                image_x += image_width / 2.0
        elif button_position == NAVBAR_LEFT:
            x = self.x + NAVIGATION_BAR_PAD / 2.0
            image_x = x
            text_x = image_x + image_width + NAVIGATION_BAR_PAD / 2.0
            image_x += image_width / 2.0
        if name is not None:
            draw_text_with_alignment_and_size_validation(name, text_x, self.y, width, self.height, color, navigation_font, alignment_x='left', alignment_y='center')
        if image is not None:
            image.blit(image_x, image_y)
        return


def create_medium_navbar():
    return NavigationBar(54, 74, 695, 32)


def create_small_navbar():
    pass


def create_large_navbar(has_middle_button=False, right_button=False):
    return NavigationBar(54, 27, 695, 32, has_middle_button, right_button)


class ListItem(object):
    image = None

    def __init__(self, labels, **kw):
        self.labels = labels
        for k, v in kw.iteritems():
            setattr(self, k, v)


SCROLL_BAR_SIZE = 18
SCROLL_ARROW_SIZE = 20
SCROLL_BAR_WIDTH = 12
SCROLL_BAR_COLOR1 = (40, 40, 40, 255)
SCROLL_BAR_COLOR2 = (150, 150, 150, 255)
SCROLL_BUTTON_COLOR1 = (80, 80, 80, 255)
SCROLL_BUTTON_COLOR2 = (170, 170, 170, 255)
SCROLL_BUTTON_HEIGHT = 60
SCROLL_BAR_BACKCOLOR = (200, 200, 200, 255)
CATEGORY_HEIGHT = 27
SELECTED_COLOR = (
 247, 210, 51, 255)

class ListGrid(HandlerBase):
    alpha = 255
    selected = None
    over = None
    scroll_y = 0
    selected_column = column_index = None
    column_reversed = False
    max_lines = None
    scrolling = False
    displayed_lines = None
    pressed = False
    sign_width = 16

    def initialize(self, x, y, width, height, columns, selected_column_index=None):
        alpha = self.alpha / 255.0
        self.x = x
        self.y = y
        self.bottom_y = y - height
        self.left_x = x + width - SCROLL_BAR_SIZE
        self.width = width - SCROLL_BAR_SIZE
        self.full_height = height
        self.height = height - CATEGORY_HEIGHT
        self.lines = []
        self.columns = []
        self.item_offset_x = 4
        self.scroll_bar_offset_x = 31
        self.right_selectable_edge_x = self.x + self.scroll_bar_offset_x + self.width - (SCROLL_ARROW_SIZE - SCROLL_BAR_SIZE) / 2
        column_x = self.item_offset_x
        for column, width in columns:
            label = Label(column, x=column_x, y=-2, width=width - self.sign_width, font_size=10, font_name=EDO_FONT, color=MENU_FONT_COLOR, anchor_y='top')
            label.sign = None
            label.set_vertical_align('center')
            label.width = width - self.sign_width
            label.height = label.content_height + LINE_PAD
            label.x1 = column_x
            label.x2 = label.x1 + width - self.sign_width
            self.columns.append(label)
            column_x += width

        x = SCROLL_BAR_SIZE / 2.0 + self.scroll_bar_offset_x
        y = -SCROLL_BAR_SIZE / 2.0 + height
        self.up_sign = SquareButton(global_images.up_arrow, x, y, SCROLL_ARROW_SIZE)
        self.up_sign.add_handler(self.on_up)
        y = SCROLL_BAR_SIZE / 2.0
        self.down_sign = SquareButton(global_images.down_arrow, x, y, SCROLL_ARROW_SIZE)
        self.down_sign.add_handler(self.on_down)
        self.hidden_lines = set()
        self.elements = (self.up_sign, self.down_sign)
        if selected_column_index is not None:
            self.select_column(selected_column_index)
        self.row_height = None
        return

    def on_up(self):
        self.set_scroll(int(self.scroll_y) - 1)

    def on_down(self):
        self.set_scroll(int(self.scroll_y) + 1)

    def add_line(self, values, **kw):
        labels = []
        label_height = None
        for index, entry in enumerate(values):
            if hasattr(entry, '__iter__'):
                text, sort_key = entry
            else:
                text = sort_key = entry
            column_x = self.columns[index].x
            label = Label(text, x=column_x, y=1, font_name=CHAT_FONT, font_size=10, width=self.columns[index].width + self.sign_width - 8)
            label.sort_key = sort_key
            label.anchor_y = 'top'
            label.content_valign = 'center'
            label.width = self.columns[index].width + self.sign_width
            label.height = label.content_height + LINE_PAD
            labels.append(label)
            if text and label_height is None:
                label_height = label.height
                self.row_height = label_height

        if self.max_lines is None and label_height is not None:
            self.max_lines = int(self.height / (label_height - 2))
        line = ListItem(labels, **kw)
        self.lines.append(line)
        if self.column_index is not None:
            self.resort()
        return line

    def get_lines(self):
        lines = self.displayed_lines
        if lines is None:
            return self.lines
        else:
            return lines

    def hide(self, lines):
        self.hidden_lines.update(lines)
        self.update_displayed_lines()

    def show(self, lines):
        self.hidden_lines -= set(lines)
        self.update_displayed_lines()

    def update_displayed_lines(self):
        if not self.hidden_lines:
            self.displayed_lines = None
            return
        else:
            self.displayed_lines = self.lines[:]
            for line in self.hidden_lines:
                self.displayed_lines.remove(line)

            self.set_scroll(self.scroll_y)
            return

    def clear(self):
        self.lines = []
        self.hidden_lines = set()
        self.scroll_y = 0
        self.selected = self.over = self.displayed_lines = None
        self.fire_handlers()
        return

    def update_over(self, x, y):
        if not self.lines:
            return
        else:
            lines = self.get_lines()
            scroll_y = int(self.scroll_y)
            x1 = self.x
            x2 = self.right_selectable_edge_x
            min_item_index = scroll_y
            max_item_index = min_item_index + self.max_lines
            for index, item in enumerate(lines[min_item_index:max_item_index]):
                y2 = self.y - CATEGORY_HEIGHT - 1 - (item.labels[0].height - 2) * index
                y1 = y2 - item.labels[0].height
                if collides(x1, y1, x2, y2, x, y, x, y):
                    self.over = index + scroll_y
                    return

            self.over = None
            return

    def on_mouse_motion(self, x, y, dx, dy):
        element_x = x - self.left_x
        element_y = y - self.bottom_y
        for element in self.elements:
            element.on_mouse_motion(element_x, element_y, dx, dy)

        self.update_over(x, y)

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        element_x = x - self.left_x
        element_y = y - self.bottom_y
        for element in self.elements:
            element.on_mouse_drag(element_x, element_y, dx, dy, button, modifiers)

        if button != mouse.LEFT:
            return
        if self.scrolling:
            self.update_scrollbar_pos(x, y)
        else:
            self.update_over(x, y)
            self.update_selected()

    def update_scrollbar_pos(self, x, y):
        if not self.max_lines:
            return
        else:
            scroll_lines = len(self.get_lines()) - self.max_lines
            if scroll_lines <= 0:
                return
            height = self.full_height
            bar_height = height - SCROLL_BAR_SIZE * 2 - SCROLL_BUTTON_HEIGHT
            y = y - (self.bottom_y + SCROLL_BAR_SIZE) - SCROLL_BUTTON_HEIGHT / 2.0
            factor = (bar_height - y) / float(bar_height)
            self.set_scroll(factor * scroll_lines)
            return

    def update_selected(self):
        if self.over is not None:
            self.selected = self.over
            self.fire_handlers()
            return True
        else:
            return False

    def on_mouse_press(self, x, y, button, modifiers):
        element_x = x - self.left_x
        element_y = y - self.bottom_y
        for element in self.elements:
            element.on_mouse_press(element_x, element_y, button, modifiers)

        if button != mouse.LEFT:
            return
        self.pressed = True
        if self.update_selected():
            return
        if self.check_column(x, y):
            return
        if self.check_scrollbar(x, y):
            return

    def on_mouse_release(self, x, y, button, modifiers):
        element_x = x - self.left_x
        element_y = y - self.bottom_y
        for element in self.elements:
            element.on_mouse_release(element_x, element_y, button, modifiers)

        if button != mouse.LEFT:
            return
        self.scrolling = self.pressed = False

    def select_column(self, column_index):
        if column_index is None or column_index < 0 or column_index >= len(self.columns) or len(self.lines) == 0:
            for column in self.columns:
                column.sign = None
                column.color = MENU_FONT_COLOR

            return
        column = self.columns[column_index]
        if column == self.selected_column:
            self.column_reversed = not self.column_reversed
        elif self.selected_column is not None:
            self.selected_column.sign = None
            self.selected_column.color = MENU_FONT_COLOR
            self.column_reversed = False
        self.selected_column = column
        self.column_index = column_index
        if self.column_reversed:
            sign = global_images.filter_down
        else:
            sign = global_images.filter_up
        column.sign = sign
        column.color = SELECTED_COLOR
        self.resort()
        return

    def check_column(self, x, y):
        x1 = self.x
        x2 = self.right_selectable_edge_x
        y1 = self.y - CATEGORY_HEIGHT
        y2 = self.y
        if not collides(x1, y1, x2, y2, x, y, x, y):
            return False
        x = x - x1
        for column_index, column in enumerate(self.columns):
            if x < column.x2 - self.item_offset_x:
                break
        else:
            return True

        self.select_column(column_index)
        return True

    def check_scrollbar(self, x, y):
        y1 = self.bottom_y + SCROLL_BAR_SIZE
        y2 = y1 + self.full_height - SCROLL_BAR_SIZE * 2
        x1 = self.x + self.scroll_bar_offset_x + self.width
        x2 = x1 + SCROLL_BAR_SIZE
        if collides(x, y, x, y, x1, y1, x2, y2):
            self.scrolling = True
            self.update_scrollbar_pos(x, y)
            return True
        return False

    def resort(self):
        selected_line = None
        if self.selected:
            selected_line = self.lines[self.selected]
        column_index = self.column_index
        reverse = self.column_reversed
        self.lines.sort(key=(lambda item: item.labels[column_index].sort_key), reverse=reverse)
        self.update_displayed_lines()
        if selected_line is not None:
            for index, line in enumerate(self.lines):
                if line == selected_line:
                    self.selected = index
                    self.fire_handlers()
                    break

        return

    def set_scroll(self, value):
        if self.max_lines is not None:
            value = min(value, len(self.get_lines()) - self.max_lines)
        self.scroll_y = max(0, value)
        return

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        scroll_y = int(scroll_y)
        self.set_scroll(int(self.scroll_y) - scroll_y)
        if self.pressed:
            self.update_selected()

    def get_scrollbar_y(self):
        if not self.max_lines:
            return None
        else:
            scroll_lines = len(self.get_lines()) - self.max_lines
            if scroll_lines <= 0:
                return None
            bar_height = self.full_height - SCROLL_BAR_SIZE * 2
            scroll_height = (bar_height - SCROLL_BUTTON_HEIGHT) * (float(self.scroll_y) / scroll_lines)
            return bar_height - scroll_height + SCROLL_BAR_SIZE - SCROLL_BUTTON_HEIGHT

    def draw(self):
        from aoslib.text import draw_text_with_size_validation
        gl.glPushMatrix()
        gl.glTranslatef(self.x + self.width, self.bottom_y, 0.0)
        height = self.full_height
        draw_quad(self.scroll_bar_offset_x, SCROLL_BAR_SIZE, SCROLL_BAR_SIZE, height - SCROLL_BAR_SIZE * 2, (0,
                                                                                                             0,
                                                                                                             0,
                                                                                                             255))
        scroll_y = self.get_scrollbar_y()
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        if scroll_y is not None:
            element_height = int(global_images.scroll_bottom.height / float(global_images.scroll_bottom.width) * SCROLL_BAR_SIZE)
            y = scroll_y
            x = float(self.scroll_bar_offset_x) + 3.5
            global_images.scroll_bottom.blit(x, y, width=SCROLL_BAR_WIDTH, height=element_height + 1)
            y += element_height
            global_images.scroll_mid.blit(x, y, width=SCROLL_BAR_WIDTH, height=SCROLL_BUTTON_HEIGHT - element_height * 2 + 1)
            y += SCROLL_BUTTON_HEIGHT - element_height * 2
            global_images.scroll_top.blit(x, y, width=SCROLL_BAR_WIDTH, height=element_height)
        for element in self.elements:
            element.draw()

        gl.glPopMatrix()
        gl.glPushMatrix()
        gl.glTranslatef(self.x, self.y, 0)
        for item in self.columns:
            draw_text_with_alignment_and_size_validation(item._text, item.x, item.y - item.height, item.width, item.height, item.color, item.font, alignment_x='left', alignment_y='center')
            if not item.sign:
                continue
            sign_offset = min(item.content_width, item.width) + 7
            item.sign.blit(item.x + sign_offset, -item.height * 0.5 - 1)

        gl.glTranslatef(0.0, -CATEGORY_HEIGHT, 0.0)
        total_height = self.height
        over = self.over
        scroll_y = int(self.scroll_y)
        if over is not None:
            over += scroll_y
        lines = self.get_lines()
        background_colors = [(72, 68, 54, 255), (47, 45, 36, 255)]
        color_index = 0
        for index, item in enumerate(lines[scroll_y:], scroll_y):
            height = item.labels[0].height - 2
            if index == self.selected:
                color = (255, 255, 255, 100)
            elif index == self.over:
                color = (255, 255, 255, 50)
            else:
                color = None
            x = self.item_offset_x
            for column_index, label in enumerate(item.labels):
                row_x = self.columns[column_index].x - x
                row_width = self.columns[column_index].width - 1 + self.sign_width
                draw_quad(row_x, -height, row_width, height, background_colors[color_index])
                draw_text_with_alignment_and_size_validation(label._text, label.x, label.y - label.height, label.width, label.height, label.color, label.font, alignment_x='left', alignment_y='center')
                row_x += row_width

            if color is not None:
                draw_quad(0, -height, self.width + 30, height, color)
            color_index += 1
            if color_index == len(background_colors):
                color_index = 0
            image = item.image
            if image:
                column = self.columns[1]
                label = item.labels[0]
                image.blit(column.x - image.width, -label.height / 2 + 2)
            gl.glTranslatef(0.0, -height, 0.0)
            total_height -= height
            if total_height <= height:
                break

        gl.glPopMatrix()
        return

    def is_over(self):
        return self.over is not None

    def get_selected(self):
        try:
            return self.get_lines()[self.selected]
        except (IndexError, TypeError):
            return

        return


class ScrollBar(HandlerBase):

    def initialize(self, x, y, width, height, max_lines, noof_visible_lines, button_size=22):
        self.bar_thickness = button_size - 2
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.scroll_pos = 0
        self.scroll_pos_float = 0.0
        self.bar_x = self.x
        self.bar_y = self.y
        self.button_size = button_size
        self.elements = (self.inc_button, self.dec_button)
        self.max_lines = max_lines
        self.noof_visible_lines = max(noof_visible_lines, 0)
        self.button_bar_gap = 2
        self.fixup_props()
        self.scrolling = False
        self.mouse_pos = 0.0
        self.on_bar_scrolled = None
        self.focus = True
        return

    def set_max_lines(self, max_lines):
        if self.max_lines == max_lines:
            return
        self.max_lines = max_lines
        self.fixup_props()
        self.update_bar_on_scroll()

    def set_visible_lines(self, visible_lines):
        if self.noof_visible_lines == visible_lines:
            return
        self.noof_visible_lines = visible_lines
        self.fixup_props()
        self.update_bar_on_scroll()

    def fixup_props(self):
        self.max_scroll = max(self.max_lines - self.noof_visible_lines, 0)
        percentage = 100
        if self.max_lines != 0.0:
            percentage = 100 * self.noof_visible_lines / float(self.max_lines)
        if percentage > 100:
            percentage = 100
        self.bar_full_length = self.length - self.button_size * 2 - self.button_bar_gap * 2
        self.bar_current_length = math.floor(self.bar_full_length * percentage / 100.0)
        if self.bar_current_length > 0:
            scale_thickness = float(self.bar_thickness) / float(global_images.scroll_bar_mid.width)
            top_height = float(global_images.scroll_bar_top.height) * scale_thickness
            bottom_height = float(global_images.scroll_bar_top.height) * scale_thickness
            length_of_bevels = math.floor(top_height + bottom_height)
            if self.bar_current_length < length_of_bevels:
                if length_of_bevels < self.bar_full_length:
                    self.bar_current_length = length_of_bevels
                else:
                    print "Scrollbars too short to contain the bevel-end images of the bar won't look good. length = ", self.length, 'bar_full_length = ', self.bar_full_length
        length_diff = self.bar_full_length - self.bar_current_length
        if self.high_coord_for_low_pos:
            self.bar_coord_at_max = self.origin_coord + self.button_size + self.button_bar_gap - 1
            self.bar_coord_at_min = self.bar_coord_at_max + length_diff
        else:
            self.bar_coord_at_min = self.origin_coord + self.button_size + self.button_bar_gap - 1
            self.bar_coord_at_max = self.bar_coord_at_min + length_diff
        self.update_buttons()

    def set_enabled(self, enabled):
        self.enabled = enabled
        self.inc_button.set_enabled(enabled)
        self.dec_button.set_enabled(enabled)
        self.update_buttons()

    def update_buttons(self):
        if self.enabled:
            self.dec_button.enabled = self.scroll_pos_float > 0 if self.noof_visible_lines > 0 else False
            self.inc_button.enabled = self.scroll_pos_float < self.max_scroll if self.noof_visible_lines > 0 else False

    def is_disabled(self):
        return not self.enabled or self.dec_button.enabled == False and self.inc_button.enabled == False

    def add_on_scrolled_handler(self, handler):
        self.on_bar_scrolled = handler

    def on_dec(self):
        if self.bar_current_length == self.bar_full_length:
            return
        if self.dec_button.enabled is False:
            return
        self.set_scroll(int(self.scroll_pos) - 1)
        self.update_bar_on_scroll()

    def on_inc(self):
        if self.bar_current_length == self.bar_full_length:
            return
        if self.inc_button.enabled is False:
            return
        self.set_scroll(int(self.scroll_pos) + 1)
        self.update_bar_on_scroll()

    def update_bar_on_scroll(self):
        pass

    def get_bar_coord_for_scroll_pos(self, scroll_pos_float):
        if scroll_pos_float <= 0:
            return self.bar_coord_at_min
        else:
            if scroll_pos_float >= self.max_scroll:
                return self.bar_coord_at_max
            return self.bar_coord_at_min + scroll_pos_float * (self.bar_coord_at_max - self.bar_coord_at_min) / float(self.max_scroll)

    def set_scroll(self, value, force_callback_call=False, silent=False, set_as_int=True):
        previous_scroll = self.scroll_pos
        self.scroll_pos_float = value
        if set_as_int:
            scroll_int = max(0, value)
            scroll_int = min(self.max_scroll, scroll_int)
        elif value <= 0.0:
            scroll_int = 0
        elif value >= float(self.max_scroll):
            scroll_int = self.max_scroll
        else:
            scroll_int = int(1 + value * (self.max_scroll - 1) / self.max_scroll)
        if previous_scroll != scroll_int or force_callback_call:
            if self.on_bar_scrolled is not None:
                self.on_bar_scrolled(scroll_int, silent=silent)
        self.scroll_pos = scroll_int
        self.update_buttons()
        self.update_bar_on_scroll()
        return

    def draw(self):
        pass

    def update_scroll_bar_position(self, coord, silent=False):
        if self.bar_coord_at_max - self.bar_coord_at_min == 0:
            return
        new_coord = math.floor(coord - self.bar_current_length / 2)
        if self.high_coord_for_low_pos:
            new_coord = min(self.bar_coord_at_min, new_coord)
            new_coord = max(new_coord, self.bar_coord_at_max)
        else:
            new_coord = max(self.bar_coord_at_min, new_coord)
            new_coord = min(new_coord, self.bar_coord_at_max)
        new_scroll = float(new_coord - self.bar_coord_at_min) * float(self.max_scroll) / float(self.bar_coord_at_max - self.bar_coord_at_min)
        self.set_scroll(new_scroll, set_as_int=False, silent=silent)

    def on_mouse_motion(self, x, y, dx, dy):
        if not self.enabled:
            return
        for element in self.elements:
            element.on_mouse_motion(x, y, dx, dy)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        pass


class VerticalScrollBar(ScrollBar):

    def initialize(self, x, y, width, height, max_lines, noof_visible_lines, button_size=22):
        x = math.floor(x)
        y = math.floor(y)
        height = math.floor(height)
        self.length = height
        self.origin_coord = y
        self.high_coord_for_low_pos = True
        half_button_size = button_size / 2
        self.dec_button = SquareButton(global_images.up_arrow, x, y + height - half_button_size, button_size)
        self.dec_button.add_handler(self.on_dec)
        self.inc_button = SquareButton(global_images.down_arrow, x, y + half_button_size, button_size)
        self.inc_button.add_handler(self.on_inc)
        super(VerticalScrollBar, self).initialize(x, y, width, height, max_lines, noof_visible_lines, button_size)

    def draw(self):
        width = self.dec_button.size
        draw_quad(self.x - width / 2, self.y, width, self.height, BLACK_COLOUR)
        half_bar_thickness = self.bar_thickness / 2
        draw_quad(self.x - half_bar_thickness, self.y + self.button_size + self.button_bar_gap, self.bar_thickness, self.bar_full_length, (73,
                                                                                                                                           63,
                                                                                                                                           7,
                                                                                                                                           255))
        for element in self.elements:
            element.draw()

        if not self.enabled:
            return
        scale_thickness = float(self.bar_thickness) / float(global_images.scroll_bar_mid.width)
        top_height = float(global_images.scroll_bar_top.height) * scale_thickness
        bottom_height = float(global_images.scroll_bar_top.height) * scale_thickness
        scale_length = (float(self.bar_current_length) - top_height * 0.5 - bottom_height * 0.5) / float(global_images.scroll_bar_mid.height)
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        bar_coord = self.get_bar_coord_for_scroll_pos(self.scroll_pos_float)
        gl.glPushMatrix()
        gl.glTranslatef(self.bar_x, bar_coord + bottom_height, 0)
        gl.glScalef(scale_thickness, scale_length, 0.0)
        global_images.scroll_bar_mid.blit(0, 0)
        gl.glPopMatrix()
        gl.glPushMatrix()
        gl.glTranslatef(self.bar_x, bar_coord + self.bar_current_length - top_height * 0.5, 0)
        gl.glScalef(scale_thickness, scale_thickness, 0.0)
        global_images.scroll_bar_top.blit(0, 0)
        gl.glPopMatrix()
        gl.glPushMatrix()
        gl.glTranslatef(self.bar_x, bar_coord + bottom_height * 0.5, 0)
        gl.glScalef(scale_thickness, scale_thickness, 0.0)
        global_images.scroll_bar_bottom.blit(0, 0)
        gl.glPopMatrix()

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        if not self.enabled:
            return
        for element in self.elements:
            element.on_mouse_drag(x, y, dx, dy, button, modifiers)

        if button != mouse.LEFT:
            return
        if self.scrolling:
            self.update_scroll_bar_position(y, silent=True)

    def on_mouse_press(self, x, y, button, modifiers):
        if not self.enabled:
            return
        for element in self.elements:
            if element.over and element.enabled:
                element.on_mouse_press(x, y, button, modifiers)

        if self.bar_current_length != self.bar_full_length:
            x1 = self.bar_x - self.bar_thickness / 2
            y1 = self.get_bar_coord_for_scroll_pos(self.scroll_pos_float)
            x2 = x1 + self.bar_thickness
            y2 = y1 + self.bar_current_length
            if collides(x, y, x, y, x1, y1, x2, y2):
                self.scrolling = True
                self.mouse_y = y

    def on_mouse_release(self, x, y, button, modifiers):
        if self.enabled:
            for element in self.elements:
                if element.over:
                    element.on_mouse_release(x, y, button, modifiers)

            if self.scrolling == False and self.bar_current_length != self.bar_full_length:
                x1 = self.bar_x - self.bar_thickness / 2
                y1 = self.bar_coord_at_max
                x2 = x1 + self.bar_thickness
                y2 = self.bar_full_length + self.bar_coord_at_max
                if collides(x, y, x, y, x1, y1, x2, y2):
                    self.update_scroll_bar_position(y)
        self.scrolling = False

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if not self.enabled:
            return
        if self.focus:
            if scroll_y > 0:
                self.on_dec()
            else:
                self.on_inc()


class HorizontalScrollBar(ScrollBar):

    def initialize(self, x, y, width, height, max_lines, noof_visible_lines, button_size=22):
        x = math.floor(x)
        y = math.floor(y)
        width = math.floor(width)
        self.length = width
        self.origin_coord = x
        self.high_coord_for_low_pos = False
        half_button_size = button_size / 2
        self.inc_button = SquareButton(global_images.right_arrow, x + width - half_button_size, y, button_size)
        self.inc_button.add_handler(self.on_inc)
        self.dec_button = SquareButton(global_images.left_arrow, x + half_button_size, y, button_size)
        self.dec_button.add_handler(self.on_dec)
        super(HorizontalScrollBar, self).initialize(x, y, width, height, max_lines, noof_visible_lines, button_size)

    def draw(self):
        height = self.dec_button.size
        draw_quad(self.x, self.y - height / 2, self.width, height, BLACK_COLOUR)
        half_bar_thickness = self.bar_thickness / 2
        draw_quad(self.x + self.button_size + self.button_bar_gap, self.y - half_bar_thickness, self.bar_full_length, self.bar_thickness, (73,
                                                                                                                                           63,
                                                                                                                                           7,
                                                                                                                                           255))
        for element in self.elements:
            element.draw()

        if not self.enabled:
            return
        scale_thickness = float(self.bar_thickness) / float(global_images.scroll_bar_hmid.height)
        right_width = float(global_images.scroll_bar_right.width) * scale_thickness
        left_width = float(global_images.scroll_bar_left.width) * scale_thickness
        scale_length = (float(self.bar_current_length) - right_width * 0.5 - left_width * 0.5) / float(global_images.scroll_bar_hmid.width)
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        bar_coord = self.get_bar_coord_for_scroll_pos(self.scroll_pos_float)
        gl.glPushMatrix()
        gl.glTranslatef(bar_coord + right_width, self.bar_y, 0)
        gl.glScalef(scale_length, scale_thickness, 0.0)
        global_images.scroll_bar_hmid.blit(0, 0)
        gl.glPopMatrix()
        gl.glPushMatrix()
        gl.glTranslatef(bar_coord + self.bar_current_length - left_width * 0.5, self.bar_y, 0)
        gl.glScalef(scale_thickness, scale_thickness, 0.0)
        global_images.scroll_bar_right.blit(0, 0)
        gl.glPopMatrix()
        gl.glPushMatrix()
        gl.glTranslatef(bar_coord + right_width * 0.5, self.bar_y, 0)
        gl.glScalef(scale_thickness, scale_thickness, 0.0)
        global_images.scroll_bar_left.blit(0, 0)
        gl.glPopMatrix()

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        if not self.enabled:
            return
        for element in self.elements:
            element.on_mouse_drag(x, y, dx, dy, button, modifiers)

        if button != mouse.LEFT:
            return
        if self.scrolling:
            self.update_scroll_bar_position(x)

    def on_mouse_press(self, x, y, button, modifiers):
        if not self.enabled:
            return
        for element in self.elements:
            if element.over and element.enabled:
                element.on_mouse_press(x, y, button, modifiers)

        if self.bar_current_length != self.bar_full_length:
            x1 = self.get_bar_coord_for_scroll_pos(self.scroll_pos_float)
            y1 = self.bar_y - self.bar_thickness / 2
            x2 = x1 + self.bar_current_length
            y2 = y1 + self.bar_thickness
            if collides(x, y, x, y, x1, y1, x2, y2):
                self.scrolling = True
                self.mouse_pos = x

    def on_mouse_release(self, x, y, button, modifiers):
        if self.enabled:
            for element in self.elements:
                if element.over:
                    element.on_mouse_release(x, y, button, modifiers)

            if self.scrolling == False and self.bar_current_length != self.bar_full_length:
                x1 = self.bar_coord_at_min
                y1 = self.bar_y - self.bar_thickness / 2
                x2 = x1 + self.bar_full_length
                y2 = y1 + self.bar_thickness
                if collides(x, y, x, y, x1, y1, x2, y2):
                    self.update_scroll_bar_position(x)
        self.scrolling = False


class SliderOption(HandlerBase):

    def initialize(self, start_index, options, x, y, width, height, draw_background_frame=True, background_colour=(83, 83, 83, 255), media=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.options = options
        self.index = -1
        self.button_size = self.height - SLIDER_OPTION_SPACING * 2.0
        self.media = media
        button_left_x = self.x + SLIDER_OPTION_SPACING + self.button_size / 2.0
        button_right_x = self.x + self.width - self.button_size - SLIDER_OPTION_SPACING + self.button_size / 2.0
        button_y = self.y + SLIDER_OPTION_SPACING + self.button_size / 2.0
        self.left_button = SquareButton(global_images.left_arrow, button_left_x, button_y, self.button_size)
        self.left_button.add_handler(self.on_click, -1)
        self.right_button = SquareButton(global_images.right_arrow, button_right_x, button_y, self.button_size)
        self.right_button.add_handler(self.on_click, 1)
        self.set(start_index)
        self.elements = (self.left_button, self.right_button)
        self.set_position(x, y)
        self.draw_background_frame = draw_background_frame
        self.background_colour = background_colour
        self.frame_scale_x = float(self.width) / float(global_images.round_control_frame.width)
        self.frame_scale_y = float(self.height) / float(global_images.round_control_frame.height)

    def get_index_by_name(self, item_name):
        for index, option in enumerate(self.options):
            if option == item_name:
                return index

        return -1

    def set_enabled(self, enabled):
        self.enabled = enabled
        if self.enabled:
            self.update_buttons()
        else:
            self.left_button.enabled = False
            self.right_button.enabled = False

    def update_position(self, x, y, width, height):
        self.width = width
        self.height = height
        self.set_position(x, y)
        self.button_size = self.height - SLIDER_OPTION_SPACING * 2.0
        self.left_button.size = self.button_size
        self.right_button.size = self.button_size
        button_left_x = self.x + SLIDER_OPTION_SPACING + self.button_size / 2.0
        button_right_x = self.x + self.width - self.button_size - SLIDER_OPTION_SPACING + self.button_size / 2.0
        button_y = self.y + SLIDER_OPTION_SPACING + self.button_size / 2.0
        self.left_button.set_position(button_left_x, button_y)
        self.right_button.set_position(button_right_x, button_y)

    def get_value(self):
        if self.index >= 0 and self.index < len(self.options):
            return self.options[self.index]
        else:
            return

    def set_position(self, x, y):
        BAR_BORDER = 1
        self.x = x
        self.y = y
        self.x1 = x + 30 + BAR_BORDER
        self.y1 = y
        self.x2 = x + self.width - 30 - BAR_BORDER
        self.y2 = y + self.height - 2
        button_spacing = self.button_size / 2 + SLIDER_OPTION_SPACING
        self.left_button.set_position(x + button_spacing, y + button_spacing)
        self.right_button.set_position(x + self.width - button_spacing, y + button_spacing)

    def set(self, index):
        if index >= 0 and index < len(self.options):
            self.index = index
            self.update_buttons()

    def set_value(self, value):
        for index, item in enumerate(self.options):
            if item == value:
                self.set(index)
                return

    def on_click(self, value):
        if self.enabled == False:
            return
        if self.media:
            self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
        self.index += value
        noof_items = len(self.options)
        if self.index < 0:
            self.index = 0
        elif self.index >= noof_items:
            self.index = noof_items - 1
        self.fire_handlers(self.index, self.options[self.index])
        self.update_buttons()

    def update_buttons(self):
        noof_items = len(self.options)
        if noof_items > 1:
            self.left_button.enabled = self.index > 0
            self.right_button.enabled = self.index < noof_items - 1
        else:
            self.left_button.enabled = False
            self.right_button.enabled = False

    def draw(self):
        if self.draw_background_frame:
            draw_quad(self.x, self.y, self.width, self.height, (0, 0, 0, 255))
        x = math.floor(self.left_button.x2) + SLIDER_OPTION_BAR_BUTTON_SPACING
        y = self.y + SLIDER_OPTION_SPACING
        width = self.right_button.x1 - SLIDER_OPTION_BAR_BUTTON_SPACING - x
        height = self.height - SLIDER_OPTION_SPACING * 2
        draw_quad(x, y, width, height, self.background_colour)
        if self.height >= MINIMUM_HEIGHT_FOR_MEDIUM_FONT:
            font = medium_aldo_ui_font
        else:
            font = small_aldo_ui_font
        if self.index > -1:
            width -= SLIDER_OPTION_SPACING * 2.0
            x += SLIDER_OPTION_SPACING
            text = unicode(self.options[self.index]).upper()
            draw_text_with_alignment_and_size_validation(text, x, self.y, width, self.height, MENU_FONT_COLOR, font, alignment_y='center')
        for element in self.elements:
            element.draw()

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        for element in self.elements:
            element.on_mouse_drag(x, y, dx, dy, button, modifiers)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.enabled == False:
            return
        for element in self.elements:
            if element.over:
                element.on_mouse_press(x, y, button, modifiers)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.enabled == False:
            return
        for element in self.elements:
            element.on_mouse_motion(x, y, dx, dy)

    def on_mouse_release(self, x, y, button, modifiers):
        if self.enabled == False:
            return
        for element in self.elements:
            element.on_mouse_release(x, y, button, modifiers)


class TextList(HandlerBase):

    def initialize(self, text_list, selected_page_index, x, y, width, height, items_per_page, header_height, header_text):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text_list = text_list if text_list is not None else []
        self.items_per_page = items_per_page if items_per_page > 0 else 1
        self.header_height = header_height
        self.header_text = header_text
        noof_items = len(self.text_list)
        if selected_page_index >= 0 and selected_page_index < noof_items:
            self.current_page_index = selected_page_index
        else:
            self.current_page_index = 0
        noof_pages = int(math.ceil(float(noof_items) / float(self.items_per_page)))
        self.min_page_index = self.current_page_index
        self.max_page_index = max(noof_pages - 1, 0)
        self.navigation_bar_height = 25
        self.left_button = SquareButton(global_images.left_arrow, x + 15, y + 14, self.navigation_bar_height)
        self.left_button.add_handler(self.on_click, -1)
        self.right_button = SquareButton(global_images.right_arrow, x + width - 16, y + 14, self.navigation_bar_height)
        self.right_button.add_handler(self.on_click, 1)
        self.set(self.current_page_index)
        self.elements = (self.left_button, self.right_button)
        self.set_position(x, y)
        return

    def set_enabled(self, enabled):
        self.enabled = enabled
        if self.enabled:
            self.update_buttons()
        else:
            for element in self.elements:
                element.enabled = False

    def set_position(self, x, y):
        self.x = x
        self.y = y
        self.x1 = x + 30 + BAR_BORDER
        self.y1 = y
        self.x2 = x + self.width - 30 - BAR_BORDER
        self.y2 = y + self.height - 2
        self.left_button.set_position(x + 15, y + 14)
        self.right_button.set_position(x + self.width - 16, y + 14)

    def set(self, index):
        self.current_page_index = index
        self.update_buttons()

    def on_click(self, value):
        if self.enabled == False:
            return
        self.current_page_index += value
        noof_items = math.ceil(float(len(self.text_list)) / float(self.items_per_page))
        if self.current_page_index < 0:
            self.current_page_index = 0
        elif self.current_page_index >= noof_items:
            self.current_page_index = noof_items - 1
        self.update_buttons()

    def update_buttons(self):
        noof_items = math.ceil(float(len(self.text_list)) / float(self.items_per_page))
        if noof_items > 1:
            self.left_button.enabled = self.current_page_index > 0
            self.right_button.enabled = self.current_page_index < noof_items - 1
        else:
            self.left_button.enabled = False
            self.right_button.enabled = False

    def draw(self):
        spacing_x = 20
        spacing_x_half = 10
        spacing_y = 10
        spacing_y_half = 5
        y = self.y + self.navigation_bar_height + spacing_y
        height = self.height - self.navigation_bar_height - spacing_y - spacing_y_half
        draw_quad(self.x, y, self.width, height, (0, 0, 0, 255))
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        width = self.width - spacing_x_half
        header_scale_x = float(width) / float(global_images.panel_header_dark_frame.width)
        header_scale_y = float(self.header_height) / float(global_images.panel_header_dark_frame.height)
        x = self.x + self.width / 2
        y = self.y + self.height - self.header_height / 2 - spacing_y_half
        gl.glPushMatrix()
        gl.glTranslatef(x, y, 0)
        gl.glScalef(header_scale_x, header_scale_y, 0.0)
        global_images.panel_header_dark_frame.blit(0, 0)
        gl.glPopMatrix()
        width -= spacing_x
        x = self.x + spacing_x - 5
        height = self.header_height - spacing_y
        draw_text_with_size_validation(self.header_text, x, y - height / 2, width, height, MENU_FONT_COLOR, big_aldo_ui_font)
        y = self.y + self.height - self.header_height - spacing_y - 2
        text_list_height = self.height - self.header_height - spacing_y * (self.items_per_page + 2)
        line_height = float(text_list_height) / float(self.items_per_page)
        line_y = y - self.header_height / 2 - spacing_y_half
        min_index = self.current_page_index * self.items_per_page
        max_index = min_index + self.items_per_page - 1
        for index, text in enumerate(self.text_list):
            if index < min_index or index > max_index:
                continue
            draw_text_with_size_validation(text, x, line_y, width, line_height, MENU_FONT_COLOR, medium_aldo_ui_font)
            line_y -= line_height + 3

        draw_quad(self.x, self.y, self.width, self.navigation_bar_height + spacing_y_half, (0,
                                                                                            0,
                                                                                            0,
                                                                                            255))
        page_text = ('{0}/{1}').format(self.current_page_index + 1, self.max_page_index + 1)
        width = width / 2
        x = self.x + self.width / 2 - width / 2
        y = self.y + 1
        draw_text_with_size_validation(page_text, x, y, width, self.navigation_bar_height - spacing_y, (255,
                                                                                                        255,
                                                                                                        255,
                                                                                                        255), medium_aldo_ui_font)
        for element in self.elements:
            element.draw()

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        for element in self.elements:
            element.on_mouse_drag(x, y, dx, dy, button, modifiers)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.enabled == False:
            return
        for element in self.elements:
            if element.over:
                element.on_mouse_press(x, y, button, modifiers)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.enabled == False:
            return
        for element in self.elements:
            element.on_mouse_motion(x, y, dx, dy)

    def on_mouse_release(self, x, y, button, modifiers):
        if self.enabled == False:
            return
        for element in self.elements:
            if element.over:
                element.on_mouse_release(x, y, button, modifiers)
