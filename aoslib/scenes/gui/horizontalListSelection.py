from pyglet import gl
from aoslib.gui import *
from aoslib.images import global_images
from shared.constants import FLAREBLOCK_TOOL
from math import ceil
from aoslib.gui import HandlerBase
from aoslib.draw import draw_quad
from shared.hud_constants import SELECT_CLASS_LOADOUT_FRAME_X, SELECT_CLASS_LOADOUT_FRAME_Y_DIFF, SELECT_CLASS_LOADOUT_FRAME_WIDTH, SELECT_CLASS_LOADOUT_FRAME_HEIGHT, SELECT_CLASS_LOADOUT_FRAME_COLOUR, SELECT_CLASS_LOADOUT_BACKGROUD_COLOUR, SELECT_CLASS_PREFAB_LOADOUT_SPACING, SELECT_CLASS_PREFAB_FRAME_Y_DIFF, SELECT_CLASS_PREFAB_FRAME_WIDTH, SELECT_CLASS_PREFAB_FRAME_HEIGHT
CLASS_SELECTION_HLIST4, CLASS_SELECTION_HLIST5, LOADOUT_HLIST, TABLE_HLIST = xrange(4)

class HorizontalListSelection(HandlerBase):
    item_info = {CLASS_SELECTION_HLIST4: {'items_per_page': 4, 'page_buttons': False, 'x': 151, 'y': 18, 'space': 167, 'button_size': 136, 'frame_scale': [1.1, 1.1]}, CLASS_SELECTION_HLIST5: {'items_per_page': 5, 'page_buttons': False, 'x': 147, 'y': 19, 'space': 134, 'button_size': 107, 'frame_scale': [0.88, 0.88]}, LOADOUT_HLIST: {'items_per_page': 6, 'page_buttons': True, 'x': 150, 'y': 15, 'space': 45, 'button_size': 42, 'frame_scale': [0.3, 0.34]}}

    def __init__(self, image_info_list, x, y, max_selected_items, button_image_scale, list_type, selected_items_ids=[], draw_frame=True, draw_back_image=True, image_colour=None, scale_hover=0.0):
        self.list_type = list_type
        self.list_parameters = self.item_info[list_type]
        self._item_index = []
        self.draw_frame = draw_frame
        self.draw_back_image = draw_back_image
        self._items_per_page = self.list_parameters['items_per_page']
        self._noof_pages = 1
        self._min_index = 0
        self._items = image_info_list
        self._noof_pages = int(ceil(float(len(self._items)) / float(self._items_per_page)))
        self._buttons = []
        self._min_selected_items = 1
        self._max_selected_items = max_selected_items
        self._x = x
        self._y = y
        self.elements = []
        x -= self.list_parameters['x']
        y += self.list_parameters['y']
        button_x = x + 5
        button_y = y
        item_size = self.list_parameters['button_size']
        button_border_scale = self.list_parameters['frame_scale']
        self.image_button_scale = button_image_scale
        for index in xrange(self._items_per_page):
            button = CustomButton(button_x, button_y, item_size, item_size, image_scale=button_image_scale, border_scale=button_border_scale, button_image_colour=image_colour, scale_image_on_hover=scale_hover)
            button.add_handler(self.on_item_selected, index)
            self._buttons.append(button)
            button_x += self.list_parameters['space']

        if self.list_parameters['page_buttons']:
            next_nav_button_x = button_x - self.list_parameters['space'] + self.list_parameters['button_size'] + 4
            self.create_navigation_buttons(next_nav_button_x, y - 16, x - 16, y - 16)
        else:
            self._next_button = None
            self._back_button = None
        self.populate_items_list(self._items, selected_items_ids)
        self.on_item_selected_callback = None
        self.on_mouse_over_item_callback = None
        self.on_page_change_callback = None
        self._item_under_mouse = None
        self.scrollbar = None
        return

    def create_navigation_buttons(self, right_button_x, right_button_y, left_button_x, left_button_y):
        button_size = 14
        self._next_button = TextButton(' ', right_button_x, right_button_y, button_size, button_size, image=global_images.right_arrow, image_scale=1.1)
        self._next_button.add_handler(self.on_next_page_selected, 0)
        self._back_button = TextButton(' ', left_button_x, left_button_y, button_size, button_size, image=global_images.left_arrow, image_scale=1.1)
        self._back_button.add_handler(self.on_back_page_selected, 0)

    def add_on_item_clicked_handler(self, handler, id):
        self.on_item_selected_callback = (
         handler, id)

    def fire_on_item_clicked_handler(self, button_info):
        if self.on_item_selected_callback is not None:
            self.on_item_selected_callback[0](self.on_item_selected_callback[1], button_info)
        return

    def add_on_mouse_over_handler(self, handler, id):
        self.on_mouse_over_item_callback = (
         handler, id)

    def fire_on_mouse_over_handler(self, button_info):
        if self.on_mouse_over_item_callback is not None:
            self.on_mouse_over_item_callback[0](self.on_mouse_over_item_callback[1], button_info)
        return

    def add_on_page_change_handler(self, handler, id):
        self.on_page_change_callback = (
         handler, id)

    def fire_on_page_change_handler(self, min_index, max_index):
        if self.on_page_change_callback is not None:
            self.on_page_change_callback[0](self.on_page_change_callback[1], min_index, max_index)
        return

    def get_selected_items(self):
        return self._item_index

    def get_selected_item_ids(self):
        item_ids = []
        for index in self._item_index:
            item_ids.append(self._items[index][0])

        return item_ids

    def get_selected_item_ids_and_indices(self):
        selected_items = []
        for index in self._item_index:
            selected_items.append({'id': (self._items[index][0]), 'index': index})

        return selected_items

    def get_min_index(self):
        return self._min_index

    def get_page_index(self, item_index=None):
        if item_index is None:
            item_index = self._min_index
        return item_index / self._items_per_page

    def get_indices_for_item_id(self, id):
        return [index for index, item in enumerate(self._items) if item[0] == id]

    def populate_items_list(self, image_info_list, selected_items_ids=[], page_changed=False):
        count = 0
        self._items = image_info_list
        if page_changed == False:
            self._item_index = []
            self._min_index = 0
        min_index = self._min_index
        max_index = min_index + self._items_per_page - 1
        for index, image_info in enumerate(self._items):
            if index < min_index or index > max_index:
                if image_info[0] in selected_items_ids:
                    self._item_index.append(index)
                continue
            if count >= self._items_per_page:
                break
            if image_info[1] == None:
                continue
            button = self._buttons[count]
            if image_info[0] == FLAREBLOCK_TOOL:
                button.image_scale = 0.1
            else:
                button.image_scale = self.image_button_scale
            button.image = image_info[1]
            if len(image_info) > 2:
                button.set_enabled(image_info[2])
            button.draw_background_image = self.draw_back_image
            if image_info[0] in selected_items_ids:
                self._item_index.append(index)
            this_button_selected = True
            if index in self._item_index:
                if not button.enabled:
                    self._item_index.remove(index)
                    this_button_selected = False
            else:
                this_button_selected = False
            button.set_draw_border(this_button_selected)
            count += 1

        for index in range(count, self._items_per_page):
            self._buttons[index].image = None
            self._buttons[index].draw_background_image = False

        if len(self._item_index) == 0 and len(self._items) > 0 and len(self._buttons) > 0 and self._min_selected_items > 0:
            selected_index = 0
            self._item_index.append(selected_index)
            button = self._buttons[selected_index]
            button.set_draw_border(True)
        if page_changed:
            self.fire_on_page_change_handler(min_index, max_index)
        self.update_navigation_buttons_state()
        return

    def on_next_page_selected(self, value):
        self._min_index += self._items_per_page
        self._min_index = min(self._min_index, len(self._items) - 1)
        self.populate_items_list(self._items, page_changed=True)
        if self._next_button:
            self._next_button.pressed = False
        self.set_scrollbar_from_min_index()

    def on_back_page_selected(self, value):
        self._min_index -= self._items_per_page
        self._min_index = max(self._min_index, 0)
        self.populate_items_list(self._items, page_changed=True)
        if self._back_button:
            self._back_button.pressed = False
        self.set_scrollbar_from_min_index()

    def set_scrollbar(self, scrollbar):
        self.scrollbar = scrollbar
        self.set_scrollbar_from_min_index()

    def on_scrollbar_scroll(self, value, silent=False):
        self.set_min_index(int(value))

    def set_scrollbar_from_min_index(self):
        if self.scrollbar:
            self.scrollbar.set_scroll(self._min_index, silent=True)

    def set_min_index(self, value):
        self._min_index = value
        self._min_index = max(self._min_index, 0)
        self._min_index = min(self._min_index, len(self._items) - 1)
        self.populate_items_list(self._items, page_changed=True)

    def set_max_selected_items(self, noof):
        self._max_selected_items = max([noof, 0])
        while self._max_selected_items < len(self._item_index):
            self._item_index.pop(0)

    def on_itemindex_selected(self, value):
        if value < self._min_index or value >= self._min_index + self._items_per_page:
            if value < self._min_index:
                self._min_index = value
            else:
                self._min_index = max(value - self._items_per_page + 1, 0)
            self.populate_items_list(self._items, page_changed=True)
            if self.on_mouse_over_item_callback is not None:
                self.fire_on_mouse_over_handler(None)
            self.set_scrollbar_from_min_index()
        offset_value = value - self._min_index
        self.on_item_selected(offset_value)
        return

    def on_item_selected(self, value):
        if self._buttons[value].image is None:
            return
        else:
            self._item_under_mouse = self._buttons[value]
            new_index = value + self._min_index
            if new_index in self._item_index:
                if len(self._item_index) - 1 >= self._min_selected_items:
                    self._item_index.remove(new_index)
            elif len(self._item_index) < self._max_selected_items:
                self._item_index.append(new_index)
            elif len(self._item_index) > 0:
                self._item_index.pop(0)
                self._item_index.append(new_index)
            for index, item in enumerate(self._buttons):
                item_index = index + self._min_index
                item.set_draw_border(item_index in self._item_index)

            button_info = {'button': (self._buttons[value]), 'id': (self._items[new_index][0]), 'index': new_index}
            self.fire_on_item_clicked_handler(button_info)
            return

    def on_mouse_release(self, x, y, button, modifiers):
        for item in self._buttons:
            if item.image is not None and item.over:
                item.on_mouse_release(x, y, button, modifiers)
                if self._item_under_mouse is not None:
                    break

        self._item_under_mouse = None
        if self._back_button and self._back_button.enabled and self._back_button.over:
            self._back_button.on_mouse_release(x, y, button, modifiers)
        if self._next_button and self._next_button.enabled and self._next_button.over:
            self._next_button.on_mouse_release(x, y, button, modifiers)
        return

    def on_mouse_press(self, x, y, button, modifiers):
        for item in self._buttons:
            if item.image is not None and item.over:
                item.on_mouse_press(x, y, button, modifiers)

        for item in [self._back_button, self._next_button]:
            if item and item.enabled and item.over:
                item.on_mouse_press(x, y, button, modifiers)

        return

    def on_mouse_motion(self, x, y, dx, dy):
        index = 0
        mouse_over_button = None
        for item in self._buttons:
            if item.image is not None:
                item.on_mouse_motion(x, y, dx, dy)
                if item.over and self.on_mouse_over_item_callback is not None:
                    item_index = index + self._min_index
                    mouse_over_button = {'button': item, 'id': (self._items[item_index][0])}
                    break
            index += 1

        if self.on_mouse_over_item_callback is not None:
            self.fire_on_mouse_over_handler(mouse_over_button)
        if self._back_button and self._back_button.enabled:
            self._back_button.on_mouse_motion(x, y, dx, dy)
        if self._next_button and self._next_button.enabled:
            self._next_button.on_mouse_motion(x, y, dx, dy)
        return

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        for item in self._buttons:
            item.on_mouse_drag(x, y, dx, dy, button, modifiers)

        if self._back_button and self._back_button.enabled:
            self._back_button.on_mouse_drag(x, y, dx, dy, button, modifiers)
        if self._next_button and self._next_button.enabled:
            self._next_button.on_mouse_drag(x, y, dx, dy, button, modifiers)

    def update_navigation_buttons_state(self):
        if self._back_button:
            self._back_button.enabled = self._min_index > 0
        if self._next_button:
            self._next_button.enabled = self._min_index + self._items_per_page < len(self._items)

    def draw_background(self):
        if self.draw_frame == False:
            return
        if self.list_type == CLASS_SELECTION_HLIST4:
            global_images.four_items_frame.blit(self._x, self._y)
        elif self.list_type == CLASS_SELECTION_HLIST5:
            global_images.five_items_frame.blit(self._x, self._y)
        elif self.list_type == LOADOUT_HLIST:
            draw_quad(SELECT_CLASS_LOADOUT_FRAME_X, self._y - SELECT_CLASS_LOADOUT_FRAME_Y_DIFF, SELECT_CLASS_LOADOUT_FRAME_WIDTH, SELECT_CLASS_LOADOUT_FRAME_HEIGHT, SELECT_CLASS_LOADOUT_FRAME_COLOUR)
        else:
            x = SELECT_CLASS_LOADOUT_FRAME_X + SELECT_CLASS_LOADOUT_FRAME_WIDTH + SELECT_CLASS_PREFAB_LOADOUT_SPACING
            draw_quad(x, self._y - SELECT_CLASS_PREFAB_FRAME_Y_DIFF, SELECT_CLASS_PREFAB_FRAME_WIDTH, SELECT_CLASS_PREFAB_FRAME_HEIGHT, SELECT_CLASS_LOADOUT_FRAME_COLOUR)

    def draw(self):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        self.draw_background()
        for button in self._buttons:
            if button.image is not None:
                button.draw()
            elif self.draw_frame:
                draw_quad(button.x, button.y - button.height, button.width, button.height, SELECT_CLASS_LOADOUT_BACKGROUD_COLOUR)

        if self._next_button and self._back_button and (self._next_button.enabled or self._back_button.enabled):
            self._next_button.draw()
            self._back_button.draw()
        return

    def set_visible(self, value):
        self.visible = value
        for button in self._buttons:
            button.visible = value

    def set_enabled(self, value):
        self.enabled = value
        for button in self._buttons:
            button.enabled = value
