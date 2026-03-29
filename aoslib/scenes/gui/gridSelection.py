from pyglet import gl
from aoslib.gui import *
from aoslib.scenes.gui.horizontalListSelection import HorizontalListSelection, TABLE_HLIST
from aoslib.text import draw_text_with_alignment_and_size_validation
from math import ceil

class GridSelection(HorizontalListSelection):

    def __init__(self, image_info_list, x, y, max_selected_items, min_selected_items, button_image_scale, button_width, button_height, button_background_image, button_border_image, items_per_row, items_per_page, selected_items_ids=[], pad_x=6, pad_y=6, image_offset=[0.0, 0.0]):
        self.draw_frame = False
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
        button_x = x + pad_x
        button_y = y
        button_border_scale = [button_width / float(button_border_image.width), button_height / float(button_border_image.height)]
        self.image_button_scale = button_image_scale
        column_index = 0
        row_index = 0
        for index in xrange(self._items_per_page):
            if column_index >= self._items_per_row:
                button_y -= button_height + pad_y
                column_index = 0
                button_x = x + pad_x
                row_index += 1
            button = CustomButton(button_x, button_y, button_width, button_height, image_scale=button_image_scale, border_scale=[1.0, 1.0], border_image=button_border_image, background_image=button_background_image, image_offset=image_offset)
            button.draw_background_image = True
            button.add_handler(self.on_item_selected, index)
            self._buttons.append(button)
            button_x += button_width + pad_x
            column_index += 1

        self._back_button = None
        self._next_button = None
        self.populate_items_list(self._items, selected_items_ids)
        self.on_item_selected_callback = None
        self.on_mouse_over_item_callback = None
        self.on_page_change_callback = None
        self._item_under_mouse = None
        rows_per_page = int(ceil(float(items_per_page) / items_per_row))
        scrollbar_x = self._x + button_width * self._items_per_row + pad_x * (self._items_per_row + 1) + ceil(PREFABS_MENU_SCROLLBAR_WIDTH * 0.5)
        scrollbar_y = self._y - button_height * rows_per_page - pad_y * max((rows_per_page - 1, 0)) + 1
        noof_rows = int(len(self._items) / float(self._items_per_row))
        scrollbar_height = button_height * rows_per_page + pad_y * max((rows_per_page - 1, 0))
        if self._noof_pages > 1:
            self.scrollbar = VerticalScrollBar(scrollbar_x, scrollbar_y, PREFABS_MENU_SCROLLBAR_WIDTH, scrollbar_height, noof_rows + 1, rows_per_page, PREFABS_MENU_SCROLLBAR_BUTTON_SIZE)
            self.scrollbar.add_on_scrolled_handler(self.on_scrollbar_scroll)
            self.on_scrollbar_scroll(0, silent=True)
            self.scrollbar.set_scroll(0)
        else:
            self.scrollbar = None
        return

    def on_scrollbar_scroll(self, value, silent=False):
        self.set_min_index(int(value * self._items_per_row))

    def on_scroll_list_item_deleted(self, value):
        if self._min_index <= value and value < self._min_index + self._items_per_page:
            offset_value = value - self._min_index
            self._buttons[offset_value].set_draw_border(False)
        if value in self._item_index:
            self._item_index.remove(value)

    def draw_background(self):
        pass

    def draw_button_background(self, button):
        pass

    def draw(self):
        super(GridSelection, self).draw()
        if self.visible:
            for button_index, button in enumerate(self._buttons):
                item_index = self._min_index + button_index
                if item_index < len(self._items) and len(self._items[item_index]) > 2:
                    for label in self._items[item_index][2]:
                        text_x = button.x + label.x
                        text_y = button.y + label.y
                        draw_text_with_alignment_and_size_validation(text=label.text, x=text_x, y=text_y, width=label.width, height=label.height, color=label.color, font=label.font, alignment_x=label.anchor_x, alignment_y=label.anchor_y)
