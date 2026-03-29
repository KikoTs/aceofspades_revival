from aoslib.scenes.frontend.listPreviewMenuBase import ListPreviewMenuBase
from aoslib.scenes.frontend.lobbyPanelBase import LobbyPanelBase
from aoslib.scenes.main.categoryListItem import CategoryListItem
from aoslib.scenes.frontend.previewPanelBase import PreviewPanelBase
from aoslib.scenes.frontend.expandableListPanel import ExpandableListPanel
from aoslib.scenes.frontend.panelBase import BACKGROUND_NONE
from aoslib.scenes.main.gameRulesToggleListItem import GameRulesToggleListItem
from aoslib.scenes.main.gameRulesSliderListItem import GameRulesSliderListItem
from aoslib.scenes.main.matchSettings import get_string_as_list, get_playlist_with_id
from aoslib import strings
from aoslib.gui import SliderOption
from shared.constants_matchmaking import A2667, A2688, A2680, A2712
from shared.constants_gamemode import A2448
from shared.steam import SteamGetLobbyData, SteamSetLobbyData, SteamAmITheLobbyOwner
from playlists import get_default_rule_value_for_current_lobby
from shared.hud_constants import ROW_GREY_COLOUR, ROW_DARK_GREY_COLOUR, LIST_PANEL_SPACING
import playlists
from shared.constants import CLASS_MINER, CLASS_SOLDIER, CLASS_SCOUT, CLASS_ENGINEER, CLASS_GANGSTER_1, CLASS_CLASSIC_SOLDIER, DEFAULT_TEAM_CLASSES, CLASS_SPECIALIST, CLASS_MEDIC

