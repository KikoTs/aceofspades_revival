from aoslib.scenes.main.gameRulesListItemBase import GameRulesListItemBase
from aoslib.images import global_images
from shared.constants import MENU_FONT_COLOR
from aoslib.text import draw_text_with_size_validation, medium_standard_ui_font
from aoslib.gui import SliderOption
from aoslib import strings
from pyglet import gl
from shared.steam import SteamSetLobbyData, SteamGetLobbyData
from shared.constants_matchmaking import *
from shared.hud_constants import TEXT_BACKGROUND_SPACING

class GameRulesSliderListItem(GameRulesListItemBase):

    def initialize(self, rule_type, rule_id, lobby_id, rule_values, on_rule_value_changed, media):
        super(GameRulesSliderListItem, self).initialize(rule_id, lobby_id, on_rule_value_changed, media, rule_type)
        self.spacing = self.width / 30.0
        self.center_text = False
        if self.current_value == '' or self.current_value == None:
            self.set_default_value()
        initial_index = -1
        for index, rule_value in enumerate(rule_values):
            if rule_value == self.current_value:
                initial_index = index
                break

        self.control = SliderOption(initial_index, rule_values, self.x1, self.y1, self.width, self.height, background_colour=(43,
                                                                                                                              37,
                                                                                                                              3,
                                                                                                                              255), media=self.media)
        self.control.add_handler(self.on_value_changed, self.rule_id)
        self.elements.append(self.control)
        return

    def get_item_index(self, items, value):
        for index, item in enumerate(items):
            if item == value:
                return index

        return 0

    def on_value_changed(self, index, value, rule_id):
        self.current_value = value
        if self.on_value_changed_callback is not None:
            self.on_value_changed_callback(self.rule_type, self.rule_id, self.current_value, self.get_default_value())
        return

    def reset(self):
        self.set_default_value()
        index = self.control.get_index_by_name(self.current_value)
        self.control.set(index)

    def update_position(self, x, y, width, height, highlight_width):
        super(GameRulesSliderListItem, self).update_position(x, y, width, height, highlight_width)
        self.spacing = self.width / 30.0
        self.name_width = text_width = self.width / 3.0 * 2.0 - self.spacing * 2.0
        control_width = self.width - self.name_width - self.spacing
        spacing_y = self.height / 5.0
        height = self.height - spacing_y
        x = self.x1 + self.name_width + self.height / 10.0 - TEXT_BACKGROUND_SPACING / 2
        y = self.y1 + spacing_y / 2.0
        self.control.button_size = height
        self.control.update_position(x, y, control_width, height)

    def draw_name(self):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        if self.control.enabled == False:
            colour = (
             self.background_colour[0] + 20, self.background_colour[1] + 20, self.background_colour[2] + 20, self.background_colour[3])
        else:
            colour = MENU_FONT_COLOR
        width = self.width - self.control.width - TEXT_BACKGROUND_SPACING * 3
        x = self.x1 + TEXT_BACKGROUND_SPACING
        y = self.get_text_y_position()
        draw_text_with_size_validation(self.name, x, y, width, self.height, colour, self.font, False)
        for element in self.elements:
            element.draw()
