from aoslib.scenes.frontend.listPanelBase import ListPanelBase
from aoslib.scenes.frontend.lobbyPanelBase import LobbyPanelBase
from aoslib.scenes.frontend.panelBase import BACKGROUND_NONE
from aoslib.scenes.main.matchSettingsListItem import MatchSettingsSliderListItem, MatchSettingsMenuListItem
from aoslib.scenes.main.matchSettingsEditTextListItem import MatchSettingsEditTextListItem
from aoslib.scenes.main.matchSettings import get_string_as_list, get_display_name, generate_ugc_map_filename_from_lobby, generate_ugc_map_filename
from shared.constants_matchmaking import *
from aoslib import strings
from aoslib.squadEventManager import *
from shared.steam import SteamGetLobbyData, SteamGetFriendPersonaName, SteamGetLobbyOwner, SteamSetLobbyAccessibility, SteamSetLobbyData, SteamAmITheLobbyOwner, SteamSetLobbyMaxPlayers, SteamSetRichPresenceLobby, SteamClearRichPresence
from shared.constants_prefabs import A3056, A3037
from shared.hud_constants import LIST_PANEL_SPACING, MATCH_SETTINGS_ROW_HEIGHT, MATCH_SETTINGS_ROW_SPACING
from aoslib.media import HUD_AUDIO_ZONE
from shared.constants_gamemode import A2448
PRIVACY_TYPES_LIST = [
 strings.INVITE, strings.FRIENDS, strings.OPEN]

