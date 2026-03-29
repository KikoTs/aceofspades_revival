from aoslib.scenes.frontend.listPanelBase import ListPanelBase
from aoslib.scenes.main.categoryListItem import CategoryListItem
from aoslib.gui import VerticalScrollBar
from aoslib.images import global_images
from aoslib.media import HUD_AUDIO_ZONE
from aoslib.text import draw_text_with_size_validation
from aoslib.common import collides, in_zone
from shared.hud_constants import CATEGORY_ROW_HEIGHT, NORMAL_ROW_HEIGHT, LIST_PANEL_SPACING
from pyglet import gl
import math

class ExpandableListPanel(ListPanelBase):

    def initialize(self):
        self.category_row_map = {}
        self.set_row_height(CATEGORY_ROW_HEIGHT, NORMAL_ROW_HEIGHT)
        self.selected_before_collapsed = None
        self.last_mouse_selected_row = None
        super(ExpandableListPanel, self).initialize()
        return

    def set_row_height(self, category_row_height, normal_row_height):
        self.category_row_height = category_row_height
        self.normal_row_height = normal_row_height

    def reset_list(self):
        for row in [row for row in self.rows if hasattr(row, 'close')]:
            row.close()

        self.rows = []
        self.category_row_map = {}

    def add_list_item(self, category_row, rows):
        if category_row is None or len(rows) == 0:
            return
        category_row.expand_button_clicked_callback = self.on_category_row_expanded
        self.category_row_map[category_row] = rows
        self.rows.append(category_row)
        for row in rows:
            self.rows.append(row)

        self.__populate_rows_list()
        return

    def calculate_noof_visible_items(self, min_index):
        noof_visible_items = 0
        current_row_height = 0
        total_height = self.list_area_height
        for index, row in enumerate(self.rows):
            if type(row) is CategoryListItem:
                noof_visible_items += 1
                row_spacing = 0
                row_height = self.category_row_height + row_spacing
                current_row_height += row_height
            if current_row_height + row_height > total_height:
                break

        for index, row in enumerate(self.rows):
            if current_row_height + self.normal_row_height > total_height:
                break
            if type(row) is not CategoryListItem:
                noof_visible_items += 1
                current_row_height += self.normal_row_height

        return noof_visible_items

    def set_list_items_position_on_scroll(self, x, y, width):
        for row_index, row in enumerate(self.rows):
            if row_index < self.min_index or row_index >= self.max_index:
                if row.enable_on_scroll:
                    row.set_enabled(False)
                row.visible = False
            elif row.enable_on_scroll:
                row.set_enabled(True)
            row.visible = True
            row_height = self.get_row_height(row)
            if type(row) is CategoryListItem:
                row_spacing = 0
                if row_index > self.min_index and type(self.rows[row_index - 1]) is CategoryListItem:
                    row.spacing_colour = self.category_spacing_colour
                    row.enable_draw_spacing(True, self.category_row_spacing, self.category_spacing_colour)
                else:
                    row.enable_draw_spacing(False)
                row.update_position(x, y - row_spacing, width, row_height, width)
                y -= row_spacing
            else:
                row.update_position(x, y, width, row_height, width)
            if row_index + 1 < len(self.rows):
                row_height = self.get_row_height(self.rows[row_index + 1])
            y -= row_height + self.line_spacing

    def __populate_rows_list(self):
        self.rows = []
        for category_row in sorted(self.category_row_map.keys(), key=(lambda category_row: (category_row.sort_order, category_row.name))):
            self.rows.append(category_row)
            if category_row.is_expanded:
                for row in self.category_row_map[category_row]:
                    row.set_enabled(True)
                    self.rows.append(row)
                    if self.current_row_index == -1 and row == self.selected_before_collapsed:
                        self.last_selected_item = len(self.rows) - 1
                    elif self.current_row_index > -1 and row == self.last_mouse_selected_row:
                        self.last_selected_item = len(self.rows) - 1

            else:
                for row in self.category_row_map[category_row]:
                    row.set_enabled(False)

    def on_row_selected(self, row):
        self.selected_before_collapsed = None
        self.last_mouse_selected_row = row
        return

    def expand_all(self, expand=True, silent=False):
        category_rows = []
        for row in self.rows:
            if type(row) == CategoryListItem:
                category_rows.append(row)
                if expand:
                    row.expand()
                else:
                    row.collapse()

        if len(category_rows) > 0:
            self.on_row_expanded_changed(category_rows, silent=silent)

    def on_row_expanded_changed(self, category_rows, silent=False):
        prev_noof_rows = len(self.rows)
        selected_row = self.get_selected_item()
        for category_row in category_rows:
            for row in self.category_row_map[category_row]:
                row.visible = category_row.is_expanded
                if category_row.is_expanded == False and selected_row == row:
                    self.selected_before_collapsed = row
                    self.current_row_index = -1
                    self.last_selected_item = -1

        self.__populate_rows_list()
        last_scroll = self.scrollbar.scroll_pos
        noof_rows = len(self.rows)
        noof_rows_removed = prev_noof_rows - noof_rows
        if noof_rows_removed > 0:
            if noof_rows - self.noof_visible_items - last_scroll < 0:
                last_scroll = max(last_scroll - noof_rows_removed, noof_rows - self.noof_visible_items, 0)
        self.scrollbar.set_scroll(last_scroll, force_callback_call=True, silent=silent)

    def on_category_row_expanded(self, category_row, silent=False):
        self.on_row_expanded_changed([category_row], silent=silent)

    def initialise_ui(self, title, x, y, width, height, has_header=False, enable_background_resizing=False, category_spacing=2, category_spacing_colour=(0, 0, 0, 0)):
        super(ExpandableListPanel, self).initialise_ui(title, x, y, width, height, has_header=has_header, enable_background_resizing=enable_background_resizing)
        self.category_row_spacing = category_spacing
        self.category_spacing_colour = category_spacing_colour

    def get_row_height(self, row=None, index=0):
        if row == None:
            index = int(self.min_index)
            if index >= 0 and index < len(self.rows):
                return self.get_row_height(self.rows[index])
            return self.normal_row_height
        else:
            if type(row) is CategoryListItem:
                height = self.category_row_height
                if index > int(self.min_index):
                    height += self.category_row_spacing
                return height
            return self.normal_row_height

    def draw_list_items(self):
        colours = []
        color_index = 0
        for index, row in enumerate(self.rows):
            if index < self.min_index or index >= self.max_index:
                if type(row) is CategoryListItem:
                    colours = row.sub_row_colours
                continue
            if row.visible == False:
                continue
            if type(row) is CategoryListItem:
                row.draw()
                colours = row.sub_row_colours
                continue
            if len(colours) == 0:
                row_colour = (0, 0, 0, 255)
            else:
                row_colour = colours[color_index]
            row.draw(row_colour)
            color_index += 1
            if color_index == len(self.list_items_background_colors):
                color_index = 0
