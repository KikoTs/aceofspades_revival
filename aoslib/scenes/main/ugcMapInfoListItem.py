from aoslib.scenes.main.listPanelItemBase import ListPanelItemBase
from aoslib.text import draw_text_with_alignment_and_size_validation, medium_aldo_ui_font, big_aldo_ui_font
from pyglet import gl
from aoslib import strings
from shared.hud_constants import TEXT_BACKGROUND_SPACING, UGC_MORE_DATA_COLOUR, UGC_PUBLISHED_MAP_COLOUR
from shared.constants import MENU_FONT_COLOR
MODE_STATE_COMPLETED, MODE_STATE_DATA_REQUIRED = xrange(2)
MODE_STATE_NAME = {MODE_STATE_COMPLETED: 'COMPLETED', 
   MODE_STATE_DATA_REQUIRED: 'CANNOT_BE_PUBLISHED'}

class UGCMapInfoListItem(ListPanelItemBase):

    def initialize(self, name, state=MODE_STATE_DATA_REQUIRED, reason=''):
        super(UGCMapInfoListItem, self).initialize(name)
        self.state = state
        self.reason = reason

    def set_hovered(self, hovered):
        pass

    def set_selected(self, selected, media):
        pass

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
        if self.state == MODE_STATE_COMPLETED:
            colour = UGC_PUBLISHED_MAP_COLOUR
        elif self.state == MODE_STATE_DATA_REQUIRED:
            colour = UGC_MORE_DATA_COLOUR
        else:
            colour = MENU_FONT_COLOR
        try:
            if self.reason == '':
                state_name = '' if self.state not in MODE_STATE_NAME else '[' + strings.get_by_id_or_except(MODE_STATE_NAME[self.state]) + ']'
            else:
                state_name = '[' + strings.get_by_id_or_except(self.reason) + ']'
        except KeyError:
            state_name = ''

        draw_text_with_alignment_and_size_validation(state_name, state_x, self.y1, width, self.height, colour, self.font, 'right', 'center')
        draw_text_with_alignment_and_size_validation(self.name, name_x, self.y1, width, self.height, colour, self.font, 'left', 'center')
