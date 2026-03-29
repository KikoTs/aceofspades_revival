from aoslib.scenes.main.settingsListItemBase import SettingsListItemBase
from aoslib.images import global_images
from shared.constants import MENU_FONT_COLOR
from aoslib.text import draw_text_with_alignment_and_size_validation, medium_edo_ui_font
from aoslib.scenes.gui.toggleOptionControl import ToggleOptionControl
from pyglet import gl
from shared.hud_constants import UI_CONTROL_SPACING, TEXT_BACKGROUND_SPACING

class SettingsToggleListItem(SettingsListItemBase):

    def initialize(self, name, id, initial_value, on_value_changed_callback):
        super(SettingsToggleListItem, self).initialize(name)
        self.id = id
        self.initial_value = initial_value
        self.control = ToggleOptionControl(initial_value, self.x1, self.y1, self.width, self.height)
        self.control.add_handler(on_value_changed_callback, self.id)
        self.elements.append(self.control)

    def set_enabled(self, enabled):
        super(SettingsToggleListItem, self).set_enabled(enabled)
        if self.control is not None:
            self.control.enabled = enabled
        return

    def get_current_value(self):
        return self.control.index

    def set_value(self, value):
        self.initial_value = value
        self.control.set(self.initial_value)

    def reset(self):
        self.control.set(self.initial_value)

    def update_position(self, x, y, width, height, highlight_width):
        super(SettingsToggleListItem, self).update_position(x, y, width, height, highlight_width)
        height = self.height - UI_CONTROL_SPACING * 2
        width = self.width - TEXT_BACKGROUND_SPACING * 3 - self.name_width
        x = self.x1 + TEXT_BACKGROUND_SPACING + self.name_width + TEXT_BACKGROUND_SPACING
        y = self.y1 + UI_CONTROL_SPACING
        self.control.update_position(x, y, width, height)
