from aoslib.scenes.main.listPanelItemBase import ListPanelItemBase
from aoslib.text import draw_text_with_size_validation, medium_standard_ui_font, small_standard_ui_font
from aoslib.draw import draw_quad
from pyglet import gl

class ListPanelItemMultiColumn(ListPanelItemBase):

    def initialize(self, name=None, x=0, y=0, width=10, height=10):
        super(ListPanelItemMultiColumn, self).initialize(name=name, x=x, y=y, width=width, height=height)
        self.separator_width = 1
        self.column_texts = None
        return

    def set_columns(self, column_texts):
        self.column_texts = column_texts

    def draw_background(self, colour, widths=None):
        if widths is None:
            super(ListPanelItemMultiColumn, self).draw_background(colour)
            return
        else:
            column_x1 = self.x1
            total_widths = 0
            noof_items = len(widths) - 1
            for index, column_width in enumerate(widths):
                width = column_width
                if index < noof_items:
                    width -= self.separator_width
                draw_quad(column_x1, self.y1, width, self.height, colour)
                column_x1 += column_width
                total_widths += column_width

            if total_widths < self.width:
                draw_quad(column_x1, self.y1, self.width - total_widths, self.height, colour)
            return

    def get_column_x1(self, column_widths, column_index):
        if column_widths is None:
            return self.x1
        else:
            x = self.x1
            for index in xrange(0, column_index):
                x += column_widths[index]

            return x

    def get_column_text_x_offset(self, column_widths, column_index):
        if self.center_text:
            return self.pad
        else:
            if not column_widths:
                return self.pad_x
            return self.get_pad_x_for_width(column_widths[column_index])

    def draw_column_texts(self, widths=None):
        if widths is None:
            return
        else:
            y = self.get_text_y_position()
            gl.glColor4f(1.0, 1.0, 1.0, 1.0)
            column_x1 = self.x1
            noof_columns = len(self.column_texts)
            for index, column_width in enumerate(widths):
                if index >= noof_columns:
                    break
                column_offset = self.get_column_text_x_offset(widths, index)
                text_width = column_width - self.separator_width - column_offset * 2
                text_height = self.height - self.pad * 2
                x = column_x1 + column_offset
                draw_text_with_size_validation(self.column_texts[index], x, y, text_width, text_height, self.text_colour, self.font, self.center_text)
                column_x1 += column_width

            return

    def draw_elements(self, widths=None):
        self.draw_column_texts(widths)
        super(ListPanelItemMultiColumn, self).draw_elements()

    def draw(self, colour, widths=None):
        if widths == None:
            super(ListPanelItemMultiColumn, self).draw(colour)
        if self.visible == False:
            return
        else:
            gl.glColor4f(1.0, 1.0, 1.0, 1.0)
            self.background_colour = colour
            self.draw_background(colour, widths)
            if self._is_hovered and self.is_selectable():
                self.draw_hovered_highlight()
            if self._is_selected and self.is_selectable():
                self.draw_selection_highlight()
            if self.name is not None:
                self.draw_name()
            self.draw_elements(widths)
            return
