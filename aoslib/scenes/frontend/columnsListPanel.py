from aoslib.text import draw_text_with_size_validation, medium_edo_ui_font
from aoslib.scenes.frontend.listPanelBase import ListPanelBase
from pyglet import gl
from shared.constants import MENU_FONT_COLOR

class ColumnsListPanel(ListPanelBase):
    column_texts = []
    column_widths = []

    def set_list_panel_columns(self, column_texts=[], column_widths=[]):
        self.column_texts = column_texts
        self.column_widths = column_widths
        self.column_text_y = 0
        self.padding = 23

    def update_position(self, x, y, width, height):
        super(ColumnsListPanel, self).update_position(x, y, width, height)
        if len(self.column_texts) > 0 and len(self.column_texts) == len(self.column_widths):
            self.column_text_y = self.list_area_y - 10
            self.y1 -= 20
            self.list_area_y -= 20
            self.list_area_height -= 20
        if self.scrollbar and not self.scrollbar.is_disabled():
            self.scrollbar.height = self.list_area_height
            self.scrollbar.y = self.list_area_y

    def draw(self):
        if self.visible == False:
            return
        if len(self.column_texts) > 0 and len(self.column_texts) == len(self.column_widths):
            no_of_cols = len(self.column_widths)
            gl.glColor4f(1.0, 1.0, 1.0, 1.0)
            self.draw_background_frame()
            if self.has_header:
                self.draw_header(self.title)
            for i in xrange(no_of_cols):
                text_width = self.column_widths[i]
                text_height = 30
                width_to_add = 0
                for n in xrange(i):
                    width_to_add += self.column_widths[n]

                x = self.padding + self.x1 + width_to_add
                y = self.column_text_y
                draw_text_with_size_validation(self.column_texts[i], x, y, text_width, text_height, MENU_FONT_COLOR, medium_edo_ui_font, False)

            self.draw_list_items()
            if not self.scrollbar.is_disabled():
                self.scrollbar.draw()
        else:
            super(ColumnsListPanel, self).draw()
