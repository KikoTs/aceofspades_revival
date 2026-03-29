from aoslib.scenes.main.settingsListItemBase import SettingsListItemBase
from aoslib.images import global_images
from shared.constants import MENU_FONT_COLOR
from aoslib.text import draw_text_with_alignment_and_size_validation, medium_edo_ui_font
from aoslib.scenes.gui.dropBoxControl import DropBoxControl
from pyglet import gl
from shared.hud_constants import UI_CONTROL_SPACING, TEXT_BACKGROUND_SPACING

class SettingsDropdownListItem(SettingsListItemBase):

    def initialize(self, name, config_name, drop_box_options, manager, initial_option_index=0, on_option_changed_callback=None):
        super(SettingsDropdownListItem, self).initialize(name)
        self.id = config_name
        self.on_option_changed_callback = on_option_changed_callback
        if drop_box_options is None:
            drop_box_options = []
        self.control = DropBoxControl(manager, drop_box_options, initial_option_index, 0, 0, 100, 20, 10)
        self.control.add_handler(self.on_drop_box_option_changed)
        self.control.list_panel.draw_background = False
        self.elements.append(self.control)
        return

    def on_drop_box_option_changed(self, index):
        if self.on_option_changed_callback:
            self.on_option_changed_callback(index, str(index), self.id)

    def set_enabled(self, enabled):
        super(SettingsDropdownListItem, self).set_enabled(enabled)
        self.control.set_enabled(enabled)

    def get_current_value(self):
        return self.control.list_panel.current_row_index

    def get_current_value_as_text(self):
        row = self.control.list_panel.get_selected_item()
        if row is None:
            return ''
        else:
            return row.name

    def set_value(self, index):
        self.initial_index = index
        self.control.set_index(self.initial_index)

    def reset(self):
        self.control.set(self.initial_index)

    def on_mouse_motion(self, x, y, dx, dy):
        pass

    def on_mouse_release(self, x, y, button, modifiers):
        pass

    def draw_elements(self):
        pass

    def update_position(self, x, y, width, height, highlight_width):
        super(SettingsDropdownListItem, self).update_position(x, y, width, height, highlight_width)
        height = self.height - UI_CONTROL_SPACING * 2
        width = self.width - TEXT_BACKGROUND_SPACING * 3 - self.name_width
        x = self.x1 + TEXT_BACKGROUND_SPACING + self.name_width + TEXT_BACKGROUND_SPACING
        y = self.y1 + UI_CONTROL_SPACING
        self.control.update_position(x, y, width, height)
