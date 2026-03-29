from aoslib.scenes.main.listPanelItemMultiColumn import ListPanelItemMultiColumn
from shared.hud_constants import LEADERBOARD_MENU_GRID_COLUMN_PADDING
from aoslib.text import draw_text_with_size_validation
from pyglet import gl

class LeaderboardListItem(ListPanelItemMultiColumn):
    column_padding = LEADERBOARD_MENU_GRID_COLUMN_PADDING
    horizontal_scroll_index = 0
    first_scrolling_column_index = 2

    def initialize(self, uid=None):
        super(LeaderboardListItem, self).initialize()
        self.uid = uid

    def set_horizontal_scroll_index(self, horizontal_scroll_index):
        self.horizontal_scroll_index = horizontal_scroll_index

    def get_pad_x_for_width(self, width):
        return self.column_padding

    def set_font_for_row_height(self):
        pass

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
                if index >= self.first_scrolling_column_index:
                    text_index = index + self.horizontal_scroll_index
                else:
                    text_index = index
                draw_text_with_size_validation(self.column_texts[text_index], x, y, text_width, text_height, self.text_colour, self.font, self.center_text)
                column_x1 += column_width

            return
