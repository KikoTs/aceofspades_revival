from aoslib.scenes.main.listPanelItemBase import ListPanelItemBase
from aoslib.common import collides
from aoslib.images import global_images
from aoslib.text import draw_text_with_size_validation, get_resized_font_and_formatted_text_to_fit_boundaries, medium_standard_ui_font, small_standard_ui_font
from aoslib.draw import draw_quad
from pyglet import gl
from shared.constants import MENU_FONT_COLOR
from aoslib.common import tint_colour

class MultiColumnPanelItem(ListPanelItemBase):

    def initialize(self, column_widths, column_texts):
        super(MultiColumnPanelItem, self).initialize()
        self.column_widths = column_widths
        self.column_texts = column_texts

    def draw_name(self):
        no_of_cols = len(self.column_widths)
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        for i in xrange(no_of_cols):
            text_width = self.column_widths[i] - self.pad * 2
            text_height = self.height - self.pad * 2
            width_to_add = 0
            for n in xrange(i):
                width_to_add += self.column_widths[n]

            if self.center_text:
                x = self.x1 + self.pad + self.spacing + width_to_add
            else:
                x = self.x1 + self.pad + self.spacing + width_to_add
            y = self.get_text_y_position()
            draw_text_with_size_validation(self.column_texts[i], x, y, text_width, text_height, self.text_colour, self.font, self.center_text)

    def draw_background(self, colour):
        no_of_cols = len(self.column_widths)
        for i in xrange(no_of_cols):
            if i % 1 == 0:
                colour = tint_colour(colour, (0.7, 0.7, 0.7, 1.0))
            width_to_add = 0
            for n in xrange(i):
                width_to_add += self.column_widths[n]

            if i == no_of_cols - 1:
                width = self.width - width_to_add
            else:
                width = self.column_widths[i]
            draw_quad(self.x1 + width_to_add, self.y1, width, self.height, colour)

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
            if self.column_texts is not None and len(self.column_texts) > 0 and len(self.column_texts) == len(self.column_widths):
                self.draw_name()
            self.draw_elements()
            return
