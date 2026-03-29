from aoslib.scenes.main.listPanelItemBase import ListPanelItemBase
from aoslib.scenes.main.listPanelItemMultiColumn import ListPanelItemMultiColumn
from aoslib.text import draw_text_with_size_validation, small_edo_ui_font, medium_edo_ui_font, big_edo_ui_font
from aoslib.text import reserve_font, draw_text_with_alignment_and_size_validation
from pyglet import gl
from shared.constants import MENU_FONT_COLOR
from shared.constants import LIGHT_GREEN
from shared.constants import DARK_GREEN
from shared.hud_constants import RED_BAR_FLAT_COLOUR
from aoslib.common import *
from aoslib.draw import draw_quad
from aoslib.images import global_images
from aoslib import strings

class PlayerProfileSummaryListItem(ListPanelItemMultiColumn):

    def initialize(self, name, rank, text_colour=MENU_FONT_COLOR, background_tint=(1.0, 1.0, 1.0, 1.0)):
        super(PlayerProfileSummaryListItem, self).initialize()
        self.name = name
        self.rank = rank
        self.text_colour = text_colour
        self.background_tint = background_tint
        self.center_text = False

    def set_selected(self, selected, media):
        pass

    def set_hovered(self, hovered):
        pass

    def update_position(self, x, y, width, height, highlight_width):
        self.column_widths = [
         width / 2, width / 2]
        column_texts = [self.name, self.rank]
        self.set_columns(column_texts)
        super(PlayerProfileSummaryListItem, self).update_position(x, y, width, height, highlight_width)

    def draw(self, colour):
        background_col = tint_colour(colour, self.background_tint)
        super(PlayerProfileSummaryListItem, self).draw(background_col, self.column_widths)

    def draw_name(self):
        pass


class PlayerProfileCategoryItem(ListPanelItemBase):

    def initialize(self, name):
        super(PlayerProfileCategoryItem, self).initialize(name)
        self.center_text = False
        self.small_font = small_edo_ui_font
        self.medium_font = medium_edo_ui_font
        self.big_font = big_edo_ui_font
        self.font = self.medium_font

    def set_selected(self, selected, media):
        pass

    def get_text_x_position(self):
        pad_x = self.get_pad_x_for_width(self.width * 0.5)
        x = self.x1 + pad_x
        return x

    def set_hovered(self, hovered):
        pass

    def draw_background(self, colour):
        red_bar_left = global_images.red_header_left
        red_bar_right = global_images.red_header_right
        x_left = self.x1 + red_bar_left.width / 2
        x_right = self.x1 + self.width - red_bar_right.width / 2 - 2
        y_for_image = self.y1 + 12
        red_bar_left.blit(x_left, y_for_image, 0, red_bar_left.width, self.height)
        red_bar_right.blit(x_right, y_for_image, 0, red_bar_left.width, self.height)
        draw_quad(self.x1 + red_bar_left.width, self.y1, self.width - red_bar_right.width - red_bar_left.width, self.height, RED_BAR_FLAT_COLOUR)


