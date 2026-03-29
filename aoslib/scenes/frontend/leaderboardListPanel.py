from aoslib.images import global_images
from aoslib.media import HUD_AUDIO_ZONE
from aoslib.common import in_zone
from pyglet import gl
from pyglet.gl import glPushMatrix, glPopMatrix, glScalef, glTranslatef, glColor4f
import math
from aoslib.scenes.frontend.leaderboardListItem import *
from aoslib.scenes.frontend.listPanelBase import *
from shared.hud_constants import *
from shared.constants import NOT_SORTING, SORTING_DOWN, SORTING_UP
from aoslib.text import small_edo_ui_font, small_standard_ui_font, tiny_edo_ui_font, modify_name_to_fix_width
from aoslib.gui import HorizontalScrollBar

class LeaderboardListPanel(ListPanelBase):
    horizontal_scroll_position = 0

    def initialize(self):
        self.columns = []
        self.column_widths = []
        self.column_names = []
        self.column_sorting = []
        self.noof_visible_columns = 0
        self.row_width = 0
        self.row_height = LEADERBOARD_MENU_GRID_ROW_HEIGHT
        self.column_header_row = None
        self.top_padding = 5
        self.horizontal_scrollbar = None
        super(LeaderboardListPanel, self).initialize()
        self.sorting_column_index = None
        self.header_font = small_edo_ui_font
        self.row_width = self.scroll_item_width
        self.first_scrolling_column_index = 2
        self.horizontal_scroll_position = 0
        return

    def initialise_ui(self, title, x, y, width, height, row_height=20, has_header=False, list_items_background_colors=None, spacing=None):
        super(LeaderboardListPanel, self).initialise_ui(title, x, y, width, height, row_height, has_header, list_items_background_colors, spacing)
        self.column_header_row = LeaderboardListItem()
        self.__create_horizontal_scroll_bar()

    def populate(self, rows):
        self.rows = []
        for row_index, row in enumerate(rows):
            row.update_position(x=self.x, y=self.list_area_y - LEADERBOARD_MENU_GRID_ROW_HEIGHT - row_index * LEADERBOARD_MENU_GRID_ROW_HEIGHT, width=self.row_width, height=self.row_height, highlight_width=row.highlight_width)
            row.font = small_standard_ui_font
            row.column_texts[1] = modify_name_to_fix_width(row.column_texts[1], LEADERBOARD_MENU_GRID_COLUMN_NAME_WIDTH, small_standard_ui_font)
            row.first_scrolling_column_index = self.first_scrolling_column_index
            self.rows.append(row)

        self.scrollbar.set_scroll(0, force_callback_call=True, silent=True)
        self.refresh_visible_columns(self.columns, self.horizontal_scroll_position)

    def set_columns(self, columns):
        self.sorting_column_index = None
        self.columns = columns
        max_columns = max(len(self.columns) - self.first_scrolling_column_index, 0)
        self.horizontal_scrollbar.set_max_lines(max_columns)
        self.horizontal_scrollbar.set_scroll(0, force_callback_call=True, silent=True)
        self.refresh_visible_columns(self.columns, self.horizontal_scroll_position)
        return

    def on_scroll(self, index, silent=False):
        if self.media is not None and not silent:
            self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
        if index > self.scrollbar.max_scroll:
            index = self.scrollbar.max_scroll
        noof_rows = len(self.rows)
        self.noof_visible_items = self.calculate_noof_visible_items(index)
        self.scrollbar.set_visible_lines(self.noof_visible_items)
        if noof_rows > 0 and noof_rows != self.scrollbar.max_lines:
            self.scrollbar.scroll_pos = 0
            self.scrollbar.set_max_lines(noof_rows)
        self.min_index = index
        self.max_index = self.min_index + self.noof_visible_items
        noof_rows = len(self.rows) if len(self.rows) > 0 else 1
        self.scrollbar.set_max_lines(noof_rows + 1)
        self.scroll_item_area_x = self.x1 + LIST_PANEL_SPACING
        x = self.scroll_item_area_x
        y = self.list_area_y - self.get_row_height()
        if self.scrollbar.is_disabled():
            self.scroll_item_width = self.width - LIST_PANEL_SPACING * 2
        else:
            self.scroll_item_width = self.width - LIST_PANEL_SPACING * 3 - max(self.scrollbar.width, self.scrollbar.button_size)
        self.set_list_items_position_on_scroll(x, y, self.scroll_item_width)
        return

    def on_horizontal_scroll(self, index, silent=False):
        self.horizontal_scroll_position = int(math.floor(index))
        self.column_header_row.set_horizontal_scroll_index(self.horizontal_scroll_position)
        for row in self.rows:
            row.set_horizontal_scroll_index(self.horizontal_scroll_position)

        for column_index, column in enumerate(self.columns):
            if column_index < self.first_scrolling_column_index:
                self.columns[column_index][3] = True
            elif column_index - self.first_scrolling_column_index >= self.horizontal_scroll_position and column_index - self.first_scrolling_column_index - self.horizontal_scroll_position < self.noof_visible_columns:
                self.columns[column_index][3] = True
            else:
                self.columns[column_index][3] = False

    def refresh_selection(self):
        for index, row in enumerate(self.rows):
            if row._is_selected:
                self.current_row_index = index
                row.set_selected(True, None)
            else:
                row.set_selected(False, None)

        return

    def sort_rows(self, sort_type, sorting_column_index):
        reverse = sort_type == SORTING_UP
        if sorting_column_index > 1:
            reverse = not reverse
        if sorting_column_index != 1:
            self.rows.sort(key=(lambda row: float(row.column_texts[sorting_column_index])), reverse=reverse)
        else:
            self.rows.sort(key=(lambda row: row.column_texts[sorting_column_index]), reverse=reverse)
        self.refresh_selection()
        self.scrollbar.set_scroll(0, force_callback_call=True, silent=True)

    def on_mouse_release(self, x, y, button, modifiers):
        if not self.enabled:
            return
        header_pos_x = self.x + LIST_PANEL_SPACING
        header_pos_y = self.list_area_y - self.row_height - self.top_padding
        header_width = self.row_width
        header_height = self.row_height
        if in_zone(x, y, header_pos_x, header_pos_y, header_pos_x + header_width, header_pos_y + header_height):
            current_column_position_x = header_pos_x
            for column_index, column in enumerate(self.columns):
                column_name, column_width, column_sort, column_visible = column
                if column_visible:
                    if column_visible and x >= current_column_position_x and x < current_column_position_x + column_width:
                        self.sorting_column_index = column_index
                        if self.column_sorting[column_index] == SORTING_DOWN:
                            self.column_sorting[column_index] = SORTING_UP
                        else:
                            self.column_sorting[column_index] = SORTING_DOWN
                    else:
                        self.column_sorting[column_index] = NOT_SORTING
                    current_column_position_x += column_width

            self.sort_rows(self.column_sorting[self.sorting_column_index], self.sorting_column_index)
        else:
            super(LeaderboardListPanel, self).on_mouse_release(x, y, button, modifiers)

    def draw_grid_header(self):
        self.min_index = int(self.min_index)
        header_pos_x = self.x + LIST_PANEL_SPACING
        header_pos_y = self.list_area_y - self.row_height - self.top_padding
        header_height = self.row_height
        header_right_edge_offset = 10
        header_left_edge_offset = 12
        header_width = self.row_width
        half_header_height = math.floor(float(header_height) / 2.0)
        self.column_header_row.update_position(x=header_pos_x, y=header_pos_y, width=header_width, height=header_height, highlight_width=0)
        glPushMatrix()
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glPushMatrix()
        glTranslatef(header_pos_x + header_width - header_left_edge_offset, header_pos_y + half_header_height, 0.0)
        global_images.red_header_right.blit(0, 0, height=header_height)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(header_pos_x + header_right_edge_offset, header_pos_y + half_header_height, 0.0)
        global_images.red_header_left.blit(0, 0, height=header_height)
        glPopMatrix()
        glPopMatrix()
        self.column_header_row.center_text = False
        self.column_header_row.draw(RED_BAR_FLAT_COLOUR, self.column_widths)
        sort_icon_position_x = header_pos_x - LEADERBOARD_MENU_GRID_SORT_ICON_RIGHT_PADDING
        for column_index, column in enumerate(self.columns):
            column_name, column_width, column_sort, column_visible = column
            if column_visible:
                sort_icon_position_x += column_width
                glPushMatrix()
                glTranslatef(sort_icon_position_x, header_pos_y + half_header_height, 0.0)
                if self.column_sorting[column_index] == SORTING_DOWN:
                    global_images.filter_down.blit(0, 0)
                elif self.column_sorting[column_index] == SORTING_UP:
                    global_images.filter_up.blit(0, 0)
                else:
                    global_images.filter_down_white.blit(0, 0)
                glPopMatrix()

        glColor4f(1.0, 1.0, 1.0, 1.0)

    def draw_list_items(self):
        color_index = 0
        self.draw_grid_header()
        for index, row in enumerate(self.rows):
            if index < self.min_index:
                continue
            elif index >= self.max_index - 1:
                break
            row.center_text = False
            row.draw(self.list_items_background_colors[color_index], self.column_widths)
            color_index += 1
            if color_index == len(self.list_items_background_colors):
                color_index = 0

    def set_list_items_position_on_scroll(self, x, y, width):
        y = y - self.row_height - self.top_padding
        for row_index, row in enumerate(self.rows):
            if row_index < self.min_index or row_index >= self.max_index - 1:
                if row.enable_on_scroll:
                    row.set_enabled(False)
            elif row.enable_on_scroll:
                row.set_enabled(True)
            row.update_position(x, y, width, self.row_height, width)
            y -= self.row_height + self.line_spacing

    def __create_horizontal_scroll_bar(self, scrollbar_thickness=25):
        self.horizontal_scrollbar = HorizontalScrollBar(0, 0, 0, scrollbar_thickness, 0, 0)
        self.horizontal_scrollbar.add_on_scrolled_handler(self.on_horizontal_scroll)
        self.elements.append(self.horizontal_scrollbar)

    def draw(self):
        if self.visible == False:
            return
        super(LeaderboardListPanel, self).draw()
        if not self.horizontal_scrollbar.is_disabled():
            self.horizontal_scrollbar.draw()

    def readjust_column_widths(self):
        if len(self.columns) < self.first_scrolling_column_index:
            return
        rank_and_name_width = self.columns[0][1] + self.columns[1][1]
        added_column_width = 0
        widest_column_width = 0
        for column_index in xrange(self.first_scrolling_column_index, len(self.columns)):
            column_required_width = self.header_font.get_content_width(self.columns[column_index][0]) + LEADERBOARD_MENU_GRID_COLUMN_TEXT_PADDING
            added_column_width += column_required_width
            widest_column_width = max(widest_column_width, column_required_width)

        remaining_width = self.row_width - (added_column_width + rank_and_name_width)
        extra_padding_from_remaining_space = math.floor(remaining_width / (len(self.columns) - self.first_scrolling_column_index))
        last_column_offset = max(remaining_width - extra_padding_from_remaining_space * (len(self.columns) - self.first_scrolling_column_index), 0)
        if remaining_width >= 0:
            resize_column_widths = False
            for column_index in xrange(self.first_scrolling_column_index, len(self.columns)):
                cwidth = self.header_font.get_content_width(self.columns[column_index][0]) + LEADERBOARD_MENU_GRID_COLUMN_TEXT_PADDING + extra_padding_from_remaining_space
                self.columns[column_index][1] = cwidth

        else:
            resize_column_widths = True
            for column_index in xrange(self.first_scrolling_column_index, len(self.columns)):
                self.columns[column_index][1] = widest_column_width

        if resize_column_widths:
            available_scrolling_space = self.row_width - rank_and_name_width
            self.noof_visible_columns = min(int(math.floor(float(available_scrolling_space) / float(widest_column_width))), len(self.columns) - self.first_scrolling_column_index)
            if self.noof_visible_columns <= 0:
                print 'no columns fit'
                return
            resized_column_width = math.floor(float(available_scrolling_space) / float(self.noof_visible_columns))
            for column_index in xrange(self.first_scrolling_column_index, len(self.columns)):
                self.columns[column_index][1] = resized_column_width

            last_column_offset = self.row_width - (rank_and_name_width + resized_column_width * self.noof_visible_columns)
        else:
            self.noof_visible_columns = len(self.columns) - self.first_scrolling_column_index
        if last_column_offset > 0:
            last_visible_column_index = self.noof_visible_columns + (self.first_scrolling_column_index - 1) + self.horizontal_scroll_position
            self.columns[last_visible_column_index][1] += last_column_offset
        if self.horizontal_scrollbar:
            horizontal_scrollbar_position_x = self.x + LIST_PANEL_SPACING + rank_and_name_width
            horizontal_scrollbar_position_y = self.list_area_y - (self.noof_visible_items + 1) * self.row_height
            horizontal_scrollbar_width = self.row_width - rank_and_name_width
            horizontal_scrollbar_height = self.horizontal_scrollbar.height
            self.reposition_horizontal_scrollbar(x=horizontal_scrollbar_position_x, y=horizontal_scrollbar_position_y, width=horizontal_scrollbar_width, height=horizontal_scrollbar_height)
        if self.scrollbar:
            vertical_scrollbar_position_x = self.scrollbar.x
            vertical_scrollbar_width = self.scrollbar.width
            vertical_scrollbar_height = self.list_area_height
            vertical_scrollbar_position_y = self.list_area_y - self.list_area_height + self.scrollbar_offset_y
            vertical_scrollbar_position_y += self.scrollbar_extra_offset_y
            vertical_scrollbar_height += self.scrollbar_extra_length
            if self.horizontal_scrollbar and not self.horizontal_scrollbar.is_disabled():
                vertical_scrollbar_height += -self.row_height
                vertical_scrollbar_position_y += self.row_height
            self.reposition_vertical_scrollbar(x=vertical_scrollbar_position_x, y=vertical_scrollbar_position_y, width=vertical_scrollbar_width, height=vertical_scrollbar_height)

    def reposition_vertical_scrollbar(self, x, y, width, height):
        if not self.scrollbar:
            return
        self.scrollbar.initialize(x, y, width, height, self.horizontal_scrollbar.max_lines, self.noof_visible_columns, button_size=22)
        self.scrollbar.add_on_scrolled_handler(self.on_scroll)
        self.scrollbar.set_scroll(0, force_callback_call=True, silent=True)

    def reposition_horizontal_scrollbar(self, x, y, width, height):
        if not self.horizontal_scrollbar:
            return
        self.horizontal_scrollbar.initialize(x, y, width, height, self.horizontal_scrollbar.max_lines, self.noof_visible_columns, button_size=22)
        self.horizontal_scrollbar.add_on_scrolled_handler(self.on_horizontal_scroll)
        self.horizontal_scrollbar.set_scroll(0, force_callback_call=True, silent=True)

    def refresh_visible_columns(self, columns, horizontal_scroll_position):
        self.row_width = self.scroll_item_width
        self.readjust_column_widths()
        self.column_widths = []
        self.column_names = []
        self.column_sorting = []
        total_column_width = 0
        for column_index, column in enumerate(self.columns):
            column_name, column_width, column_sort, column_visible = column
            total_column_width += column_width
            if total_column_width <= self.row_width:
                self.columns[column_index][3] = True
                self.column_widths.append(column_width)
            else:
                self.columns[column_index][3] = False
            self.column_names.append(column_name)
            self.column_sorting.append(NOT_SORTING)

        self.column_header_row.set_columns(self.column_names)
        self.column_header_row.font = self.header_font
        self.column_header_row.first_scrolling_column_index = self.first_scrolling_column_index
        self.noof_visible_items = self.calculate_noof_visible_items(self.min_index)
        self.scrollbar.set_visible_lines(self.noof_visible_items)

    def calculate_noof_visible_items(self, min_index):
        noof_visible_items = super(LeaderboardListPanel, self).calculate_noof_visible_items(min_index)
        if self.horizontal_scrollbar and not self.horizontal_scrollbar.is_disabled():
            noof_visible_items = max(noof_visible_items - 1, 0)
        return noof_visible_items
