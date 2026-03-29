from aoslib.scenes.main.settingsListItemBase import SettingsListItemBase
from aoslib.images import global_images
from shared.constants import MENU_FONT_COLOR
from aoslib.text import draw_text_with_alignment_and_size_validation, small_edo_ui_font, medium_edo_ui_font
from aoslib.gui import KeyControl
from pyglet import gl
from aoslib import strings
from aoslib.draw import draw_quad
from shared.hud_constants import UI_CONTROL_SPACING, TEXT_BACKGROUND_SPACING, KEY_CONTROL_BACKGROUND_COLOUR, UI_CONTROL_BAR_BUTTON_SPACING, MINIMUM_HEIGHT_FOR_MEDIUM_FONT

class SettingsKeyControlListItem(SettingsListItemBase):

    def initialize(self, name, config_name, initial_value, value_text, on_value_changed_callback, has_key_control=True):
        super(SettingsKeyControlListItem, self).initialize(name)
        self.config_name = config_name
        self.initial_value = initial_value
        self.key_background_x = self.x1
        self.key_background_width = self.width
        self.text = value_text
        self.text_x = self.x1
        self.text_y = self.y1
        self.text_width = self.width
        self.text_height = self.height
        self.on_value_changed_callback = on_value_changed_callback
        self.has_key_control = has_key_control
        if has_key_control:
            self.control = KeyControl(initial_value, value_text, self.x1, self.y1, self.width, self.height)
            self.control.add_handler(self.on_key_value_changed)
            self.elements.append(self.control)
        else:
            self.control = None
        return

    def get_key_text(self):
        if self.control is None:
            return
        else:
            text = self.control.text if self.control.text is not None else None
            return text

    def on_key_value_changed(self):
        if self.on_value_changed_callback is not None:
            self.on_value_changed_callback(self, self.config_name, self.control.value)
        return

    def draw_background(self, colour):
        super(SettingsKeyControlListItem, self).draw_background(colour)
        if self.control is not None:
            draw_quad(self.key_background_x, self.y1 + UI_CONTROL_SPACING, self.key_background_width, self.height - UI_CONTROL_SPACING * 2, KEY_CONTROL_BACKGROUND_COLOUR)
        return

    def draw_name(self):
        super(SettingsKeyControlListItem, self).draw_name()
        if self.text is not None and self.control is None:
            font = small_edo_ui_font
            draw_text_with_alignment_and_size_validation(self.text, self.text_x, self.text_y, self.text_width, self.text_height, MENU_FONT_COLOR, font, alignment_x='center', alignment_y='center')
        return

    def on_key_press(self, symbol, modifiers):
        if not self.enabled:
            return
        else:
            if self.control is not None:
                self.control.on_key_press(symbol, modifiers)
            return

    def set_enabled(self, enabled):
        super(SettingsKeyControlListItem, self).set_enabled(enabled)
        if self.control is not None:
            self.control.enabled = enabled
        return

    def get_current_value(self):
        return self.control.index

    def set_value(self, value):
        self.initial_value = value
        if self.control is not None:
            self.control.set(self.initial_value)
        return

    def reset(self):
        self.control.set(self.initial_value)

    def update_position(self, x, y, width, height, highlight_width):
        super(SettingsKeyControlListItem, self).update_position(x, y, width, height, highlight_width)
        self.key_background_x = self.x1 + TEXT_BACKGROUND_SPACING + self.name_width + TEXT_BACKGROUND_SPACING
        self.key_background_width = self.width - TEXT_BACKGROUND_SPACING * 3 - self.name_width
        self.text_x = self.key_background_x + UI_CONTROL_SPACING
        self.text_y = self.y1 + UI_CONTROL_SPACING + UI_CONTROL_BAR_BUTTON_SPACING
        self.text_width = self.key_background_width - UI_CONTROL_SPACING * 2
        self.text_height = self.height - UI_CONTROL_SPACING * 2 - UI_CONTROL_BAR_BUTTON_SPACING * 2
        if self.control is not None:
            self.control.update_position(self.text_x, self.text_y, self.text_width, self.text_height)
        return
