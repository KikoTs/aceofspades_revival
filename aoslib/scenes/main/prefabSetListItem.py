from aoslib.scenes.main.listPanelItemBase import ListPanelItemBase
from aoslib.common import collides
from aoslib.images import global_images
from aoslib.text import draw_text_with_size_validation, get_resized_font_and_formatted_text_to_fit_boundaries, big_standard_ui_font, medium_standard_ui_font, small_standard_ui_font
from aoslib.draw import draw_quad
from pyglet import gl
from shared.constants import MENU_FONT_COLOR
from shared.hud_constants import MINIMUM_HEIGHT_FOR_BIG_FONT, MINIMUM_HEIGHT_FOR_MEDIUM_FONT, TEXT_BACKGROUND_SPACING

class PrefabSetListItem(ListPanelItemBase):

    def initialize(self, name, id):
        super(PrefabSetListItem, self).initialize(name)
        self.id = id
