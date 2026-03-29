from aoslib.gui import HandlerBase
from aoslib.common import collides
from aoslib.images import global_images
from aoslib.text import draw_text_with_size_validation, get_resized_font_and_formatted_text_to_fit_boundaries, big_standard_ui_font, medium_standard_ui_font, small_standard_ui_font
from aoslib.draw import draw_quad
from pyglet import gl
from shared.constants import MENU_FONT_COLOR
from shared.hud_constants import MINIMUM_HEIGHT_FOR_BIG_FONT, MINIMUM_HEIGHT_FOR_MEDIUM_FONT, TEXT_BACKGROUND_SPACING
from aoslib.media import HUD_AUDIO_ZONE

class ListPanelItemBase(HandlerBase):

    def initialize(self, name=None, x=0, y=0, width=10, height=10, uid=None):
        self.elements = []
        self.enabled = True
        self._is_selected = False
        self._is_hovered = False
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height
        self.pad_x = 2
        self.width = width
        self.height = height
        self.highlight_width = width
        self.highlight_height = height
        self.name = name
        self.hovered_colour = (175, 172, 161, 255)
        self.background_colour = (0, 0, 0, 255)
        self.text_colour = MENU_FONT_COLOR
        self.small_font = small_standard_ui_font
        self.medium_font = medium_standard_ui_font
        self.big_font = big_standard_ui_font
        self.font = self.medium_font
        self.pad = height * 0.03
        self.glow_pad_x = 1.0
        self.glow_pad_y = 1.0
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.glow_scale_x = 1.0
        self.glow_scale_y = 1.0
        self.visible = True
        self.selectable_row = True
        self.center_text = True
        self.spacing = self.width * 0.02
        self.set_font_for_row_height()
        self.spacing_colour = (0, 0, 0, 0)
        self.spacing_size = 0
        self.draw_spacing = False
        self.uid = uid
        self.silent_control = False
        self.enable_on_scroll = True

    def get_is_selected(self):
        return self._is_selected

    def get_is_hovered(self):
        return self._is_hovered

    def set_hovered(self, hovered):
        self._is_hovered = hovered

    def set_selected(self, selected, media):
        if self.is_selectable():
            if media and selected and not self.silent_control:
                media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
            self._is_selected = selected

    def enable_draw_spacing(self, draw_spacing=False, spacing_size=0, spacing_colour=(0, 0, 0, 0)):
        self.draw_spacing = draw_spacing
        self.spacing_colour = spacing_colour
        self.spacing_size = spacing_size

    def is_same_item(self, item):
        if item is None:
            return False
        else:
            if self.uid is not None:
                return self.uid == item.uid
            else:
                return self.name == item.name

            return

    def is_selectable(self):
        return self.selectable_row

    def set_font_for_row_height(self):
        if self.height >= MINIMUM_HEIGHT_FOR_BIG_FONT:
            self.font = self.big_font
        elif self.height >= MINIMUM_HEIGHT_FOR_MEDIUM_FONT:
            self.font = self.medium_font
        else:
            self.font = self.small_font

    def get_pad_x_for_width(self, width):
        return width / 24.0

    def update_position(self, x, y, width, height, highlight_width):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.pad = height * 0.03
        self.y2 = y + height
        self.width = width
        self.height = height
        self.highlight_width = highlight_width
        self.spacing = self.width * 0.02
        self.pad_x = self.get_pad_x_for_width(self.width)
        self.glow_pad_x = self.width * 0.05
        self.glow_pad_y = self.height * 0.3
        self.scale_x = float(self.width) / float(global_images.green_highlight_line.width)
        self.scale_y = float(self.height) / float(global_images.green_highlight_line.height)
        self.glow_scale_x = float(self.width + self.glow_pad_x) / float(global_images.green_highlight_glow.width)
        self.glow_scale_y = float(self.height + self.glow_pad_y) / float(global_images.green_highlight_glow.height)
        text_width = width - self.pad * 2
        text_height = height - self.pad * 2
        self.set_font_for_row_height()
        self.font, lines = get_resized_font_and_formatted_text_to_fit_boundaries(self.name, text_width, text_height, self.font, 1)

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        for element in self.elements:
            element.on_mouse_drag(x, y, dx, dy, button, modifiers)

    def on_mouse_press(self, x, y, button, modifiers):
        for element in self.elements:
            element.on_mouse_press(x, y, button, modifiers)

    def mouse_collides(self, x, y):
        return collides(self.x1, self.y1, self.x2, self.y2, x, y, x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        for element in self.elements:
            element.on_mouse_release(x, y, button, modifiers)

    def on_mouse_motion(self, x, y, dx, dy):
        for element in self.elements:
            element.on_mouse_motion(x, y, dx, dy)

    def on_key_press(self, symbol, modifiers):
        if not self.enabled:
            return
        for element in self.elements:
            element.on_key_press(symbol, modifiers)

    def on_text(self, value):
        if not self.enabled:
            return
        for element in self.elements:
            element.on_text(value)

    def on_text_motion(self, value):
        if not self.enabled:
            return
        for element in self.elements:
            element.on_text_motion(value)

    def get_text_y_position(self):
        if self.center_text:
            return self.y1 + float(self.height) / 2.0 - float(self.font.get_ascender() + self.font.get_descender()) / 2.0
        else:
            return self.y1 + float(self.height) / 2.0 - float(self.font.get_ascender() + self.font.get_descender()) / 2.0

    def get_text_x_position(self):
        if self.center_text:
            return self.x1 + self.pad
        else:
            return self.x1 + TEXT_BACKGROUND_SPACING

    def draw_name(self):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        text_width = self.width - self.pad * 2
        text_height = self.height - self.pad * 2
        x = self.get_text_x_position()
        y = self.get_text_y_position()
        draw_text_with_size_validation(self.name, x, y, text_width, text_height, self.text_colour, self.font, self.center_text)

    def draw_selection_highlight(self):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        gl.glPushMatrix()
        gl.glTranslatef(self.x1, self.y1, 0)
        gl.glScalef(self.scale_x, self.scale_y, 1.0)
        global_images.green_highlight_line.blit(0, 0)
        gl.glPopMatrix()
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        gl.glPushMatrix()
        gl.glTranslatef(self.x1 - self.glow_pad_x / 2, self.y1 - self.glow_pad_y / 2, 0)
        gl.glScalef(self.glow_scale_x, self.glow_scale_y, 1.0)
        global_images.green_highlight_glow.blit(0, 0)
        gl.glPopMatrix()

    def draw_hovered_highlight(self):
        draw_quad(self.x1, self.y1, self.width, self.height, self.hovered_colour)

    def draw_background(self, colour):
        draw_quad(self.x1, self.y1, self.width, self.height, colour)
        if self.draw_spacing:
            draw_quad(self.x1, self.y1 + self.height - self.spacing_size, self.width, self.spacing_size, self.spacing_colour)

    def draw_elements(self):
        for element in self.elements:
            element.draw()

    def draw(self, colour):
        if self.visible == False:
            return
        else:
            gl.glColor4f(1.0, 1.0, 1.0, 1.0)
            self.background_colour = colour
            self.draw_background(colour)
            if self._is_hovered and self.is_selectable():
                self.draw_hovered_highlight()
            if self._is_selected and self.is_selectable():
                self.draw_selection_highlight()
            if self.name is not None:
                self.draw_name()
            self.draw_elements()
            return
