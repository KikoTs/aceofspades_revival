from pyglet import gl
from aoslib.gui import HandlerBase, SquareButton
from aoslib.draw import draw_quad
from aoslib.text import draw_text_with_alignment_and_size_validation, medium_aldo_ui_font, small_aldo_ui_font
from aoslib.images import global_images
from shared.constants import MENU_FONT_COLOR
from shared.hud_constants import DROP_BOX_BACKGROUND_COLOUR, MENU_OPTION_SPACING, MENU_OPTION_BAR_BUTTON_SPACING, MENU_OPTION_MINIMUM_HEIGHT_FOR_MEDIUM_FONT, TEXT_BACKGROUND_SPACING
import math

class MenuOptionControl(HandlerBase):

    def initialize(self, name, x, y, width, height, on_open_menu_button_click, icon=global_images.edit_icon, background_colour=DROP_BOX_BACKGROUND_COLOUR, border_colour=(0, 0, 0, 255), text_colour=MENU_FONT_COLOR, center_text=True):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.name = name
        self.border_colour = border_colour
        self.background_colour = background_colour
        self.text_colour = text_colour
        self.elements = []
        self.button_height = height
        self.open_menu_button = SquareButton(icon, x, y, self.button_height)
        self.open_menu_button.add_handler(on_open_menu_button_click)
        self.elements.append(self.open_menu_button)
        self.update_position(x, y, width, height)
        self.center_text = center_text
        self.text_width = width

    def update_position(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.button_height = self.height - MENU_OPTION_SPACING * 2
        half_size = self.button_height / 2.0
        button_x = x + width - half_size - MENU_OPTION_SPACING
        button_y = y + MENU_OPTION_SPACING + half_size
        self.open_menu_button.size = self.button_height
        self.open_menu_button.set_position(button_x, button_y)
        self.text_width = self.width - TEXT_BACKGROUND_SPACING * 2 - self.button_height - MENU_OPTION_BAR_BUTTON_SPACING

    def set_enabled(self, enabled):
        self.enabled = enabled
        self.open_menu_button.enabled = enabled

    def draw(self):
        grey_bar_width = self.width - MENU_OPTION_SPACING * 2 - self.open_menu_button.size - MENU_OPTION_BAR_BUTTON_SPACING
        grey_bar_height = self.height - MENU_OPTION_SPACING * 2
        draw_quad(self.x, self.y, self.width, self.height, self.border_colour)
        draw_quad(self.x + MENU_OPTION_SPACING, self.y + MENU_OPTION_SPACING, grey_bar_width, grey_bar_height, self.background_colour)
        if grey_bar_height >= MENU_OPTION_MINIMUM_HEIGHT_FOR_MEDIUM_FONT:
            font = medium_aldo_ui_font
        else:
            font = small_aldo_ui_font
        alignment_x = 'center' if self.center_text else 'left'
        draw_text_with_alignment_and_size_validation(self.name.upper(), self.x + TEXT_BACKGROUND_SPACING, self.y, self.text_width, self.height, self.text_colour, font, alignment_x, alignment_y='center')
        for element in self.elements:
            element.draw()

    def get_mouse_collides(self, x, y):
        x1 = self.x
        y1 = self.y
        x2 = self.x + self.width
        y2 = self.y + self.height
        return x <= x2 and x >= x1 and y <= y2 and y >= y1

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
