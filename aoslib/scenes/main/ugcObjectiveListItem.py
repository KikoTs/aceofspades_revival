from shared.constants_ugc_objectives import *
from aoslib.text import draw_text_with_alignment_and_size_validation, get_resized_font_and_formatted_text_to_fit_boundaries, get_line_scale_from_text_and_width
from aoslib import strings
from pyglet import gl
from aoslib.scenes.main.listPanelItemBase import ListPanelItemBase
from shared.constants import MENU_FONT_COLOR, LIGHT_RED, LIGHT_GREEN
from shared.hud_constants import TEXT_BACKGROUND_SPACING

class UGCObjectiveListItem(ListPanelItemBase):

    def initialize(self, objective_id, value=0):
        super(UGCObjectiveListItem, self).initialize()
        self.objective_id = objective_id
        self.max_value = UGC_OBJECTIVES_TYPES[self.objective_id]['max']
        self.min_value = UGC_OBJECTIVES_TYPES[self.objective_id]['min']
        self.priority = UGC_OBJECTIVES_TYPES[self.objective_id]['priority']
        self.update_done = False
        self.value = value
        self.name = strings.get_by_id(self.objective_id) + ' (' + strings.MAX + ': ' + str(self.max_value) + ')'

    def update_position(self, x, y, width, height, highlight_width):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.pad = height * 0.03
        self.y2 = y + height
        self.width = width
        self.height = height
        self.highlight_width = highlight_width
        self.spacing = self.width * 0.02
        self.pad_x = self.get_pad_x_for_width(self.width)
        self.name_width = self.width * 0.8 - TEXT_BACKGROUND_SPACING
        self.value_width = self.width * 0.15 - TEXT_BACKGROUND_SPACING
        self.set_font_for_row_height()
        self.force_scale = get_line_scale_from_text_and_width(self.name, self.name_width, self.font)
        self.font_to_use, self.text_lines = get_resized_font_and_formatted_text_to_fit_boundaries(self.name, self.name_width, self.height, self.font, 2, dont_split=True)
        self.update_done = True

    def get_is_complete(self):
        if self.value > self.max_value or self.value < self.min_value:
            return False
        return True

    def draw_selection_highlight(self):
        pass

    def draw_hovered_highlight(self):
        pass

    def draw_name(self):
        if not self.update_done:
            return
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        colour = MENU_FONT_COLOR
        values_colour = LIGHT_GREEN
        if self.value > self.max_value:
            values_colour = LIGHT_RED
        if self.value < self.min_value:
            values_colour = LIGHT_RED
        text_name = self.name
        draw_text_with_alignment_and_size_validation(self.name, self.x1 + TEXT_BACKGROUND_SPACING, self.y1, self.name_width, self.height, colour, self.font_to_use, 'left', 'center', forced_scale=self.force_scale)
        text_values = str(self.value)
        if self.min_value != 0:
            text_values += ' / ' + str(self.min_value)
        draw_text_with_alignment_and_size_validation(text_values, self.x1 + self.width - self.value_width - TEXT_BACKGROUND_SPACING, self.y1, self.value_width, self.height, values_colour, self.font_to_use, 'right', 'center', forced_scale=self.force_scale)
