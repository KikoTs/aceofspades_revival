from aoslib.scenes.main.settingsListItemBase import SettingsListItemBase
from aoslib.images import global_images
from shared.constants import MENU_FONT_COLOR
from aoslib.text import draw_text_with_alignment_and_size_validation, medium_edo_ui_font
from aoslib.gui import SliderOption
from pyglet import gl
from shared.hud_constants import UI_CONTROL_SPACING, TEXT_BACKGROUND_SPACING

class SettingsSliderListItem(SettingsListItemBase):

    def initialize(self, name, id, items, initial_index, on_value_changed_callback, media):
        super(SettingsSliderListItem, self).initialize(name)
        self.id = id
        self.initial_index = initial_index if initial_index >= 0 else 0
        self.control = SliderOption(self.initial_index, items, self.x1, self.y1, self.width, self.height, media=media)
        self.control.add_handler(on_value_changed_callback, self.id)
        self.elements.append(self.control)

    def set_enabled(self, enabled):
        super(SettingsSliderListItem, self).set_enabled(enabled)
        if self.control is not None:
            self.control.set_enabled(enabled)
        return

    def get_current_value(self):
        return self.control.index

    def set_value(self, index):
        self.initial_index = index
        self.control.set(self.initial_index)

    def reset(self):
        self.control.set(self.initial_index)

    def update_position(self, x, y, width, height, highlight_width):
        super(SettingsSliderListItem, self).update_position(x, y, width, height, highlight_width)
        height = self.height - UI_CONTROL_SPACING * 2
        width = self.width - TEXT_BACKGROUND_SPACING * 3 - self.name_width
        x = self.x1 + TEXT_BACKGROUND_SPACING + self.name_width + TEXT_BACKGROUND_SPACING
        y = self.y1 + UI_CONTROL_SPACING
        self.control.update_position(x, y, width, height)