class MatchSettingsPanel(LobbyPanelBase):

    def initialize(self):
        super(MatchSettingsPanel, self).initialize()
        self.list_panel = ListPanelBase(self.manager)
        self.last_scroll_index = None
        self.on_show_rules = None
        self.on_show_playlists = None
        self.on_show_map_rotation = None
        self.on_show_ugc_mode = None
        self.on_show_prefab_set = None
        self.on_save_map_name_modified = None
        self.on_cancel_game = None
        self.enable_privacy_type = True
        self.enable_match_length = True
        self.enable_game_rules = True
        self.enable_map_rotation = True
        self.enable_max_players = True
        self.enable_playlist = True
        self.enable_ugc_mode = False
        self.enable_save_map_name = False
        self.enable_prefab_set = False
        return

    def set_callbacks(self, on_show_rules, on_show_playlists, on_show_map_rotation, on_show_ugc_mode, on_cancel_game):
        self.on_show_rules = on_show_rules
        self.on_show_playlists = on_show_playlists
        self.on_show_map_rotation = on_show_map_rotation
        self.on_show_ugc_mode = on_show_ugc_mode
        self.on_cancel_game = on_cancel_game

    def set_title(self, title):
        self.list_panel.title = title
        self.list_panel.has_header = True

    def initialise_ui(self, lobby_id, x, y, width, height):
        super(MatchSettingsPanel, self).initialise_ui(lobby_id, x, y, width, height)
        default_panel_height = 30
        pad = 5
        panel_height = self.height - default_panel_height - pad
        self.list_panel.initialise_ui(self.title, x, y, width, panel_height, row_height=MATCH_SETTINGS_ROW_HEIGHT, has_header=True)
        self.list_panel.line_spacing = MATCH_SETTINGS_ROW_SPACING
        self.list_panel.center_header_text = True
        self.list_panel.set_background(BACKGROUND_NONE)
        self.list_panel.add_on_item_selected_handler(self.on_row_selected, 0)
        self.elements.append(self.list_panel)
        x = self.x + LIST_PANEL_SPACING
        y -= panel_height
        self.add_default_panel(x, y, width - LIST_PANEL_SPACING * 2, default_panel_height)
        self.add_default_button(self.on_defaults_button_clicked, x, y, button_height=default_panel_height)
        self.populate_match_settings_list()

    def set_content_visibility(self, visible):
        super(MatchSettingsPanel, self).set_content_visibility(visible)
        if self.visible:
            self.populate_match_settings_list()
        else:
            self.last_scroll_index = self.list_panel.scrollbar.scroll_pos
        if self.default_button is not None:
            self.default_button.set_enabled(visible)
            self.default_button.set_visible(visible)
        return

    def reset_to_defaults(self):
        if not SteamAmITheLobbyOwner():
            return
        else:
            map_title_row = None
            for row in self.list_panel.rows:
                if row.settings_id == 'MAP_TITLE':
                    map_title_row = row
                else:
                    row.reset()

            if map_title_row is not None:
                self.manager.hosted_ugc_map_filename = generate_ugc_map_filename_from_lobby(self.lobby_id)
                map_title_row.reset(SteamGetLobbyData(self.lobby_id, 'MAP_ROTATION_NEW_TITLE'))
            return

    def on_defaults_button_clicked(self):
        self.media.stop_sounds()
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        self.reset_to_defaults()
        self.cancel_game()

    def on_row_selected(self, index, row):
        if row is None:
            return
        else:
            return

    def open_edit_map_rotation_menu(self):
        self.cancel_game()
        if self.on_show_map_rotation is not None:
            self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
            self.on_show_map_rotation()
        return

    def open_edit_game_rules_menu(self):
        self.cancel_game()
        if self.on_show_rules is not None:
            self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
            self.on_show_rules()
        return

    def open_edit_playlist_menu(self):
        self.cancel_game()
        if self.on_show_playlists is not None:
            self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
            self.on_show_playlists()
        return

    def open_edit_ugc_mode_menu(self):
        self.cancel_game()
        if self.on_show_ugc_mode is not None:
            self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
            self.on_show_ugc_mode()
        return

    def open_prefab_set_menu(self):
        self.cancel_game()
        if self.on_show_prefab_set is not None:
            self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
            self.on_show_prefab_set()
        return

    def on_save_map_modified(self, name):
        if not SteamAmITheLobbyOwner():
            return
        else:
            self.cancel_game()
            SteamSetLobbyData('MAP_ROTATION_NEW_TITLE', name)
            if self.on_save_map_name_modified is not None:
                self.on_save_map_name_modified()
            return

    def add_playlist_row(self):
        default_playlist = SteamGetLobbyData(self.lobby_id, 'PLAYLIST')
        if default_playlist != '':
            default_text = get_display_name('PLAYLIST', self.lobby_id)
        else:
            default_text = strings.DEFAULT
        playlist = MatchSettingsMenuListItem(strings.MODE, 'PLAYLIST', self.lobby_id, self.open_edit_playlist_menu, default_text)
        self.list_panel.rows.append(playlist)

    def add_ugc_mode_row(self):
        game_mode = SteamGetLobbyData(self.lobby_id, 'UGC_MODES')
        if game_mode in A2448:
            if game_mode == 'ctf':
                default_text = strings.CTF_AND_CLASSIC_CTF
            else:
                default_text = strings.get_by_id(A2448[game_mode])
        else:
            default_text = strings.DEFAULT
        playlist_row = MatchSettingsMenuListItem(strings.MODE, 'UGC_MODES', self.lobby_id, self.open_edit_ugc_mode_menu, default_text)
        self.list_panel.rows.append(playlist_row)

    def add_map_rotation_row(self):
        default_text = map_rotation_string = SteamGetLobbyData(self.lobby_id, 'MAP_ROTATION_ORIGINAL_TITLE')
        if default_text == 'Untitled UGC':
            default_text = SteamGetLobbyData(self.lobby_id, 'MAP_ROTATION_FILENAME')
        if default_text == '':
            default_text = strings.DesertBaseplate
            SteamSetLobbyData('MAP_ROTATION_ORIGINAL_TITLE', default_text)
            SteamSetLobbyData('MAP_ROTATION_FILENAME', 'DesertBaseplate')
        map_rotation = MatchSettingsMenuListItem(strings.MAP, 'MAP_ROTATION_FILENAME', self.lobby_id, self.open_edit_map_rotation_menu, default_text)
        self.list_panel.rows.append(map_rotation)

    def on_match_type_value_changed(self, new_value):
        self.populate_match_settings_list()

    def on_privacy_changed(self, value):
        self.cancel_game()
        if value == str(A2714):
            SteamSetLobbyAccessibility(A2714)
        elif value == str(A2713):
            SteamSetLobbyAccessibility(A2713)
        elif value == str(A2715):
            SteamSetLobbyAccessibility(A2715)

    def on_max_players_changed(self, value):
        self.cancel_game()
        SteamSetLobbyMaxPlayers(self.lobby_id, int(value))

    def on_match_length_changed(self, value):
        self.cancel_game()

    def cancel_game(self):
        self.on_cancel_game(silent=True, only_if_started=True)

    def populate_match_settings_list(self):
        self.list_panel.rows = []
        if self.enable_privacy_type:
            privacy_type = MatchSettingsSliderListItem(strings.PRIVACY, 'PRIVACY', self.lobby_id, PRIVACY_TYPES_LIST, self.on_privacy_changed, media=self.manager.media, set_as_index=True)
            self.list_panel.rows.append(privacy_type)
        if self.enable_playlist:
            self.add_playlist_row()
        if self.enable_max_players:
            max_players = MatchSettingsSliderListItem(strings.MAX_PLAYERS, 'MAX_PLAYERS', self.lobby_id, A2668, on_value_changed_callback=self.on_max_players_changed, media=self.manager.media)
            self.list_panel.rows.append(max_players)
        if self.enable_match_length:
            match_length = MatchSettingsSliderListItem(strings.MATCH_LENGTH, 'MATCH_LENGTH', self.lobby_id, A2669, on_value_changed_callback=self.on_match_length_changed, media=self.manager.media)
            self.list_panel.rows.append(match_length)
        if self.enable_map_rotation:
            self.add_map_rotation_row()
        if self.enable_game_rules:
            default_text = get_display_name('GAME_RULES', self.lobby_id)
            rules = MatchSettingsMenuListItem(strings.GAME_RULES, 'GAME_RULES', self.lobby_id, self.open_edit_game_rules_menu, default_text)
            self.list_panel.rows.append(rules)
        if self.enable_prefab_set:
            default_text = self.get_prefab_set_name()
            prefab_set = MatchSettingsMenuListItem(strings.PREFAB_SET, 'PREFAB_SET', self.lobby_id, self.open_prefab_set_menu, default_text)
            self.list_panel.rows.append(prefab_set)
        if self.enable_ugc_mode:
            self.add_ugc_mode_row()
        if self.enable_save_map_name:
            if self.manager.hosted_ugc_map_filename == '':
                self.manager.hosted_ugc_map_filename = generate_ugc_map_filename_from_lobby(self.lobby_id)
            map_name = SteamGetLobbyData(self.lobby_id, 'MAP_ROTATION_NEW_TITLE')
            save_map_name_item = MatchSettingsEditTextListItem(map_name, strings.UGC_MAP_TITLE, 'MAP_TITLE', self.lobby_id, self.on_save_map_modified, self.manager.game_scene.profanity_manager)
            self.list_panel.rows.append(save_map_name_item)
        if self.last_scroll_index is not None:
            self.list_panel.on_scroll(self.last_scroll_index, silent=True)
            self.list_panel.scrollbar.set_scroll(self.last_scroll_index)
        else:
            self.list_panel.on_scroll(0, silent=True)
        return

    def get_prefab_set_name(self):
        prefab_set_id = SteamGetLobbyData(self.lobby_id, 'PREFAB_SET')
        if prefab_set_id == '':
            prefab_set_id = str(A3037)
            SteamSetLobbyData('PREFAB_SET', prefab_set_id)
        id = int(prefab_set_id)
        if id in A3056:
            return strings.get_by_id(A3056[id])
        return ''

    def draw(self):
        super(MatchSettingsPanel, self).draw()
