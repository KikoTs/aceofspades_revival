from aoslib.scenes.main.listPanelItemBase import ListPanelItemBase
from aoslib.text import draw_text_with_alignment_and_size_validation, medium_aldo_ui_font, big_aldo_ui_font
from pyglet import gl
from aoslib import strings
from shared.hud_constants import TEXT_BACKGROUND_SPACING, UGC_PUBLISHED_MAP_COLOUR, UGC_UNPUBLISHED_MAP_COLOUR, UGC_MORE_DATA_COLOUR, UGC_DATA_CHANGED_COLOUR
from shared.constants import MENU_FONT_COLOR
MAP_STATE_PUBLISHED, MAP_STATE_UNPUBLISHED, MAP_STATE_DATA_REQUIRED, MAP_STATE_CHANGED = xrange(4)
MAP_STATE_NAME = {MAP_STATE_PUBLISHED: 'PUBLISHED', 
   MAP_STATE_UNPUBLISHED: 'UNPUBLISHED', 
   MAP_STATE_DATA_REQUIRED: 'CANNOT_BE_PUBLISHED', 
   MAP_STATE_CHANGED: 'UGC_CHANGED_SINCE_PUBLISH'}

class UGCMapListItem(ListPanelItemBase):

    def initialize(self, name, state=MAP_STATE_UNPUBLISHED, publishable_modes=[], unpublishable_modes={}, uid=None):
        super(UGCMapListItem, self).initialize(name, uid=uid)
        self.publishable_modes = publishable_modes
        self.unpublishable_modes = unpublishable_modes
        self.state = state

    def draw_name(self):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        y = self.get_text_y_position()
        pad_x = 20
        pad_y = 10
        height = self.height - pad_y
        right_text_width = 25
        right_text_x = self.x1 + self.width - pad_x / 2 - right_text_width
        pad_x = 15
        width = self.width / 2 - TEXT_BACKGROUND_SPACING * 2
        name_x = self.x1 + TEXT_BACKGROUND_SPACING
        state_x = name_x + width + TEXT_BACKGROUND_SPACING * 2
        name_colour = MENU_FONT_COLOR
        if self.state == MAP_STATE_PUBLISHED:
            colour = UGC_PUBLISHED_MAP_COLOUR
            name_colour = colour
        elif self.state == MAP_STATE_UNPUBLISHED:
            colour = UGC_UNPUBLISHED_MAP_COLOUR
        elif self.state == MAP_STATE_DATA_REQUIRED:
            colour = UGC_MORE_DATA_COLOUR
        elif self.state == MAP_STATE_CHANGED:
            colour = UGC_DATA_CHANGED_COLOUR
        else:
            colour = MENU_FONT_COLOR
        state_name = '' if self.state not in MAP_STATE_NAME else '[' + strings.get_by_id(MAP_STATE_NAME[self.state]) + ']'
        draw_text_with_alignment_and_size_validation(state_name, state_x, self.y1, width, self.height, colour, self.font, 'right', 'center')
        draw_text_with_alignment_and_size_validation(self.name, name_x, self.y1, width, self.height, name_colour, self.font, 'left', 'center')
