from aoslib.scenes.main.gameRulesListItemBase import GameRulesListItemBase
from shared.constants import MENU_FONT_COLOR, MENU_FONT_DISABLED_COLOR
from aoslib.text import draw_text_with_size_validation
from aoslib.scenes.gui.checkboxControl import CheckboxControl
from aoslib import strings
from pyglet import gl
from shared.steam import SteamSetLobbyData, SteamGetLobbyData
from shared.constants_matchmaking import *
from shared.hud_constants import TEXT_BACKGROUND_SPACING

class GameRulesToggleListItem(GameRulesListItemBase):

    def initialize(self, rule_type, rule_id, lobby_id, on_rule_value_changed, media):
        super(GameRulesToggleListItem, self).initialize(rule_id, lobby_id, on_rule_value_changed, media, rule_type)
        self.spacing = self.width / 30.0
        self.center_text = False
        if self.current_value == 'ON':
            is_selected = True
        else:
            is_selected = False
        self.checkbox = CheckboxControl(is_selected, self.x1, self.y1, self.height / 2.0)
        self.checkbox.add_handler(self.on_check_changed)
        self.elements.append(self.checkbox)

    def reset(self):
        self.set_default_value()
        if self.current_value == 'ON':
            self.checkbox.value = True
        else:
            self.checkbox.value = False

    def set_disabled(self, do_disable=True):
        self.disabled = do_disable
        self.checkbox.set_enabled(not do_disable)

    def on_check_changed(self):
        if self.checkbox.value == True:
            self.current_value = 'ON'
        else:
            self.current_value = 'OFF'
        if self.on_value_changed_callback is not None:
            self.on_value_changed_callback(self.rule_type, self.rule_id, self.current_value, self.get_default_value())
        return

    def update_position(self, x, y, width, height, highlight_width):
        super(GameRulesToggleListItem, self).update_position(x, y, width, height, highlight_width)
        self.spacing = self.width / 30.0
        self.checkbox.size = self.height / 3.0 * 2.0
        x = self.x1 + self.width - self.checkbox.size / 2 - TEXT_BACKGROUND_SPACING
        y = self.y1 + self.height / 2.0
        self.checkbox.update_position(x, y)

    def draw_name(self):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        if self.checkbox.enabled == False:
            colour = MENU_FONT_DISABLED_COLOR
        else:
            colour = MENU_FONT_COLOR
        width = self.width - (self.checkbox.size * 2.0 + 20)
        x = self.x1 + TEXT_BACKGROUND_SPACING
        y = self.get_text_y_position()
        draw_text_with_size_validation(self.name, x, y, width, self.height, colour, self.font, False)
        for element in self.elements:
            element.draw()
