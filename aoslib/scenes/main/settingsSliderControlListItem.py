from aoslib.scenes.main.settingsListItemBase import SettingsListItemBase
from aoslib.images import global_images
from shared.constants import MENU_FONT_COLOR
from aoslib.text import draw_text_with_alignment_and_size_validation, medium_edo_ui_font
from aoslib.scenes.gui.sliderControl import SliderControl
from aoslib.draw import draw_quad
from pyglet import gl
from shared.hud_constants import UI_CONTROL_SPACING, TEXT_BACKGROUND_SPACING, BLACK_COLOUR, UI_CONTROL_BAR_BUTTON_SPACING

class SettingsSliderControlListItem(SettingsListItemBase):

    def initialize(self, name, config_name, initial_value, on_value_changed_callback, min_value=0.0, max_value=1.0, decimal_places=2, has_edit_box=True):
        super(SettingsSliderControlListItem, self).initialize(name)
        self.config_name = config_name
        self.inital_value = initial_value
        self.callback = on_value_changed_callback
        self.control = SliderControl(initial_value, self.x1, self.y1, self.width, self.height, has_edit_box, min_value, max_value, decimal_places)
        self.control.add_handler(self.on_slider_value_changed)
        self.elements.append(self.control)

    def on_text(self, value):
        if not self.enabled:
            return
        for element in self.elements:
            element.on_text(value)

    def on_text_motion(self, value):
        if not self.enabled:
            return
        for element in self.elements:
            element.on_text_motion(value)

    def on_slider_value_changed(self, on_click):
        if self.callback is not None:
            self.callback(self.control.value)
        return

    def set_enabled(self, enabled):
        super(SettingsSliderControlListItem, self).set_enabled(enabled)
        if self.control is not None:
            self.control.set_enabled(enabled)
        return

    def get_current_value(self):
        return self.control.index

    def set_value(self, new_value):
        self.control.set(new_value)

    def reset(self):
        self.control.set(self.inital_value)

    def update_position(self, x, y, width, height, highlight_width):
        super(SettingsSliderControlListItem, self).update_position(x, y, width, height, highlight_width)
        x = self.x1 + TEXT_BACKGROUND_SPACING + self.name_width + TEXT_BACKGROUND_SPACING
        y = self.y1 + UI_CONTROL_SPACING
        height = self.height - UI_CONTROL_SPACING * 2
        width = self.width - TEXT_BACKGROUND_SPACING * 3 - self.name_width
        self.control.update_position(x, y, width, height)
