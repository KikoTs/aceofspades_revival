from aoslib.scenes.main.listPanelItemBase import ListPanelItemBase
from aoslib.text import draw_text_with_alignment_and_size_validation, small_edo_ui_font, medium_edo_ui_font, big_edo_ui_font
from aoslib.gui import SquareButton
from aoslib.images import global_images
from pyglet import gl
from shared.constants import MENU_FONT_COLOR
from shared.hud_constants import CATEGORY_GREEN_COLOUR
from aoslib.common import to_float_color_alpha, get_lighter_colour, draw_image_resized
from aoslib.draw import draw_quad
from shared.hud_constants import TEXT_BACKGROUND_SPACING, UI_CONTROL_SPACING

class CategoryListItem(ListPanelItemBase):

    def initialize(self, name, text_colour=MENU_FONT_COLOR, background_colour=CATEGORY_GREEN_COLOUR, is_expandable=False, sub_row_colours=None, draw_background_texture=False, sort_order=0):
        super(CategoryListItem, self).initialize()
        self.name = name
        self.text_colour = text_colour
        self.background_colour = background_colour
        self.small_font = medium_edo_ui_font
        self.medium_font = big_edo_ui_font
        self.big_font = big_edo_ui_font
        self.draw_background_texture = draw_background_texture
        self.sort_order = sort_order
        self.center_text = False
        if is_expandable:
            texture_colour = to_float_color_alpha(self.background_colour)
            self.expand_button = SquareButton(global_images.collapse_minus, 0, 0, 16, texture_colour)
            self.expand_button.draw_background_image = True
            self.expand_button.add_handler(self.on_expand)
            self.elements.append(self.expand_button)
            self.is_expanded = True
        else:
            self.expand_button = None
            self.is_expanded = False
        self.expand_button_clicked_callback = None
        if sub_row_colours == None:
            if self.draw_background_texture:
                self.sub_row_colours = [
                 (0, 0, 0, 0), (0, 0, 0, 0)]
            else:
                self.sub_row_colours = [
                 get_lighter_colour(self.background_colour, 15), get_lighter_colour(self.background_colour)]
        else:
            self.sub_row_colours = sub_row_colours
        return

    def update_position(self, x, y, width, height, highlight_width):
        super(CategoryListItem, self).update_position(x, y, width, height, highlight_width)
        if self.expand_button is not None:
            self.expand_button.size = self.height - UI_CONTROL_SPACING * 2
            x = self.x1 + self.width - TEXT_BACKGROUND_SPACING - self.expand_button.size / 2.0
            y = self.y1 + UI_CONTROL_SPACING + self.expand_button.size / 2.0 - float(self.spacing_size) * 0.5
            self.expand_button.set_position(x, y)
        return

    def expand(self):
        self.is_expanded = True
        self.expand_button.texture = global_images.collapse_minus

    def collapse(self):
        self.is_expanded = False
        self.expand_button.texture = global_images.collapse_plus

    def on_expand(self, silent=False):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.expand_button.texture = global_images.collapse_minus
        else:
            self.expand_button.texture = global_images.collapse_plus
        if self.expand_button_clicked_callback is not None:
            self.expand_button_clicked_callback(self, silent=silent)
        return

    def set_selected(self, selected, media):
        pass

    def set_hovered(self, hovered):
        pass

    def draw_background(self, colour):
        height = self.height
        if self.draw_spacing:
            height -= self.spacing_size
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        if self.draw_background_texture:
            red_bar_center = global_images.red_header_center
            red_bar_left = global_images.red_header_left
            red_bar_right = global_images.red_header_right
            new_center_width = self.width - red_bar_left.width - red_bar_right.width
            y = self.y1
            draw_image_resized(red_bar_center, self.x1 + red_bar_left.width, y, self.width - red_bar_left.width - red_bar_right.width, height, 'bottom')
            draw_image_resized(red_bar_left, self.x1, y, red_bar_left.width, height, 'bottom')
            draw_image_resized(red_bar_right, self.x1 + red_bar_left.width + self.width - red_bar_left.width - red_bar_right.width, y, red_bar_right.width, height, 'bottom')
        else:
            draw_quad(self.x1, self.y1, self.width, height, colour)
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        if self.draw_spacing:
            draw_quad(self.x1, self.y1 + self.height - self.spacing_size, self.width, self.spacing_size, self.spacing_colour)

    def draw_name(self):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        y = self.y1
        alignment = 'center' if self.center_text else 'left'
        draw_text_with_alignment_and_size_validation(self.name, self.x1 + TEXT_BACKGROUND_SPACING, y, self.width - TEXT_BACKGROUND_SPACING * 2, self.height, MENU_FONT_COLOR, self.font, alignment, 'center')

    def draw(self, colour=None):
        super(CategoryListItem, self).draw(self.background_colour)