class GameRulesPanel(LobbyPanelBase):

    def initialize(self):
        super(GameRulesPanel, self).initialize()
        self.expandable_list_panel = ExpandableListPanel(self.manager)
        self.last_scroll_index = None
        self.last_filter_index = None
        self.filter_slider = None
        return

    def initialise_ui(self, lobby_id, x, y, width, height):
        super(GameRulesPanel, self).initialise_ui(lobby_id, x, y, width, height)
        self.modified_rules = {}
        self.selected_filter_key = None
        default_panel_height = 30
        pad = 5
        panel_height = self.height - default_panel_height - pad
        self.expandable_list_panel.initialise_ui(strings.RULES, x, y, width, height, has_header=True)
        self.expandable_list_panel.center_header_text = True
        self.expandable_list_panel.add_on_item_selected_handler(self.on_row_selected, 0)
        self.elements.append(self.expandable_list_panel)
        x = self.x + LIST_PANEL_SPACING
        y -= panel_height + default_panel_height
        self.add_default_panel(x, y, width - LIST_PANEL_SPACING * 2, default_panel_height)
        self.add_default_button(self.on_defaults_button_clicked, x, y, button_height=default_panel_height)
        self.__initialise()
        return

    def __initialise(self):
        self.populate_playlist()
        self.expandable_list_panel.scrollbar.set_scroll(0)

    def set_content_visibility(self, visible):
        super(GameRulesPanel, self).set_content_visibility(visible)
        if not SteamAmITheLobbyOwner():
            return
        else:
            if visible:
                self.__initialise()
            elif self.filter_slider is not None:
                self.last_filter_index = self.filter_slider.index
            if self.default_button is not None:
                self.default_button.set_enabled(visible)
                self.default_button.set_visible(visible)
            return

    def on_defaults_button_clicked(self):
        for row in self.expandable_list_panel.rows:
            if type(row) is CategoryListItem:
                continue
            row.reset()

        self.reset_modified_rules()

    def get_selected_filter_rules(self):
        if self.selected_filter_key is None or self.selected_filter_key not in A2667.keys():
            self.set_selected_filter_key()
        return A2667[self.selected_filter_key]

    def set_selected_filter_key(self):
        if self.filter_slider.index == -1:
            self.selected_filter_key = 'GENERAL'
        for key, rules in A2667.iteritems():
            if key in A2448.keys():
                text = strings.get_by_id(A2448[key])
            else:
                text = strings.get_by_id(key)
            if text == self.filter_slider.options[self.filter_slider.index]:
                self.selected_filter_key = key
                return

        self.selected_filter_key = 'GENERAL'

    def reset_modified_rules(self):
        for category, data in self.modified_rules.iteritems():
            self.reset_modified_rule_type(category)

    def reset_modified_rule_type(self, rule_type):
        data = self.modified_rules[rule_type]
        for rule_id, value in data.iteritems():
            default_value = get_default_rule_value_for_current_lobby(rule_id)
            if default_value == A2688[rule_id]['default']:
                SteamSetLobbyData(rule_id, '')
            else:
                SteamSetLobbyData(rule_id, default_value)

    def check_rule_availability(self, rule_id):
        rule = A2688[rule_id]
        enabled = available = True
        if rule_id in A2712:
            class_id = A2712[rule_id]
            if class_id not in self.available_classes:
                available = False
        elif 'classes' in rule:
            enabled = available = False
            valid_classes = rule['classes']
            for test_class in valid_classes:
                if test_class in self.available_classes:
                    available = True
                if test_class in self.enabled_classes:
                    enabled = True

        return (
         available, enabled)

    def on_rule_value_changed(self, rule_type, rule_id, rule_value, default_rule_value):
        if default_rule_value == rule_value:
            if rule_type in self.modified_rules.keys():
                if rule_id in self.modified_rules[rule_type]:
                    self.modified_rules[rule_type][rule_id] = None
            if default_rule_value == A2688[rule_id]['default']:
                SteamSetLobbyData(rule_id, '')
            else:
                SteamSetLobbyData(rule_id, default_rule_value)
        else:
            SteamSetLobbyData(rule_id, rule_value)
            if rule_type in self.modified_rules.keys():
                self.modified_rules[rule_type][rule_id] = rule_value
        if rule_id in A2712:
            class_id = A2712[rule_id]
            if class_id in self.available_classes:
                if rule_value == '':
                    rule_value = A2688[rule_id]['default']
                if rule_value == 'ON':
                    if class_id not in self.enabled_classes:
                        self.enabled_classes.append(class_id)
                elif rule_value == 'OFF':
                    if class_id in self.enabled_classes:
                        self.enabled_classes.remove(class_id)
            for row in self.expandable_list_panel.rows:
                if type(row) is CategoryListItem:
                    continue
                available, enabled = self.check_rule_availability(row.rule_id)
                row.set_disabled(not enabled)

        return

    def populate_playlist(self):
        self.expandable_list_panel.reset_list()
        self.modified_rules = {}
        playlist = None
        try:
            playlist_id = int(SteamGetLobbyData(self.lobby_id, 'PlaylistID'))
            playlist = get_playlist_with_id(playlist_id)
        except:
            pass

        if playlist is None:
            return
        else:
            if playlist.classic:
                self.available_classes = self.enabled_classes = [
                 CLASS_CLASSIC_SOLDIER]
            elif playlist.mafia:
                self.available_classes = self.enabled_classes = [
                 CLASS_GANGSTER_1]
            else:
                self.available_classes = DEFAULT_TEAM_CLASSES
                self.enabled_classes = []
                for class_rule in ['RULE_ENABLE_CLASS_COMMANDO', 'RULE_ENABLE_CLASS_MARKSMAN', 
                     'RULE_ENABLE_CLASS_MINER', 'RULE_ENABLE_CLASS_ENGINEER', 
                     'RULE_ENABLE_CLASS_SPECIALIST', 'RULE_ENABLE_CLASS_MEDIC']:
                    class_id = A2712[class_rule]
                    current_value = SteamGetLobbyData(self.lobby_id, class_rule)
                    if current_value == '':
                        current_value = A2688[class_rule]['default']
                    if current_value == 'ON':
                        self.enabled_classes.append(class_id)

            game_modes_string = SteamGetLobbyData(self.lobby_id, 'PLAYLIST')
            game_modes = get_string_as_list(game_modes_string)
            standard_rule_headers = {'GENERAL': 1, 'CLASSES': 2, 'WEAPONS': 3, 'EQUIPMENT': 4}
            for rule_type in A2667.keys():
                category_text = ''
                if rule_type in standard_rule_headers:
                    category_text = strings.get_by_id(rule_type)
                    use_order = standard_rule_headers[rule_type]
                elif rule_type in game_modes and rule_type in A2448.keys():
                    category_text = strings.get_by_id(A2448[rule_type])
                    use_order = 0
                else:
                    continue
                categoryItem = CategoryListItem(category_text, is_expandable=True, sub_row_colours=[ROW_GREY_COLOUR, ROW_DARK_GREY_COLOUR], sort_order=use_order)
                categoryItem.center_text = False
                rule_rows = []
                rule_ids = {}
                for rule_id in A2667[rule_type]:
                    available, enabled = self.check_rule_availability(rule_id)
                    if not available:
                        continue
                    rule = A2688[rule_id]
                    if rule['values'] == A2680:
                        rule_row = GameRulesToggleListItem(rule_type, rule_id, self.lobby_id, self.on_rule_value_changed, self.manager.media)
                    else:
                        rule_values = rule['values']
                        sorted_friendly_values = sorted(rule_values, key=rule_values.get)
                        rule_row = GameRulesSliderListItem(rule_type, rule_id, self.lobby_id, sorted_friendly_values, self.on_rule_value_changed, self.manager.media)
                    rule_row.set_disabled(not enabled)
                    rule_rows.append(rule_row)
                    rule_ids[rule_id] = None

                if len(rule_rows) > 0:
                    self.expandable_list_panel.add_list_item(categoryItem, rule_rows)
                    self.modified_rules[rule_type] = rule_ids

            self.expandable_list_panel.on_scroll(0, silent=True)
            return

    def on_row_selected(self, index, row):
        pass

    def draw(self):
        super(GameRulesPanel, self).draw()
