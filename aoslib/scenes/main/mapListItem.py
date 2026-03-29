from aoslib.scenes.main.listPanelItemBase import ListPanelItemBase
from aoslib.text import draw_text_with_size_validation, medium_aldo_ui_font, big_aldo_ui_font
from pyglet import gl
from aoslib import strings
from shared.constants import MENU_FONT_COLOR

class MapListItem(ListPanelItemBase):

    def initialize(self, name, available_map=True):
        super(MapListItem, self).initialize()
        self.name = name
        self.available_map = available_map

    def update_position(self, x, y, width, height, highlight_width):
        super(MapListItem, self).update_position(x, y, width, height, highlight_width)

    def set_selected(self, selected, media):
        if self.available_map:
            super(MapListItem, self).set_selected(selected, media)

    def set_hovered(self, hovered):
        if self.available_map:
            super(MapListItem, self).set_hovered(hovered)

    def draw_name(self):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        y = self.get_text_y_position()
        pad_x = 20
        pad_y = 10
        height = self.height - pad_y
        right_text_width = 25
        right_text_x = self.x1 + self.width - pad_x / 2 - right_text_width
        pad_x = 15
        name_width = self.width / 3 * 2
        name_x = self.x1 + pad_x
        if self.available_map:
            colour = MENU_FONT_COLOR
        else:
            colour = (
             self.background_colour[0] + 20, self.background_colour[1] + 20, self.background_colour[2] + 20, self.background_colour[3])
            draw_text_with_size_validation(strings.NOT_OWNED, name_x + name_width + pad_x, y, self.width / 3 - pad_x * 3, height, colour, medium_aldo_ui_font, False)
        draw_text_with_size_validation(self.name, name_x, y, name_width, height, colour, self.font, False)
