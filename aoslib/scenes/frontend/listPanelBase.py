from aoslib.scenes.frontend.panelBase import PanelBase, BACKGROUND_WITH_IMAGE
from aoslib.gui import VerticalScrollBar
from aoslib.images import global_images
from aoslib.media import HUD_AUDIO_ZONE
from aoslib.text import draw_text_with_size_validation
from aoslib.common import collides, in_zone
from shared.hud_constants import ROW_GREY_COLOUR, ROW_DARK_GREY_COLOUR, LIST_PANEL_SPACING, NORMAL_ROW_HEIGHT, LIST_PANEL_SCROLLBAR_WIDTH, LIST_PANEL_SCROLLBAR_BUTTON_SIZE
from pyglet import gl
import math

class ListPanelBase(PanelBase):
    scrollbar_extra_offset_x = 0
    scrollbar_extra_offset_y = 0
    scrollbar_extra_length = 0

    def initialize(self):
        super(ListPanelBase, self).initialize()
        self.allow_unselect_row_on_click = False
        self.current_row_index = None
        self.last_selected_item = None
        self.scrollbar_offset_x = 0
        self.scrollbar_offset_y = 0
        self.scroll_item_area_x = 0
        self.scroll_item_width = 0
        self.list_area_height = 0
        self.header_spacing = 0
        self.list_spacing = LIST_PANEL_SPACING
        self.rows = []
        self.scrollbar = None
        self.initialise_ui('', 10, 10, 10, 10)
        return

    def initialise_ui(self, title, x, y, width, height, row_height=NORMAL_ROW_HEIGHT, has_header=False, list_items_background_colors=None, spacing=None, enable_background_resizing=False):
        super(ListPanelBase, self).initialise_ui(title, x, y, width, height, has_header)
        self.title = title
        self.update_position(x, y, width, height)
        self.elements = []
        self.scrollbar = None
        for row in [row for row in self.rows if hasattr(row, 'close')]:
            row.close()

        self.rows = []
        if spacing != None:
            self.spacing = spacing
        else:
            self.spacing = self.width * 0.02
        self.line_spacing = 0
        self.row_height = row_height if row_height > 0 else NORMAL_ROW_HEIGHT
        if self.current_row_index is None:
            self.current_row_index = -1
        self.noof_visible_items = int(math.floor(float(self.list_area_height + self.line_spacing) / float(self.row_height + self.line_spacing)))
        self.noof_visible_items = 1 if self.noof_visible_items == 0 else self.noof_visible_items
        self.row_height = row_height
        self.min_index = self.current_row_index
        self.max_index = self.current_row_index + self.noof_visible_items
        self.__create_scroll_bar()
        self.on_item_hovered_callback = None
        self.on_item_selected_callback = None
        self.on_item_unselected_callback = None
        self.enable_background_resizing = enable_background_resizing
        if list_items_background_colors is None or len(list_items_background_colors) == 0:
            self.list_items_background_colors = [
             ROW_GREY_COLOUR, ROW_DARK_GREY_COLOUR]
        else:
            self.list_items_background_colors = list_items_background_colors
        return

    def close(self):
        for row in [row for row in self.rows if hasattr(row, 'close')]:
            row.close()

        return super(ListPanelBase, self).close()

    def update_position(self, x, y, width, height):
        self.x1 = x
        self.y1 = y if self.has_header == False else y - self.title_height - self.list_spacing * 2
        self.width = width
        if self.has_header:
            self.list_area_y = y - self.title_height - self.list_spacing * 2
            self.list_area_height = height - self.title_height - self.list_spacing * 3
        else:
            self.list_area_y = y - self.list_spacing
            self.list_area_height = height - self.list_spacing * 2

    def select_row_with_name(self, name, silent=True):
        selected_row = None
        media = None
        if not silent:
            media = self.media
        for index, row in enumerate(self.rows):
            if row.name == name:
                self.current_row_index = index
                row.set_selected(True, media)
                self.on_row_selected(row)
                selected_row = row
            else:
                row.set_selected(False, self.media)

        return selected_row

    def select_row_with_uid(self, uid, silent=True):
        selected_row = None
        media = None
        if not silent:
            media = self.media
        for index, row in enumerate(self.rows):
            if row.uid == uid:
                self.current_row_index = index
                row.set_selected(True, media)
                self.on_row_selected(row)
                selected_row = row
            else:
                row.set_selected(False, self.media)

        return selected_row

    def find_row_with_name(self, name):
        for index, row in enumerate(self.rows):
            if row.name == name:
                return row

        return

    def select_row(self, row, silent=True, fire_selected_row_event=True, selected=True):
        if row is None or row.is_selectable() == False:
            return
        media = None
        if not silent:
            media = self.media
        for index, item in enumerate(self.rows):
            if item.is_same_item(row):
                if selected:
                    self.current_row_index = index
                    item.set_selected(True, media)
                    self.on_row_selected(row)
                    if fire_selected_row_event:
                        self.__fire_on_item_selected_handler(row)
                else:
                    self.current_row_index = None
                    row.set_selected(False, media)
                    if fire_selected_row_event:
                        self.__fire_on_item_unselected_handler(row)
                while index >= self.max_index:
                    self.min_index += 1
                    self.max_index = self.min_index + self.noof_visible_items

                self.on_scroll(self.min_index, silent=True)
                self.scrollbar.set_scroll(self.min_index)
            else:
                item.set_selected(False, media)

        return

    def remove_row(self, row_to_delete):
        selected_row = self.get_selected_item()
        self.rows.remove(row_to_delete)
        self.select_row(selected_row, silent=True)
        self.on_scroll(self.min_index, silent=True)
        self.scrollbar.set_scroll(self.min_index, silent=True)

    def get_selected_item(self):
        if self.current_row_index < 0 or self.current_row_index >= len(self.rows):
            return None
        return self.rows[self.current_row_index]

    def add_on_item_hovered_handler(self, handler, id):
        self.on_item_hovered_callback = (
         handler, id)

    def add_on_item_selected_handler(self, handler, id):
        self.on_item_selected_callback = (
         handler, id)

    def add_on_item_unselected_handler(self, handler, id):
        self.on_item_unselected_callback = (
         handler, id)

    def __fire_on_item_hovered_handler(self, row):
        if self.on_item_hovered_callback is not None:
            self.on_item_hovered_callback[0](self.on_item_hovered_callback[1], row)
        return

    def __fire_on_item_selected_handler(self, row):
        if self.on_item_selected_callback is not None:
            self.on_item_selected_callback[0](self.on_item_selected_callback[1], row)
        return

    def __fire_on_item_unselected_handler(self, row):
        if self.on_item_unselected_callback is not None:
            self.on_item_unselected_callback[0](self.on_item_unselected_callback[1], row)
        return

    def __create_scroll_bar(self, scrollbar_width=LIST_PANEL_SCROLLBAR_WIDTH, scrollbar_button_size=LIST_PANEL_SCROLLBAR_BUTTON_SIZE):
        noof_rows = len(self.rows)
        max_noof_rows = noof_rows if noof_rows > 0 else 1
        scrollbar_control_width = max(scrollbar_width, scrollbar_button_size)
        x = self.x1 + self.width - scrollbar_control_width / 2 - self.list_spacing + self.scrollbar_offset_x
        height = self.list_area_height
        y = self.list_area_y - self.list_area_height + self.scrollbar_offset_y
        x += self.scrollbar_extra_offset_x
        y += self.scrollbar_extra_offset_y
        height += self.scrollbar_extra_length
        if self.scrollbar is not None:
            if self.scrollbar in self.elements:
                self.elements.remove(self.scrollbar)
            self.scrollbar = None
        self.scrollbar = VerticalScrollBar(x, y, scrollbar_width, height, max_noof_rows, self.noof_visible_items, scrollbar_button_size)
        self.scrollbar.add_on_scrolled_handler(self.on_scroll)
        self.elements.append(self.scrollbar)
        self.on_scroll(self.current_row_index, silent=True)
        return

    def recreate_scrollbar(self):
        self.__create_scroll_bar()

    def calculate_noof_visible_items(self, min_index):
        return math.floor(float(self.list_area_height) / float(self.row_height + self.line_spacing))

    def get_row_height(self, row=None, index=0):
        return self.row_height

    def on_scroll(self, index, silent=False):
        if self.media is not None and not silent:
            self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
        if index > self.scrollbar.max_scroll:
            index = self.scrollbar.max_scroll
        if index < 0:
            index = 0
        noof_rows = len(self.rows)
        self.noof_visible_items = self.calculate_noof_visible_items(index)
        self.scrollbar.set_visible_lines(self.noof_visible_items)
        if noof_rows > 0 and noof_rows != self.scrollbar.max_lines:
            self.scrollbar.scroll_pos = 0
            self.scrollbar.set_max_lines(noof_rows)
        self.min_index = index
        self.max_index = self.min_index + self.noof_visible_items
        noof_rows = len(self.rows) if len(self.rows) > 0 else 1
        self.scrollbar.set_max_lines(noof_rows)
        self.scroll_item_area_x = self.x1 + self.list_spacing
        x = self.scroll_item_area_x
        y = self.list_area_y - self.get_row_height()
        if self.scrollbar.is_disabled():
            self.scroll_item_width = self.width - self.list_spacing * 2
        else:
            self.scroll_item_width = self.width - self.list_spacing * 3 - max(self.scrollbar.width, self.scrollbar.button_size)
        self.set_list_items_position_on_scroll(x, y, self.scroll_item_width)
        return

    def set_list_items_position_on_scroll(self, x, y, width):
        for row_index, row in enumerate(self.rows):
            if row_index < self.min_index or row_index >= self.max_index:
                if row.enable_on_scroll:
                    row.set_enabled(False)
            elif row.enable_on_scroll:
                row.set_enabled(True)
            row.update_position(x, y, width, self.row_height, width)
            y -= self.row_height + self.line_spacing

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        if self.enabled == False:
            return
        for row in self.rows:
            if row.enabled:
                row.on_mouse_drag(x, y, dx, dy, button, modifiers)

        for element in self.elements:
            element.on_mouse_drag(x, y, dx, dy, button, modifiers)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.enabled == False:
            return
        for row in self.rows:
            if row.enabled:
                row.on_mouse_press(x, y, button, modifiers)

        for element in self.elements:
            element.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        if self.enabled == False or self.visible_content == False or self.visible == False:
            return
        selected_index = -1
        self.last_selected_item = self.current_row_index
        previously_selected_row = None
        if self.get_mouse_collides(x, y):
            if self.current_row_index is not None and self.current_row_index > -1 and self.current_row_index < len(self.rows):
                previously_selected_row = self.rows[self.current_row_index]
                if self.allow_unselect_row_on_click == False:
                    self.rows[self.current_row_index].set_selected(False, self.media)
            else:
                self.last_selected_item = -1
            for index, row in enumerate(self.rows):
                if not row.visible:
                    continue
                if not row.mouse_collides(x, y):
                    row.on_mouse_release(x, y, button, modifiers)
                    continue
                row.on_mouse_release(x, y, button, modifiers)
                if index < self.min_index or index > self.max_index:
                    continue
                if selected_index != -1:
                    break
                if row.mouse_collides(x, y):
                    if self.allow_unselect_row_on_click and previously_selected_row == row:
                        select_row = not row.get_is_selected()
                        self.select_row(self.rows[index], silent=False, fire_selected_row_event=False, selected=select_row)
                    else:
                        self.select_row(self.rows[index], silent=False, fire_selected_row_event=False)
                    self.__fire_on_item_selected_handler(row)
                    if self.rows[index].get_is_selected():
                        selected_index = index
                        self.current_row_index = index
                        self.on_row_selected(self.rows[index])

            if self.allow_unselect_row_on_click == False:
                if selected_index == -1 and self.last_selected_item > -1 and self.last_selected_item < len(self.rows):
                    self.select_row(self.rows[self.last_selected_item])
                    if self.rows[self.last_selected_item].get_is_selected():
                        self.on_row_selected(self.rows[self.last_selected_item])
                        self.current_row_index = self.last_selected_item
            self.last_selected_item = -1
        for item in self.elements:
            item.on_mouse_release(x, y, button, modifiers)

        return

    def on_row_selected(self, row):
        pass

    def get_mouse_collides(self, x, y, include_scrollbar=False):
        x1 = self.scroll_item_area_x
        y1 = self.y1
        x2 = self.x1 + self.width - self.list_spacing
        if not include_scrollbar and self.scrollbar is not None and not self.scrollbar.is_disabled():
            x2 -= self.scrollbar.width + self.list_spacing
        y2 = self.y1 - self.list_area_height
        return in_zone(x, y, x1, y2, x2, y1)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.enabled == False:
            return
        hovered_index = -1
        if self.get_mouse_collides(x, y):
            for index, row in enumerate(self.rows):
                row.on_mouse_motion(x, y, dx, dy)
                self.rows[index].set_hovered(False)
                if index < self.min_index or index > self.max_index:
                    continue
                if hovered_index == -1 and row.mouse_collides(x, y):
                    self.rows[index].set_hovered(True)
                    if self.rows[index].get_is_hovered():
                        hovered_index = index

        for item in self.elements:
            item.on_mouse_motion(x, y, dx, dy)

    def on_mouse_scroll(self, x, y, dx, dy):
        if self.enabled == False:
            return
        if self.get_mouse_collides(x, y):
            for element in self.get_elements():
                element.on_mouse_scroll(x, y, dx, dy)

    def on_text(self, value):
        if not self.enabled:
            return
        for row in self.rows:
            row.on_text(value)

        for element in self.get_elements():
            element.on_text(value)

    def on_text_motion(self, value):
        if not self.enabled:
            return
        for row in self.rows:
            row.on_text_motion(value)

        for element in self.get_elements():
            element.on_text_motion(value)

    def on_key_press(self, symbol, modifiers):
        if not self.enabled:
            return
        for row in self.rows:
            row.on_key_press(symbol, modifiers)

    def get_total_height_of_rows(self, only_visible=False):
        height = 0
        rows_visible = False
        for index, row in enumerate(self.rows):
            if only_visible and row.visible or not only_visible:
                height += self.get_row_height(row, index)
                rows_visible = True

        if self.has_header:
            height += self.title_height + LIST_PANEL_SPACING * 3
        return height

    def draw_list_items(self):
        color_index = 0
        for index, row in enumerate(self.rows):
            if index < self.min_index or index >= self.max_index:
                continue
            row.draw(self.list_items_background_colors[color_index])
            color_index += 1
            if color_index == len(self.list_items_background_colors):
                color_index = 0

    def draw(self):
        if self.visible == False:
            return
        if self.enable_background_resizing:
            if self.scrollbar.is_disabled():
                height = self.get_total_height_of_rows(only_visible=True)
                if height > self.original_height:
                    height = self.original_height
                self.height = height + self.frame_padding_height
            else:
                height = self.original_height
                self.height = height + self.frame_padding_height
        super(ListPanelBase, self).draw()
        self.draw_list_items()
        if not self.scrollbar.is_disabled():
            self.scrollbar.draw()
