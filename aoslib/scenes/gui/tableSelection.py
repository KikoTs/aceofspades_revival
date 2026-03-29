from pyglet import gl
from aoslib.gui import *
from aoslib.scenes.gui.horizontalListSelection import HorizontalListSelection, TABLE_HLIST
from aoslib.text import class_description_font
from shared.constants import MENU_FONT_COLOR
from math import ceil

class TableSelection(HorizontalListSelection):

    def __init__(self, image_info_list, x, y, max_selected_items, min_selected_items, button_image_scale, items_per_row, items_per_page, selected_items_ids=[], image_colour=None, draw_frame=False):
        self.draw_frame = draw_frame
        self._item_index = []
        self.elements = []
        self._buttons = []
        self._page_index = 0
        self._min_index = 0
        self.list_type = TABLE_HLIST
        self._row_index = 0
        self._min_selected_items = min_selected_items
        self._max_selected_items = max_selected_items
        self._items_per_row = items_per_row
        self._items_per_page = items_per_page
        self._items = image_info_list
        self.draw_back_image = True
        self._noof_pages = int(ceil(float(len(self._items)) / float(self._items_per_page)))
        self._x = x
        self._y = y
        button_x = x + 5
        button_y = y
        button_size = 38
        button_border_scale = [0.27, 0.3]
        self.image_button_scale = button_image_scale
        column_index = 0
        row_index = 0
        for index in xrange(self._items_per_page):
            if column_index >= self._items_per_row:
                button_y -= button_size + 5
                column_index = 0
                button_x = x + 5
                row_index += 1
            button = CustomButton(button_x, button_y, button_size, button_size, image_scale=button_image_scale, border_scale=button_border_scale, button_image_colour=image_colour)
            button.add_handler(self.on_item_selected, index)
            self._buttons.append(button)
            button_x += 41
            column_index += 1

        self.create_navigation_buttons(x + 110, y - 171, x + 5, y - 171)
        self.populate_items_list(self._items, selected_items_ids)
        self.on_item_selected_callback = None
        self.on_mouse_over_item_callback = None
        self.on_page_change_callback = None
        self._item_under_mouse = None
        self.scrollbar = None
        return

    def draw_button_background(self, button):
        pass

    def draw(self):
        super(TableSelection, self).draw()
        if self._next_button.enabled or self._back_button.enabled:
            current_page_index = self.get_page_index()
            class_description_font.draw(str(current_page_index + 1), self._x + 62, self._y - 182, MENU_FONT_COLOR)