class PlayerProfileCategoryMultiColumnItem(ListPanelItemMultiColumn):

    def initialize(self, name, column2_title):
        self.column2_title = column2_title
        super(PlayerProfileCategoryMultiColumnItem, self).initialize(name)
        self.center_text = False
        self.small_font = small_edo_ui_font
        self.medium_font = medium_edo_ui_font
        self.big_font = big_edo_ui_font
        self.font = self.medium_font

    def set_selected(self, selected, media):
        pass

    def set_hovered(self, hovered):
        pass

    def update_position(self, x, y, width, height, highlight_width):
        self.column_widths = [
         width / 2, width / 2]
        column_texts = [self.name, self.column2_title]
        self.set_columns(column_texts)
        super(PlayerProfileCategoryMultiColumnItem, self).update_position(x, y, width, height, highlight_width)

    def draw_background(self, colour, widths):
        if widths is None:
            super(PlayerProfileCategoryMultiColumnItem, self).draw_background(RED_BAR_FLAT_COLOUR, widths)
            return
        else:
            red_bar_left = global_images.red_header_left
            red_bar_right = global_images.red_header_right
            x_left = self.x1 + red_bar_left.width / 2
            x_right = self.x1 + self.width - red_bar_right.width / 2 - 2
            y_for_image = self.y1 + 12
            red_bar_left.blit(x_left, y_for_image, 0, red_bar_left.width, self.height)
            red_bar_right.blit(x_right, y_for_image, 0, red_bar_left.width, self.height)
            column_x1 = self.x1
            total_widths = 0
            for index, column_width in enumerate(widths):
                x1 = column_x1
                width = column_width
                if index == 0:
                    x1 += red_bar_left.width
                    width -= red_bar_left.width
                elif index == len(widths) - 1:
                    width -= red_bar_right.width
                draw_quad(x1, self.y1, width - self.separator_width, self.height, RED_BAR_FLAT_COLOUR)
                column_x1 += column_width
                total_widths += column_width

            return

    def draw_name(self):
        pass

    def draw(self, colour):
        background_col = colour
        super(PlayerProfileCategoryMultiColumnItem, self).draw(background_col, self.column_widths)


class PlayerProfileStatListItem(ListPanelItemMultiColumn):
    progress_bar_img = global_images.profile_level_bar_bg

    def initialize(self, name, score, colour_override=None):
        super(PlayerProfileStatListItem, self).initialize()
        self.name = name
        self.score = score
        self.text_colour = MENU_FONT_COLOR
        self.colour_override = colour_override
        self.show_bar = False
        self.center_text = False

    def setup_bar(self, level=1, next_level_min=0, next_level_max=0):
        self.show_bar = True
        self.level = level
        self.next_level_min = next_level_min
        self.next_level_max = next_level_max

    def set_selected(self, selected, media):
        pass

    def set_hovered(self, hovered):
        pass

    def update_position(self, x, y, width, height, highlight_width):
        self.column_widths = [
         width / 2, width / 2]
        if self.show_bar:
            column_texts = [
             self.name, '']
        else:
            column_texts = [
             self.name, str(self.score)]
        self.set_columns(column_texts)
        super(PlayerProfileStatListItem, self).update_position(x, y, width, height, highlight_width)

    def draw(self, colour):
        background_col = colour
        if self.colour_override != None:
            background_col = self.colour_override
        super(PlayerProfileStatListItem, self).draw(background_col, self.column_widths)
        if self.show_bar == True:
            self.draw_bar()
        return

    def draw_name(self):
        pass

    def draw_bar(self):
        colFront = LIGHT_GREEN
        colBehind = DARK_GREEN
        horz_padding = 2
        bar_pos_x = self.x1 + self.width / 2 + horz_padding
        bar_pos_y = self.y1 + 2
        bar_width = self.width / 2 - horz_padding * 2 - self.separator_width
        bar_height = self.height - 4
        draw_quad(bar_pos_x, bar_pos_y, bar_width, bar_height, colBehind)
        level_colour = self.text_colour
        fraction_colour = self.text_colour
        range = self.next_level_max - self.next_level_min
        percent = 0
        if range != 0:
            percent = 100.0 / range * (self.score - self.next_level_min)
        progress = bar_width / 100.0 * percent
        if progress > bar_width:
            progress = bar_width
        if progress < 0:
            progress = 0
        draw_quad(bar_pos_x, bar_pos_y, progress, bar_height, colFront)
        progress_text_offset_x = 100
        bar_text_margin = self.get_column_text_x_offset(self.column_widths, 1)
        bar_left_text_x = self.get_column_x1(self.column_widths, 1) + bar_text_margin
        text_y = self.get_text_y_position()
        self.font.draw(strings.LEVEL + ' ' + str(self.level), bar_left_text_x, text_y, level_colour, center=False)
        draw_text_with_alignment_and_size_validation(str(self.score) + ' / ' + str(int(self.next_level_max)), bar_pos_x + bar_width - progress_text_offset_x, text_y, progress_text_offset_x - bar_text_margin, self.height, fraction_colour, font=self.font, alignment_x='right')
