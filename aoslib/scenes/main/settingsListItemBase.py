from aoslib.scenes.main.listPanelItemBase import ListPanelItemBase
from aoslib.images import global_images
from shared.constants import MENU_FONT_COLOR
from aoslib.text import draw_text_with_alignment_and_size_validation, medium_edo_ui_font
from pyglet import gl
from shared.hud_constants import TEXT_BACKGROUND_SPACING

class SettingsListItemBase(ListPanelItemBase):

    def initialize(self, name):
        super(SettingsListItemBase, self).initialize()
        self.name = name
        self.name_width = 0
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.silent_control = True

    def get_current_value(self):
        return

    def on_value_changed(self):
        pass

    def draw_selection_highlight(self):
        pass

    def draw_hovered_highlight(self):
        pass

    def set_enabled(self, enabled):
        self.enabled = enabled

    def draw_background(self, colour):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        gl.glPushMatrix()
        gl.glTranslatef(self.x1 + self.width / 2, self.y1 + self.height / 2, 0)
        gl.glScalef(self.scale_x, self.scale_y, 0.0)
        if self.enabled:
            global_images.settings_matchsettings_frame.blit(0, 0)
        else:
            global_images.settings_frame_disabled.blit(0, 0)
        gl.glPopMatrix()

    def reset(self):
        pass

    def set_value(self):
        pass

    def update_position(self, x, y, width, height, highlight_width):
        super(SettingsListItemBase, self).update_position(x, y, width, height, highlight_width)
        self.name_width = self.width / 3
        self.scale_x = float(self.width) / float(global_images.settings_matchsettings_frame.width)
        self.scale_y = float(self.height) / float(global_images.settings_matchsettings_frame.height)

    def draw_name(self):
        if self.name is not None and self.name_width > 0:
            draw_text_with_alignment_and_size_validation(self.name, self.x1 + TEXT_BACKGROUND_SPACING, self.y1, self.name_width, self.height, MENU_FONT_COLOR, medium_edo_ui_font, alignment_x='center', alignment_y='center')
        return
