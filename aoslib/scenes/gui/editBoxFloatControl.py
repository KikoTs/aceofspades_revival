from aoslib.scenes.gui.editBoxControl import EditBoxControl
from pyglet import gl
from pyglet.window import key
from pyglet.window import mouse
from aoslib.draw import draw_quad, draw_line
from aoslib.images import global_images
from shared.constants import MENU_FONT_COLOR
from aoslib.common import multiply_color
from aoslib.text import draw_text_with_alignment_and_size_validation, small_standard_ui_font, medium_standard_ui_font
from shared.hud_constants import UI_CONTROL_SPACING, EDIT_BOX_BACKGROUND_COLOUR, MINIMUM_HEIGHT_FOR_MEDIUM_FONT
import time, copy

class EditBoxFloatControl(EditBoxControl):

    def initialize(self, value, x, y, width, height, min_value=0.0, max_value=1.0, decimal_places=2):
        self.decimal_places = decimal_places
        self.min_value = min_value
        self.max_value = max_value
        super(EditBoxFloatControl, self).initialize(value, x, y, width, height, typ=float)

    def on_return(self):
        self.value = max(self.min_value, self.value)
        self.value = min(self.max_value, self.value)
        self.value = round(self.value, self.decimal_places)
        self.set(self.value)
        super(EditBoxFloatControl, self).on_return()
