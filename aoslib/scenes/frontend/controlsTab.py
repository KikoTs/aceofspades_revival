from tabBase import TabBase
from aoslib.scenes.frontend.panelBase import BACKGROUND_NONE
from aoslib.scenes.frontend.expandableListPanel import ExpandableListPanel
from aoslib.scenes.main.categoryListItem import CategoryListItem
from aoslib.scenes.main.settingsKeyControlListItem import SettingsKeyControlListItem
from aoslib.scenes.main.settingsSliderControlListItem import SettingsSliderControlListItem
from shared.constants import MENU_FONT_COLOR, ERROR_CONTROL_ALREADY_BOUND
from aoslib.text import settings_description_font
from aoslib.gui import KeyControl, VerticalScrollBar, translate_key
from aoslib.images import global_images
from aoslib import strings
from aoslib.media import HUD_AUDIO_ZONE
from pyglet.window import key
from aoslib.config import DEFAULTS
from shared.hud_constants import CATEGORY_ROW_HEIGHT, SETTINGS_ROW_HEIGHT, SETTINGS_ROW_SPACING, ROW_GREY_COLOUR, ROW_DARK_GREY_COLOUR

class ControlsTab(TabBase):
    content_frame = global_images.controls_frame

    def initialize(self):
        cfg = self.config
        self.x = 152
        self.y = 467
        self.width = 494
        self.height = 293
        self.in_game_tab = False
        self.current_rows = 0
        self.visible_items = 7
        self.min_index = 0
        self.max_index = self.visible_items - 1
        self.elements = []
        self.items_per_row = 1
        self.height_factor = 34
        self.controls_enabled = True
        self.list_panel = ExpandableListPanel(self.manager)
        self.list_panel.initialise_ui('', self.x, self.y, self.width, self.height)
        self.list_panel.set_row_height(CATEGORY_ROW_HEIGHT, SETTINGS_ROW_HEIGHT)
        self.list_panel.set_background(BACKGROUND_NONE)
        self.list_panel.line_spacing = SETTINGS_ROW_SPACING
        self.elements.append(self.list_panel)
        keys_info = {(strings.MAIN_GAME_CONTROLS): [{'name': (strings.FORWARD), 'id': 'forward', 'key_text': None}, {'name': (strings.BACKWARD), 'id': 'backward', 'key_text': None}, {'name': (strings.LEFT), 'id': 'left', 'key_text': None}, {'name': (strings.RIGHT), 'id': 'right', 'key_text': None}, {'name': (strings.SNEAK), 'id': 'sneak', 'key_text': None}, {'name': (strings.CROUCH), 'id': 'crouch', 'key_text': None}, {'name': (strings.SPRINT), 'id': 'sprint', 'key_text': None}, {'name': (strings.JUMP), 'id': 'jump', 'key_text': None}, {'name': (strings.FIRE_USE), 'id': 'use_command2', 'key_text': (strings.LMB)}, {'name': (strings.AIM), 'id': 'aim', 'key_text': (strings.RMB)}, {'name': (strings.RELOAD), 'id': 'reload', 'key_text': None}, {'name': (strings.CYCLE_NEXT_WEAPON), 'id': 'use_command2', 'key_text': (strings.MOUSE_WHEEL)}, {'name': (strings.INVENTORY_SLOTS), 'id': 'use_command2', 'key_text': '1-9'}, {'name': (strings.TEAM_CHAT), 'id': 'team_chat', 'key_text': None}, {'name': (strings.GLOBAL_CHAT), 'id': 'global_chat', 'key_text': None}, {'name': (strings.VIEW_MAP), 'id': 'show_map', 'key_text': None}, {'name': (strings.VIEW_SCORES), 'id': 'view_scores', 'key_text': None}, {'name': (strings.CHANGE_TEAM), 'id': 'change_team', 'key_text': None}, {'name': (strings.CHANGE_CLASS), 'id': 'change_class', 'key_text': None}, {'name': (strings.IN_GAME_MENU), 'id': 'menu', 'key_text': None}, {'name': (strings.PICK_COLOUR), 'id': 'weapon_custom', 'key_text': None}, {'name': (strings.MAP_VOTE_1), 'id': 'map_vote_1', 'key_text': None}, {'name': (strings.MAP_VOTE_2), 'id': 'map_vote_2', 'key_text': None}, {'name': (strings.MAP_VOTE_3), 'id': 'map_vote_3', 'key_text': None}, {'name': (strings.KICK_PLAYER), 'id': 'kick_player', 'key_text': None}, {'name': (strings.TOGGLE_HUD), 'id': 'toggle_hud', 'key_text': None}], (strings.UGC_CONTROLS): [{'name': (strings.UGC_GAME_SETTINGS_KEY), 'id': 'ugc_settings', 'key_text': None}, {'name': (strings.TOOL_HELP), 'id': 'tool_help', 'key_text': None}, {'name': (strings.PALETTE_LEFT), 'id': 'palette_left', 'key_text': None}, {'name': (strings.PALETTE_RIGHT), 'id': 'palette_right', 'key_text': None}, {'name': (strings.PALETTE_UP), 'id': 'palette_up', 'key_text': None}, {'name': (strings.PALETTE_DOWN), 'id': 'palette_down', 'key_text': None}, {'name': (strings.CANCEL_PREFAB_PLACEMENT), 'id': 'cancel_prefab_placement', 'key_text': None}, {'name': (strings.CARVE_PREFAB), 'id': 'carve_prefab', 'key_text': None}, {'name': (strings.HOVER_INPUT), 'id': 'hover', 'key_text': None}, {'name': (strings.SAVE), 'id': 'quick_save', 'key_text': None}]}
        self.populate_list(keys_info)
        return

    def key_has_focus(self):
        for row in self.list_panel.rows:
            if type(row) is SettingsKeyControlListItem and row.has_key_control:
                if row.control.focus:
                    return True

        return False

    def populate_list(self, keys_info):
        cfg = self.config
        self.list_panel.reset_list()
        sort_order = 0
        for category, keys in keys_info.iteritems():
            categoryItem = CategoryListItem(category, is_expandable=True, sub_row_colours=[ROW_GREY_COLOUR, ROW_DARK_GREY_COLOUR], sort_order=sort_order)
            sort_order += 1
            rows = []
            if category == strings.MAIN_GAME_CONTROLS:
                row = SettingsSliderControlListItem(strings.MOUSE_SENSITIVITY, 'mouse_sensitivity', self.config.mouse_sensitivity, self.on_slider_change)
                rows.append(row)
            for item in keys:
                enabled = item['key_text'] is None or item['key_text'] is not None and item['id'] != 'use_command2'
                value = getattr(self.config, item['id']) if enabled else None
                row = SettingsKeyControlListItem(item['name'], item['id'], value, item['key_text'], self.on_change, item['id'] != 'use_command2')
                rows.append(row)

            self.list_panel.add_list_item(categoryItem, rows)

        self.list_panel.on_scroll(0, silent=True)
        return

    def on_slider_change(self, value, set_on_click=True):
        if set_on_click:
            self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
        value = round(value, 2)
        self.config.set('mouse_sensitivity', value)

    def on_change(self, modified_row, config_name, value):
        self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
        for row in self.list_panel.rows:
            if type(row) is not SettingsKeyControlListItem:
                continue
            if row.config_name == config_name:
                continue
            if row.name == strings.INVENTORY_SLOTS:
                if value in xrange(key._0, key._9 + 1):
                    self.manager.set_big_text_message(ERROR_CONTROL_ALREADY_BOUND, disconnected=False, format_vars=(translate_key(value), strings.INVENTORY_SLOTS))
                    modified_row.set_value(getattr(self.config, config_name))
                    return
            if getattr(self.config, row.config_name) == value:
                self.manager.set_big_text_message(ERROR_CONTROL_ALREADY_BOUND, disconnected=False, format_vars=(row.get_key_text(), row.name))
                modified_row.set_value(getattr(self.config, config_name))
                return

        self.config.set(config_name, value)

    def restore_values(self):
        self.config.restore()
        if self.config.old_config is None:
            return
        else:
            for category_row, rows in self.list_panel.category_row_map.iteritems():
                for row in rows:
                    if row.config_name in self.config.old_config:
                        row.set_value(self.config.old_config[row.config_name])

            return

    def on_defaults_pressed(self):
        defaults = DEFAULTS.get('Controls')
        if defaults is None:
            return
        else:
            for category_row, rows in self.list_panel.category_row_map.iteritems():
                for row in rows:
                    if row.config_name in defaults:
                        row.set_value(defaults[row.config_name])

            return

    def update_display(self):
        pass

    def draw(self):
        for element in self.elements:
            element.draw()
