from aoslib.scenes.frontend.listPreviewMenuBase import ListPreviewMenuBase
from aoslib.scenes.frontend.previewPanelBase import PreviewPanelBase
from aoslib.scenes.frontend.listPanelBase import ListPanelBase
from aoslib.scenes.main.squadFriendListItem import SquadFriendListItem
from aoslib.scenes.frontend.matchSettingsPanel import MatchSettingsPanel
from aoslib.scenes.frontend.gameRulesPanel import GameRulesPanel
from aoslib.scenes.frontend.prefabSetsPanel import PrefabSetsPanel
from aoslib.scenes.frontend.mapsPanel import MapsPanel
from aoslib.scenes.frontend.playlistPanel import PlayListPanel
from aoslib.scenes.frontend.ugcModePanel import UGCModePanel
from aoslib.draw import draw_line
from aoslib.gui import TextButton
from aoslib.draw import draw_line
from aoslib import strings
from shared.steam import SteamGetPersonaName, SteamGetLobbyMembers, SteamGetCurrentLobby, SteamGetLobbyMemberName, SteamGetPersonaName, SteamShowInviteFriendOverlay, SteamLeaveLobby, SteamGetLobbyOwner, SteamAmITheLobbyOwner, SteamSetLobbyData, SteamSetLobbyMemberData, SteamGetLobbyData, SteamGetLobbyMemberData, SteamSendChatMessage, SteamSetLobbyGameServer, SteamGetLobbyGameServer, SteamClearLobbyGameServer, GetUserSteamID, SteamIsLoggedOn
from aoslib.scenes.frontend.squadChatLog import *
from aoslib.squadEventManager import *
from twisted.internet import reactor
from aoslib.tools import make_server_identifier, ip_to_int
from shared.steam import SteamGetSessionTicket, SteamGetAllLobbyData, SteamActivateGameOverlayToStore
from shared.constants import ERROR_KICKED, SPADES_GAME_APP_ID
from shared.constants_shop import DLC_APPID_LIST
from aoslib.scenes.frontend.customServerJoiner import CustomServerJoiner
from aoslib.scenes.frontend.playlistServerJoiner import PlaylistServerJoiner
from aoslib.scenes.main.matchSettings import get_string_as_list
from aoslib.images import global_images
from pyglet import gl
from aoslib.text import medium_aldo_ui_font, draw_text_with_alignment_and_size_validation, modify_name_to_fix_width
import playlists, random
from shared.constants import TEAM1, TEAM2, TEAM_NEUTRAL, TEAM_COLOURS
from shared.hud_constants import LIST_PANEL_SPACING, DARK_GREEN_COLOUR, TEXT_BACKGROUND_SPACING
import time
from aoslib.media import HUD_AUDIO_ZONE
import ast
from aoslib.common import get_map_value_safe
from shared.steam import game_version
from shared.constants_prefabs import A3037
PANEL_PREVIEW, PANEL_SETTINGS, PANEL_RULES, PANEL_PLAYLISTS, PANEL_UGC_MODE, PANEL_MAPS, PANEL_PREFAB_SETS = xrange(7)
OPTION_TEAM1, OPTION_TEAM_NEUTRAL, OPTION_TEAM2, OPTION_KICK_PLAYER = xrange(4)

class BaseSquadLobbyMenu(ListPreviewMenuBase):
    chat_log = None
    starting_game = False
    start_game_timer = 0
    enable_team_assignment = True
    enable_kick_button = False
    start_game_tick_callback = None
    server_finder = None
    last_host_message = [
     strings.WAITING_FOR_HOST, 0.0]
    title = strings.MATCH_LOBBY
    settings_title = strings.MATCH_SETTINGS
    started = False

    def initialize(self, ugc_mode=False):
        super(BaseSquadLobbyMenu, self).initialize(self.title)
        self.invite_button = None
        self.ugc_mode = ugc_mode
        self.__initialise_panels()
        self.lobby_id = None
        self.last_selected_row = None
        self.teams = [TEAM1, TEAM_NEUTRAL, TEAM2]
        self.max_players = None
        self.button_background_x = 0
        self.button_background_y = 0
        self.button_background_scale_x = 1.0
        self.button_background_scale_y = 1.0
        self.start_game_button = None
        self.buy_now_button = None
        self.draw_team_dropdown_boxes = False
        self.draw_kick_button = False
        self.team_count = {TEAM1: 0, TEAM2: 0, TEAM_NEUTRAL: 0}
        self.squad_leader_id = None
        self.draw_team_selection_box = False
        return

    def __initialise_panels(self, initial_panel_id=None):
        self.current_panel = initial_panel_id
        self.previous_panel = initial_panel_id
        self.list_panel = ListPanelBase(self.manager)
        self.title_edit_box = EditBoxControl('', x=0, y=0, height=30, width=210, center=False, profanity_manager=self.manager.game_scene.profanity_manager, max_characters=19)
        self.title_edit_box.on_return_callback = self.refresh_name
        self.preview_panel = PreviewPanelBase(self.manager)
        self.edit_settings_button = None
        self.match_settings_panel = MatchSettingsPanel(self.manager)
        self.match_settings_panel.set_callbacks(self.on_game_rules_selected, self.on_playlists_selected, self.on_map_rotation_selected, self.on_ugc_mode_selected, self.on_cancel_game)
        self.match_settings_panel.on_show_prefab_set = self.on_prefab_sets_selected
        self.game_rules_panel = GameRulesPanel(self.manager)
        self.ugc_mode_panel = UGCModePanel(self.manager)
        self.maps_panel = MapsPanel(self.manager, self.ugc_mode)
        self.playlist_panel = PlayListPanel(self.manager, self.ugc_mode)
        self.playlist_panel.on_playlist_selected_callback = self.update_team_id_on_playlist_selected
        self.prefab_sets_panel = PrefabSetsPanel(self.manager)
        self.panels = {PANEL_PREVIEW: (self.preview_panel), 
           PANEL_SETTINGS: (self.match_settings_panel), 
           PANEL_RULES: (self.game_rules_panel), 
           PANEL_PLAYLISTS: (self.playlist_panel), 
           PANEL_UGC_MODE: (self.ugc_mode_panel), 
           PANEL_MAPS: (self.maps_panel), 
           PANEL_PREFAB_SETS: (self.prefab_sets_panel)}
        for id, panel in self.panels.iteritems():
            if panel is not None:
                panel.set_content_visibility(id == initial_panel_id)

        return

    def __initialise_buttons(self):
        button_y = 144
        button_width = self.preview_panel.width - 8
        button_height = 50
        self.start_game_button = self.create_button(strings.START_GAME, 405, button_y, button_width, button_height, 22, self.on_start_game)
        self.cancel_button = self.create_button(strings.CANCEL, 405, button_y, button_width, button_height, 22, self.on_cancel_game)
        self.start_game_button.set_constant_glow(True)
        self.confirm_button = self.create_button(strings.CONFIRM, 405, button_y, button_width, button_height, 22, self.on_confirm)
        self.join_game_button = self.create_button(strings.WAITING_FOR_HOST, 405, button_y, button_width, button_height, 22, self.on_join_game)
        self.buy_now_button = self.create_button(strings.BUY_NOW, 405, button_y, button_width, button_height, 22, self.on_buy_now)
        self.buy_now_button.tint = (0.2, 1.0, 0.2)
        self.buy_now_button.text_colour = (255, 255, 255, 255)
        button_width = 80
        button_height = 30
        x = self.list_panel.x + self.list_panel.width - button_width - LIST_PANEL_SPACING * 2
        y = self.list_panel.y - LIST_PANEL_SPACING - 6
        self.invite_button = self.create_button(strings.INVITE, x, y, button_width, button_height, 18, self.on_invite_friends)

    def on_start(self, *arg, **kw):
        from aoslib.gamemanager import GameManager
        if GameManager.invalid_data_error:
            from selectMenu import SelectMenu
            self.parent.set_menu(SelectMenu, back=True)
        self.media.stop_sounds()
        if not self.media.is_playing_music('mainmenu'):
            self.media.play_music('mainmenu', self.config.music_volume)
        self.elements = []
        self.buttons = []
        self.set_lobby_name_to_default = False
        lobby_id = SteamGetCurrentLobby()
        is_lobby_owner = SteamAmITheLobbyOwner()
        if lobby_id == 0:
            self.back_pressed(False)
            return
        else:
            self.server_finder = CustomServerJoiner(self, self.on_target_monitor_changed)
            if is_lobby_owner:
                self.default_server = self.manager.default_server
                if self.default_server is not None:
                    self.server_finder.set_target_monitor(self.default_server.ip, self.default_server.port, self.default_server.queryPort)
            else:
                self.default_server = None
            initial_panel_id = PANEL_SETTINGS if is_lobby_owner else PANEL_PREVIEW
            self.__initialise_panels(initial_panel_id)
            self.elements.append(self.navigation_bar)
            self.elements.append(self.list_panel)
            self.elements.append(self.title_edit_box)
            self.elements.append(self.preview_panel)
            self.elements.append(self.match_settings_panel)
            self.elements.append(self.game_rules_panel)
            self.elements.append(self.ugc_mode_panel)
            self.elements.append(self.maps_panel)
            self.elements.append(self.playlist_panel)
            self.elements.append(self.prefab_sets_panel)
            self.navigation_bar.left_button_text = strings.LEAVE_LOBBY
            self.dropdown_options = {OPTION_TEAM1: 'TEAM1_COLOR', 
               OPTION_TEAM_NEUTRAL: 'TEAM_NEUTRAL', 
               OPTION_TEAM2: 'TEAM2_COLOR', 
               OPTION_KICK_PLAYER: 'KICK_PLAYER'}
            self.list_panel.initialise_ui(None, 56, 505, 340, 270, row_height=25, has_header=True)
            self.list_panel.title_width = 210
            self.title_edit_box.x = 76
            self.title_edit_box.y = self.list_panel.y - LIST_PANEL_SPACING - 6 - self.title_edit_box.height
            self.list_panel.add_on_item_selected_handler(self.on_row_selected, 0)
            self.preview_panel.initialise_ui(strings.GAME_INFO, 401, 505, 340, 355, has_header=True)
            self.preview_panel.update_display_data(lobby_id)
            self.list_panel.manager.dlc_manager.append_dlc_installed_callback(self.on_dlc_installed)
            if not self.lobby_id or self.lobby_id != lobby_id:
                self.set_lobby_name_to_default = True
                self.match_settings_panel.reset_to_defaults()
                self.lobby_id = lobby_id
                SteamSetLobbyMemberData('name', SteamGetPersonaName())
            x = 400
            y = 505
            width = 340
            height = 355
            for id, panel in self.panels.iteritems():
                if id == PANEL_PREVIEW:
                    continue
                if id == PANEL_RULES:
                    panel.initialise_ui(lobby_id, x, y, width, height - self.list_panel.title_height + 10.0)
                else:
                    panel.initialise_ui(lobby_id, x, y, width, height)

            self.__initialise_buttons()
            self.set_panel_visibility(initial_panel_id, True)
            self.match_settings_panel.set_title(self.settings_title)
            button_y = self.start_game_button.y
            button_height = self.start_game_button.height
            button_background_height = button_height + 4.0
            self.button_background_x = self.preview_panel.x + self.preview_panel.width / 2.0
            self.button_background_y = button_y - button_height - 1 + button_background_height / 2.0 + 1
            self.button_background_scale_x = float(self.preview_panel.width) / float(global_images.panel_frame.width)
            self.button_background_scale_y = float(button_background_height) / float(global_images.panel_frame.height)
            self.chat_log = chatLog
            self.chat_log.profanity_manager = self.manager.game_scene.profanity_manager
            self.chat_log.media = self.manager.media
            self.chat_log.chat_box.caret_height = 12
            self.elements.append(self.chat_log)
            SteamSetLobbyMemberData('in-game', '0')
            current_team_id = SteamGetLobbyMemberData(lobby_id, GetUserSteamID(), 'team_id')
            if current_team_id is None or current_team_id == '':
                SteamSetLobbyMemberData('team_id', str(TEAM_NEUTRAL))
                SteamSetLobbyMemberData('cached_team_id', str(TEAM_NEUTRAL))
            self.populate_friends_list()
            self.update_buttons_enabled_state()
            squadEventMgr.register_callback(squadEventMgr.on_user_join, self.on_user_joined)
            squadEventMgr.register_callback(squadEventMgr.on_user_left, self.on_user_left)
            squadEventMgr.register_callback(squadEventMgr.on_user_kicked, self.on_user_kicked)
            squadEventMgr.register_callback(squadEventMgr.on_data_changed, self.on_data_changed)
            squadEventMgr.register_callback(squadEventMgr.on_chat, self.on_chat_received)
            self.started = True
            return

    def back_pressed(self, is_back):
        if is_back:
            self.do_cancel_game()
        super(BaseSquadLobbyMenu, self).back_pressed(is_back)

    def on_stop(self):
        squadEventMgr.unregister_callback(squadEventMgr.on_user_join, self.on_user_joined)
        squadEventMgr.unregister_callback(squadEventMgr.on_user_left, self.on_user_left)
        squadEventMgr.unregister_callback(squadEventMgr.on_user_kicked, self.on_user_kicked)
        squadEventMgr.unregister_callback(squadEventMgr.on_data_changed, self.on_data_changed)
        squadEventMgr.unregister_callback(squadEventMgr.on_chat, self.on_chat_received)
        self.list_panel.manager.dlc_manager.remove_dlc_installed_callback(self.on_dlc_installed)
        self.list_panel.close()
        self.preview_panel.close()
        self.match_settings_panel.close()
        self.game_rules_panel.close()
        self.ugc_mode_panel.close()
        self.maps_panel.close()
        self.playlist_panel.close()
        self.prefab_sets_panel.close()
        self.started = False

    def update_team_id_on_playlist_selected(self, draw_team_selection_box, enable_team_assignment, enable_kick_button):
        self.draw_team_selection_box = draw_team_selection_box
        self.enable_team_assignment = enable_team_assignment
        self.enable_kick_button = enable_kick_button
        if len(self.list_panel.rows) == 0:
            return
        else:
            if not SteamAmITheLobbyOwner():
                return
            owner_id = SteamGetLobbyOwner()
            dropdown_options = []
            if enable_team_assignment:
                for index, string_id in self.dropdown_options.iteritems():
                    dropdown_options.append(strings.get_by_id(string_id))

            else:
                dropdown_options.append(strings.get_by_id('TEAM_NEUTRAL'))
            kick_player_option = strings.get_by_id(self.dropdown_options[OPTION_KICK_PLAYER])
            self.team_count = {TEAM1: 0, TEAM2: 0, TEAM_NEUTRAL: 0}
            for row in self.list_panel.rows:
                if enable_team_assignment:
                    player_team_id = SteamGetLobbyMemberData(self.lobby_id, row.id, 'cached_team_id')
                    if player_team_id is None or player_team_id == '':
                        team_id = TEAM_NEUTRAL
                    else:
                        team_id = int(player_team_id)
                else:
                    team_id = TEAM_NEUTRAL
                self.team_count[team_id] += 1
                if row.id == owner_id:
                    SteamSetLobbyMemberData('team_id', str(team_id))
                    if kick_player_option in dropdown_options:
                        dropdown_options.remove(kick_player_option)
                    available_options = dropdown_options
                    row.set_show_kick_button(False)
                else:
                    message_data = self.build_parameter_string('SET_TEAM', (row.id, str(team_id)))
                    SteamSendChatMessage(('cmd:{0}').format(message_data))
                    if kick_player_option not in dropdown_options:
                        dropdown_options.append(kick_player_option)
                    available_options = dropdown_options
                    row.set_show_kick_button(enable_kick_button)
                selected_index = -1
                for index, option in enumerate(available_options):
                    if team_id == TEAM1 and option == strings.get_by_id('TEAM1_COLOR') or team_id == TEAM2 and option == strings.get_by_id('TEAM2_COLOR') or team_id == TEAM_NEUTRAL and option == strings.get_by_id('TEAM_NEUTRAL'):
                        selected_index = index
                        break

                row.set_team_id(team_id)
                row.set_dropdown_box_options(available_options, selected_index)

            for team_id, count in self.team_count.iteritems():
                self.set_team_lobby_data(team_id, count)

            return

    def on_mouse_release(self, x, y, button, modifiers):
        if not self.enabled:
            return
        else:
            enabled_elements = []
            for element in self.get_elements():
                if element.enabled:
                    if (type(element) is PreviewPanelBase or type(element) is ListPanelBase) and (element.visible_content == False or element.visible == False):
                        continue
                    enabled_elements.append(element)

            for element in enabled_elements:
                element.on_mouse_release(x, y, button, modifiers)

            for index in reversed(range(len(self.list_panel.rows))):
                row = self.list_panel.rows[index]
                if row.drop_box_control is not None and row.enabled:
                    row.drop_box_control.on_mouse_release(x, y, button, modifiers)
                if row.kick_button_control is not None and row.enabled:
                    row.kick_button_control.on_mouse_release(x, y, button, modifiers)

            return

    def on_mouse_motion(self, x, y, dx, dy):
        super(BaseSquadLobbyMenu, self).on_mouse_motion(x, y, dx, dy)
        for index in reversed(range(len(self.list_panel.rows))):
            row = self.list_panel.rows[index]
            if row.drop_box_control is not None and row.enabled:
                row.drop_box_control.on_mouse_motion(x, y, dx, dy)
            if row.kick_button_control is not None and row.enabled:
                row.kick_button_control.on_mouse_motion(x, y, dx, dy)

        return

    def on_dlc_installed(self, dlc_manager):
        if self.lobby_id is not None:
            self.preview_panel.update_display_data(self.lobby_id)
        self.update_buttons_enabled_state()
        return

    def update(self, dt):
        super(BaseSquadLobbyMenu, self).update(dt)
        if not SteamIsLoggedOn():
            from aoslib.scenes.frontend.selectMenu import SelectMenu
            self.manager.set_menu(SelectMenu, back=True)
        if SteamAmITheLobbyOwner():
            self.title_edit_box.enabled = True
            self.title_edit_box.visible = True
            self.list_panel.title = ''
            if self.default_server != self.manager.default_server:
                self.default_server = self.manager.default_server
                if self.default_server is not None:
                    self.server_finder.set_target_monitor(self.default_server.ip, self.default_server.port, self.default_server.queryPort)
        else:
            self.title_edit_box.enabled = False
            self.title_edit_box.visible = False
        self.update_join_button_text()
        return

    def is_available(self):
        if self.lobby_id is None:
            return False
        else:
            if len([row for row in self.preview_panel.info_list.rows if hasattr(row, 'owned') and not row.owned]) > 0:
                return False
            else:
                return True

            return

    def update_buttons_enabled_state(self):
        is_lobby_owner = SteamAmITheLobbyOwner()
        member_in_game = any(map((lambda friend: friend.is_in_game), self.list_panel.rows))
        self.update_invite_button()
        if member_in_game:
            hidden_buttons = [
             self.start_game_button, self.cancel_button, self.confirm_button]
            if self.is_available():
                hidden_buttons.append(self.buy_now_button)
                self.join_game_button.set_text(strings.JOIN_GAME)
                self.join_game_button.set_enabled(True)
                self.join_game_button.set_visible(True)
            else:
                hidden_buttons.append(self.join_game_button)
                self.buy_now_button.set_enabled(True)
                self.buy_now_button.set_visible(True)
            for button in hidden_buttons:
                button.set_enabled(False)
                button.set_visible(False)

        elif is_lobby_owner:
            if self.current_panel == PANEL_SETTINGS:
                if self.is_available():
                    self.start_game_button.set_enabled(not self.starting_game)
                    self.start_game_button.set_visible(not self.starting_game)
                    self.cancel_button.set_enabled(self.starting_game)
                    self.cancel_button.set_visible(self.starting_game)
                    for button in (self.confirm_button, self.buy_now_button, self.join_game_button):
                        button.set_enabled(False)
                        button.set_visible(False)

                else:
                    for button in (self.start_game_button, self.cancel_button, self.confirm_button, self.join_game_button):
                        button.set_enabled(False)
                        button.set_visible(False)

                    self.buy_now_button.set_enabled(True)
                    self.buy_now_button.set_visible(True)
            else:
                for button in (self.start_game_button, self.cancel_button, self.buy_now_button, self.join_game_button):
                    button.set_enabled(False)
                    button.set_visible(False)

                self.confirm_button.set_enabled(True)
                self.confirm_button.set_visible(True)
        else:
            hidden_buttons = [
             self.start_game_button, self.cancel_button, self.confirm_button]
            if self.is_available():
                hidden_buttons.append(self.buy_now_button)
                self.join_game_button.set_visible(True)
                self.join_game_button.set_enabled(False)
            else:
                hidden_buttons.append(self.join_game_button)
                self.buy_now_button.set_enabled(True)
                self.buy_now_button.set_visible(True)
            for button in hidden_buttons:
                button.set_enabled(False)
                button.set_visible(False)

    def update_join_button_text(self):
        if SteamAmITheLobbyOwner():
            if self.starting_game:
                self.cancel_button.set_text(self.last_host_message[0])
        else:
            member_in_game = any(map((lambda friend: friend.is_in_game), self.list_panel.rows))
            if member_in_game:
                self.join_game_button.set_text(strings.JOIN_GAME)
            elif self.last_host_message[0] != strings.WAITING_FOR_HOST:
                if time.time() - self.last_host_message[1] > 5.0:
                    self.last_host_message[0] = strings.WAITING_FOR_HOST
            self.join_game_button.set_text(self.last_host_message[0])

    def update_invite_button(self, lobby_data=None):
        if self.invite_button:
            if self.max_players is not None:
                current_players = len(self.list_panel.rows)
                if int(current_players) >= self.max_players:
                    self.invite_button.set_enabled(False)
                else:
                    self.invite_button.set_enabled(True)
            else:
                self.invite_button.set_enabled(True)
        return

    def on_user_joined(self, friend_id):
        self.populate_friends_list()

    def on_user_left(self, friend_id, kicked=False):
        self.populate_friends_list()

    def on_user_kicked(self, friend_id):
        if friend_id == GetUserSteamID() and not SteamAmITheLobbyOwner():
            self.manager.set_big_text_message(ERROR_KICKED, False, 5.0)
            self.open_parent_menu()
        else:
            self.populate_friends_list()

    def on_data_changed(self, lobby_id, success):
        if success and lobby_id == self.lobby_id:
            lobby_data = SteamGetAllLobbyData(self.lobby_id)
            lobby_version = get_map_value_safe(lobby_data, 'Version', default_value='')
            if lobby_version not in (str(game_version()), ''):
                print ('Your game version ({0}) does not match that with which the lobby was created ({1})').format(str(game_version()), lobby_version)
                self.open_parent_menu()
                return
            self.max_players = int(get_map_value_safe(lobby_data, 'MAX_PLAYERS', default_value='24'))
            self.preview_panel.update_display_data(self.lobby_id)
            self.update_rows_data()
            self.update_buttons_enabled_state()
            self.update_invite_button(lobby_data)
            self.refresh_name()
            is_host = SteamAmITheLobbyOwner()
            for team_id, count in self.team_count.iteritems():
                self.get_team_lobby_data(lobby_data, team_id)

            if is_host:
                players_in_game = any(map((lambda friend: friend.is_in_game), self.list_panel.rows))
                if self.preview_panel.visible_content and not players_in_game:
                    self.set_panel_visibility(PANEL_PREVIEW, False)
                    self.set_panel_visibility(PANEL_SETTINGS, True)
                elif self.preview_panel.visible_content == False and players_in_game:
                    self.set_panel_visibility(self.previous_panel, False)
                    self.set_panel_visibility(PANEL_PREVIEW, True)

    def on_chat_received(self, friend_id, raw_text):
        try:
            text_data = raw_text.partition(':')
            if text_data[0] == 'cmd':
                if friend_id == SteamGetLobbyOwner():
                    data_list = ast.literal_eval(text_data[2])
                    command = data_list[0]
                    parameters = data_list[1]
                    if command == 'JOIN_SERVER':
                        self.on_join_game()
                    elif command == 'SET_TEAM' or command == 'SET_CACHED_TEAM':
                        if SteamAmITheLobbyOwner() == False:
                            player_id = int(parameters[0])
                            if player_id == GetUserSteamID():
                                team_id = parameters[1]
                                if command == 'SET_CACHED_TEAM':
                                    SteamSetLobbyMemberData('cached_team_id', team_id)
                                else:
                                    SteamSetLobbyMemberData('team_id', team_id)
                                    self.update_rows_data()
            elif text_data[0] == 'announce':
                if friend_id == SteamGetLobbyOwner():
                    message = text_data[2]
                    data_list = ast.literal_eval(message)
                    translated = strings.get_by_id(data_list[0])
                    formatted = translated.format(*data_list[1])
                    self.last_host_message[0] = formatted
                    self.last_host_message[1] = time.time()
        except:
            print 'baseSquadLobbyMenu: invalid chat data received'

    def update_team_count_lobby_data(self):
        team1 = 0
        team2 = 0
        neutral = 0
        for row in self.list_panel.rows:
            team_id = row.get_team_id()
            if team_id == TEAM1:
                team1 += 1
            elif team_id == TEAM2:
                team2 += 1
            else:
                neutral += 1

        self.set_team_lobby_data(TEAM1, team1)
        self.set_team_lobby_data(TEAM2, team2)
        self.set_team_lobby_data(TEAM_NEUTRAL, neutral)

    def on_drop_box_option_changed_callback(self, option_name, row):
        if self.dropdown_options is None:
            return
        else:
            if option_name == strings.get_by_id(self.dropdown_options[OPTION_KICK_PLAYER]):
                self.on_kick_player(int(row.id))
                return
            if option_name == strings.get_by_id(self.dropdown_options[OPTION_TEAM1]):
                new_team_id = TEAM1
            elif option_name == strings.get_by_id(self.dropdown_options[OPTION_TEAM2]):
                new_team_id = TEAM2
            else:
                new_team_id = TEAM_NEUTRAL
            row_team_id = row.get_team_id()
            if new_team_id != row_team_id:
                row.set_team_id(new_team_id)
                if SteamAmITheLobbyOwner():
                    if row.is_leader:
                        SteamSetLobbyMemberData('team_id', str(new_team_id))
                        SteamSetLobbyMemberData('cached_team_id', str(new_team_id))
                    else:
                        message_data = self.build_parameter_string('SET_TEAM', (row.id, str(new_team_id)))
                        SteamSendChatMessage(('cmd:{0}').format(message_data))
                        message_data = self.build_parameter_string('SET_CACHED_TEAM', (row.id, str(new_team_id)))
                        SteamSendChatMessage(('cmd:{0}').format(message_data))
            if SteamAmITheLobbyOwner():
                self.update_team_count_lobby_data()
            return

    def on_kick_button_selected_callback(self, row):
        self.on_kick_player(int(row.id))

    def get_team_lobby_data(self, lobby_data, team_id):
        count = None
        if team_id == TEAM1:
            if get_map_value_safe(lobby_data, 'TEAM1') != None:
                self.team_count[TEAM1] = int(get_map_value_safe(lobby_data, 'TEAM1'))
        elif team_id == TEAM_NEUTRAL:
            if get_map_value_safe(lobby_data, 'TEAM_NEUTRAL') != None:
                self.team_count[TEAM_NEUTRAL] = int(get_map_value_safe(lobby_data, 'TEAM_NEUTRAL'))
        elif team_id == TEAM2:
            if get_map_value_safe(lobby_data, 'TEAM2') != None:
                self.team_count[TEAM2] = int(get_map_value_safe(lobby_data, 'TEAM2'))
        return

    def get_team_count(self, team_id):
        return self.team_count[team_id]

    def set_team_lobby_data(self, team_id, count):
        count = str(count)
        if team_id == TEAM1:
            SteamSetLobbyData('TEAM1', count)
        elif team_id == TEAM_NEUTRAL:
            SteamSetLobbyData('TEAM_NEUTRAL', count)
        elif team_id == TEAM2:
            SteamSetLobbyData('TEAM2', count)

    def get_team_id_for_player(self, player_id):
        player_team_id = SteamGetLobbyMemberData(self.lobby_id, player_id, 'team_id')
        if player_team_id is None or player_team_id == '':
            return TEAM_NEUTRAL
        return int(player_team_id)

    def update_rows_data(self):
        for row in self.list_panel.rows:
            if row.id in SteamGetLobbyMembers(self.lobby_id):
                row.is_in_game = int(SteamGetLobbyMemberData(self.lobby_id, row.id, 'in-game') or '0') != 0
                row.set_team_id(self.get_team_id_for_player(row.id))

    def populate_friends_list(self):
        last_scroll_index = self.list_panel.scrollbar.scroll_pos
        is_lobby_host = SteamAmITheLobbyOwner()
        self.draw_team_dropdown_boxes = is_lobby_host and self.draw_team_selection_box
        self.draw_kick_button = is_lobby_host and self.enable_kick_button
        self.list_panel.rows = []
        friends_list = []
        friend_ids = SteamGetLobbyMembers(self.lobby_id)
        new_squad_leader_id = SteamGetLobbyOwner()
        row_to_select = None
        initial_option_index = 1
        self.team_count = {TEAM1: 0, TEAM2: 0, TEAM_NEUTRAL: 0}
        dropdown_options = []
        kick_player_option = strings.get_by_id(self.dropdown_options[OPTION_KICK_PLAYER])
        if SteamGetLobbyData(self.lobby_id, 'PLAYLIST') != 'zom':
            for index, string_id in self.dropdown_options.iteritems():
                dropdown_options.append(strings.get_by_id(string_id))

        else:
            initial_option_index = 0
            dropdown_options.append(strings.get_by_id('TEAM_NEUTRAL'))
        for id in friend_ids:
            is_leader = id == new_squad_leader_id
            is_in_game = int(SteamGetLobbyMemberData(self.lobby_id, id, 'in-game') or '0') != 0
            team_id = self.get_team_id_for_player(id)
            self.team_count[team_id] += 1
            if is_leader and kick_player_option in dropdown_options:
                dropdown_options.remove(kick_player_option)
            elif not is_leader and kick_player_option not in dropdown_options:
                dropdown_options.append(kick_player_option)
            if team_id != TEAM_NEUTRAL:
                for index, option in enumerate(dropdown_options):
                    if team_id == TEAM1 and option == strings.get_by_id('TEAM1_COLOR') or team_id == TEAM2 and option == strings.get_by_id('TEAM2_COLOR'):
                        initial_option_index = index
                        break

            friend = SquadFriendListItem(self.manager, id, SteamGetLobbyMemberName(id), team_id, dropdown_options, initial_option_index, is_leader, self.draw_team_dropdown_boxes, self.draw_kick_button and not is_leader, is_in_game, profanity_manager=self.manager.game_scene.profanity_manager)
            friend.on_drop_box_option_changed_callback = self.on_drop_box_option_changed_callback
            friend.on_kick_button_selected_callback = self.on_kick_button_selected_callback
            if self.last_selected_row is None and is_leader or self.last_selected_row == id:
                row_to_select = friend
            if is_leader:
                self.add_friend_row(friend)
            else:
                friends_list.append(friend)

        for friend in friends_list:
            self.add_friend_row(friend)

        if is_lobby_host:
            for team_id, count in self.team_count.iteritems():
                self.set_team_lobby_data(team_id, count)

        if row_to_select is not None:
            self.list_panel.select_row(row_to_select, silent=True, fire_selected_row_event=False)
        if self.squad_leader_id != new_squad_leader_id:
            self.squad_leader_id = new_squad_leader_id
            if SteamAmITheLobbyOwner():
                current_playlist_id_string = SteamGetLobbyData(self.lobby_id, 'PlaylistID')
                if current_playlist_id_string == '':
                    self.match_settings_panel.reset_to_defaults()
                else:
                    self.playlist_panel.check_map_is_valid(current_playlist_id_string)
        self.refresh_name()
        if last_scroll_index is not None and last_scroll_index > -1:
            self.list_panel.on_scroll(last_scroll_index, silent=True)
            self.list_panel.scrollbar.set_scroll(last_scroll_index)
        else:
            self.list_panel.on_scroll(0, silent=True)
        if is_lobby_host:
            self.update_team_id_on_playlist_selected(self.draw_team_selection_box, self.enable_team_assignment, self.enable_kick_button)
        self.update_buttons_enabled_state()
        return

    def on_start_game(self):
        self.media.stop_sounds()
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        member_in_game = False
        for list_item in self.list_panel.rows:
            if list_item.is_in_game:
                member_in_game = True
                break

        if member_in_game:
            self.cancel_game_with_local_error('LOBBY_ERROR_MEMBERS_IN_GAME')
            return
        self.starting_game = True
        self.update_buttons_enabled_state()
        if self.server_finder.begin_search():
            self.start_game_timer = 6
            self.start_game_tick_callback = reactor.callLater(0.0, self.start_game_tick)
        else:
            self.cancel_game_with_local_error('LOBBY_ERROR_STEAM_LIST_UNAVAILABLE')

    def get_num_player_slots_required(self):
        return len(self.list_panel.rows)

    def on_target_monitor_changed(self, target_monitor):
        print 'on_target_monitor_changed:', target_monitor
        SteamSetLobbyData('LobbyIP', target_monitor[0])
        SteamSetLobbyData('LobbyPort', str(target_monitor[2]))

    def on_join_game(self):
        if self.is_available():
            self.starting_game = False
            server = SteamGetLobbyGameServer()
            if server:
                from aoslib.scenes.ingame_menus.loadingMenu import LoadingMenu
                identifier = make_server_identifier(server[0], server[1])
                SteamSetLobbyMemberData('in-game', '1')
                self.parent.set_menu(LoadingMenu, identifier=identifier, from_server_menu=True, name='Private server', previous_menu=type(self))

    def on_buy_now(self):
        self.media.play('menu_buyA', zone=HUD_AUDIO_ZONE)
        SteamActivateGameOverlayToStore(DLC_APPID_LIST['mafia'])

    def on_kick_player(self, friend_id):
        message_data = self.build_parameter_string('KICK_PLAYER', (friend_id,))
        SteamSendChatMessage(('cmd:{0}').format(message_data))

    def on_cancel_game(self, silent=False, only_if_started=False):
        if self.starting_game:
            if not silent:
                self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
            message_data = self.build_parameter_string('LOBBY_GAME_CANCELLED')
            SteamSendChatMessage(('announce:{0}').format(message_data))
        if only_if_started and self.starting_game or not only_if_started:
            self.do_cancel_game()

    def do_cancel_game(self):
        self.starting_game = False
        if self.start_game_tick_callback:
            self.start_game_tick_callback.cancel()
            self.start_game_tick_callback = None
        if self.server_finder:
            self.server_finder.cancel()
        if self.start_game_button:
            self.update_buttons_enabled_state()
        return

    def start_game_tick(self):
        self.start_game_tick_callback = None
        if not self.started:
            return
        else:
            self.start_game_timer -= 1
            if self.start_game_timer > 0:
                message_data = self.build_parameter_string('GAME_STARTING_MESSAGE', (self.start_game_timer,))
                encoded_string = ('announce:{0}').format(message_data)
                self.on_chat_received(GetUserSteamID(), encoded_string)
                SteamSendChatMessage(encoded_string)
                self.start_game_tick_callback = reactor.callLater(1.0, self.start_game_tick)
            else:
                message_data = self.build_parameter_string('FINDING_SERVER')
                SteamSendChatMessage(('announce:{0}').format(message_data))
                self.start_game_tick_callback = reactor.callLater(1.0, self.join_server)
            return

    def join_server(self):
        self.start_game_tick_callback = None
        if not self.started:
            return
        else:
            self.server_finder.join()
            return

    def found_server(self, ip, port):
        SteamSetLobbyGameServer(ip_to_int(ip), port)
        message_data = self.build_parameter_string('JOIN_SERVER')
        SteamSendChatMessage(('cmd:{0}').format(message_data))

    def on_invite_friends(self):
        self.media.stop_sounds()
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        SteamShowInviteFriendOverlay()

    def on_confirm(self):
        self.media.stop_sounds()
        self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
        previous = PANEL_PREVIEW if self.current_panel == PANEL_SETTINGS else self.previous_panel
        current = self.current_panel
        self.set_panel_visibility(current, False)
        self.set_panel_visibility(previous, True)

    def set_panel_visibility(self, panel_id, visible):
        if self.panels[panel_id] is not None:
            self.panels[panel_id].set_content_visibility(visible)
        if visible:
            self.previous_panel = self.current_panel
            self.current_panel = panel_id
        self.update_buttons_enabled_state()
        self.preview_panel.has_header = self.current_panel == PANEL_PREVIEW
        return

    def on_map_rotation_selected(self):
        self.set_panel_visibility(self.current_panel, False)
        self.set_panel_visibility(PANEL_MAPS, True)

    def on_playlists_selected(self):
        self.set_panel_visibility(self.current_panel, False)
        self.set_panel_visibility(PANEL_PLAYLISTS, True)

    def on_ugc_mode_selected(self):
        self.set_panel_visibility(self.current_panel, False)
        self.set_panel_visibility(PANEL_UGC_MODE, True)

    def on_game_rules_selected(self):
        self.set_panel_visibility(self.current_panel, False)
        self.set_panel_visibility(PANEL_RULES, True)

    def on_prefab_sets_selected(self):
        self.set_panel_visibility(self.current_panel, False)
        self.set_panel_visibility(PANEL_PREFAB_SETS, True)

    def on_match_settings(self):
        self.media.stop_sounds()
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        self.set_panel_visibility(self.current_panel, False)
        self.set_panel_visibility(PANEL_SETTINGS, True)

    def on_row_selected(self, index, row):
        if row is None:
            return
        else:
            self.last_selected_row = row.id
            return

    def add_friend_row(self, friend):
        if friend in self.list_panel.rows:
            return
        self.list_panel.rows.append(friend)
        self.list_panel.on_scroll(0, silent=True)

    def open_parent_menu(self):
        pass

    def draw_buttons_background(self):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        gl.glPushMatrix()
        gl.glTranslatef(self.button_background_x, self.button_background_y, 0)
        gl.glScalef(self.button_background_scale_x, self.button_background_scale_y, 0.0)
        global_images.panel_frame.blit(0, 0)
        gl.glPopMatrix()

    def draw_player_count(self):
        height = 20
        x = self.list_panel.x + 1
        y = 213 + height
        width = self.list_panel.width
        draw_quad(x, y - height, width, height, DARK_GREEN_COLOUR)
        image_size = height - 6
        scale_x = image_size / float(global_images.head_1.width)
        scale_y = image_size / float(global_images.head_1.height)
        half_image_size = image_size / 2.0
        pad = 5
        image_x = self.list_panel.x + half_image_size + TEXT_BACKGROUND_SPACING
        text_x = image_x + pad
        y -= height / 2.0
        teams = self.teams
        if not self.enable_team_assignment:
            teams = [
             TEAM_NEUTRAL]
        for team_id in teams:
            gl.glColor4f(1.0, 1.0, 1.0, 1.0)
            gl.glPushMatrix()
            gl.glTranslatef(image_x, y, 0)
            gl.glScalef(scale_x, scale_y, 0.0)
            global_images.head_1.blit(0, 0)
            colour = TEAM_COLOURS[team_id]
            if len(colour) == 3:
                colour = colour + (255, )
            gl.glColor4ub(*colour)
            global_images.head_color_1.blit(0, 0)
            gl.glPopMatrix()
            text_width = image_size
            team_count = self.get_team_count(team_id)
            draw_text_with_alignment_and_size_validation(str(team_count), text_x, y - height / 2, text_width, height, colour, medium_aldo_ui_font, 'right', 'center')
            image_x += text_width + pad + image_size
            text_x = image_x + pad

        x2 = self.list_panel.x + self.list_panel.width
        icon_size = height - 8
        text_width = 70
        icon_x = x2 - icon_size - TEXT_BACKGROUND_SPACING
        scale_x = icon_size / float(global_images.player_count_icon.width)
        scale_y = icon_size / float(global_images.player_count_icon.height)
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        gl.glPushMatrix()
        gl.glTranslatef(icon_x + pad, y, 0)
        gl.glScalef(scale_x, scale_y, 0.0)
        global_images.player_count_icon.blit(0, 0)
        gl.glPopMatrix()
        text = str(len(self.list_panel.rows)) + ' ' + strings.PLAYERS
        text_x = icon_x - pad * 2 - text_width
        draw_text_with_alignment_and_size_validation(text, text_x, y - height / 2, text_width, height, (255,
                                                                                                        255,
                                                                                                        255,
                                                                                                        255), medium_aldo_ui_font, alignment_x='right', alignment_y='center')
        draw_line(x, self.chat_log.pane_y, x + width, self.chat_log.pane_y, DARK_GREEN_COLOUR, 2)

    def draw(self):
        super(BaseSquadLobbyMenu, self).draw()
        self.draw_player_count()
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        self.chat_log.draw()
        if self.draw_team_dropdown_boxes:
            for index in reversed(range(len(self.list_panel.rows))):
                row = self.list_panel.rows[index]
                if row.drop_box_control is not None and row.enabled:
                    row.drop_box_control.draw()

        if self.draw_kick_button:
            for index in reversed(range(len(self.list_panel.rows))):
                row = self.list_panel.rows[index]
                if row.kick_button_control is not None and row.enabled:
                    row.kick_button_control.draw()

        return

    def build_server_config(self):
        if self.lobby_id is None:
            return {}
        else:
            lobby_data = SteamGetAllLobbyData(self.lobby_id)
            map_list = []
            if get_map_value_safe(lobby_data, 'PlaylistID') != None:
                playlist_id = int(get_map_value_safe(lobby_data, 'PlaylistID'))
            else:
                return {}
            if get_map_value_safe(lobby_data, 'MATCH_LENGTH') != None:
                match_length = int(get_map_value_safe(lobby_data, 'MATCH_LENGTH'))
            else:
                return {}
            map_rotation_string = get_map_value_safe(lobby_data, 'MAP_ROTATION_FILENAME', default_value='')
            ugc_modes_string = get_map_value_safe(lobby_data, 'UGC_MODES', default_value='')
            selected_maps = get_string_as_list(map_rotation_string)
            modes_string = get_map_value_safe(lobby_data, 'PLAYLIST', default_value='')
            if self.ugc_mode and modes_string != 'ugc':
                modes_string = 'ugc'
            selected_modes = get_string_as_list(modes_string)
            prefab_set_id = get_map_value_safe(lobby_data, 'PREFAB_SET', silent=True, default_value=str(A3037))
            prefab_sets = [A3037] if not prefab_set_id or prefab_set_id == '' else [int(prefab_set_id)]
            if SteamAmITheLobbyOwner():
                for map_name in selected_maps:
                    if map_name not in playlists.mapinfo.map_info:
                        from aoslib.ugc_data import get_ugc_data_from_file
                        data = get_ugc_data_from_file(map_name)
                        SteamSetLobbyData('Custom_UGC_Map_Author', data['author'])
                        if data is not None and data['baseplate'] in playlists.mapinfo.map_info:
                            map_info = playlists.mapinfo.map_info[data['baseplate']]
                            for mode in selected_modes:
                                map_list.append(mode + '_' + data['baseplate'])

                        else:
                            return {}
                    else:
                        map_info = playlists.mapinfo.map_info[map_name]
                        for mode in selected_modes:
                            if mode not in map_info['invalid_modes']:
                                map_list.append(mode + '_' + map_name)

                if len(map_list) == 0:
                    return {}
            random.shuffle(map_list)
            forced_team_members = {}
            for row in self.list_panel.rows:
                team_id = row.get_team_id()
                if team_id == TEAM_NEUTRAL:
                    continue
                forced_team_members[str(row.id)] = team_id

            playlist = playlists.play_lists_by_id[playlist_id]
            max_players = get_map_value_safe(lobby_data, 'MAX_PLAYERS', default_value='24')
            ugc_modes = get_string_as_list(ugc_modes_string)
            config = {'mode': modes_string, 
               'ugc_modes': ugc_modes, 
               'playlist_id': playlist_id, 
               'ranked': False, 
               'classic': (playlist.classic), 
               'skin': ('mafia' if playlist.mafia else ''), 
               'max_players': max_players, 
               'maps': map_list, 
               'name': 'Private server', 
               'forced_team_members': forced_team_members, 
               'match_length': match_length, 
               'prefab_sets': prefab_sets}
            for key, value in lobby_data.iteritems():
                if key in A2688.keys():
                    rule = A2688[key]
                    if value == '':
                        continue
                    config[key] = value

            return config

    def build_parameter_string(self, string_id, params=()):
        text = str([string_id, params])
        return text

    def cancel_game_with_local_error(self, error_id, params=()):
        error_text = self.build_parameter_string(error_id, params)
        self.chat_log.on_chat_received(0, ('error:{0}').format(error_text))
        self.do_cancel_game()

    def cancel_game_with_broadcast_error(self, error_id, params=()):
        error_text = self.build_parameter_string(error_id, params)
        SteamSendChatMessage(('error:{0}').format(error_text))
        self.do_cancel_game()

    def refresh_name(self):
        if not SteamAmITheLobbyOwner():
            new_name = SteamGetLobbyData(self.lobby_id, 'Name')
            self.list_panel.title = new_name
            return
        if self.set_lobby_name_to_default:
            if not self.title_edit_box.empty_text or len(self.title_edit_box.empty_text) < 1:
                str_leader_name = SteamGetPersonaName()
                header_font = self.list_panel.get_header_font()
                text_length_without_leader_name = header_font.get_content_width(strings.PLAYER_SQUAD.format(''))
                width = self.list_panel.title_width - text_length_without_leader_name
                leader_name = modify_name_to_fix_width(str_leader_name, width, header_font)
                formatted_text = self.manager.game_scene.profanity_manager.sanitise_string(strings.PLAYER_SQUAD.format(leader_name))
                self.title_edit_box.empty_text = formatted_text
        else:
            new_name = SteamGetLobbyData(self.lobby_id, 'Name')
            self.title_edit_box.empty_text = new_name
        new_name = self.title_edit_box.text
        if len(new_name) < 1:
            new_name = self.title_edit_box.empty_text
        if new_name != self.list_panel.title:
            self.list_panel.title = new_name
            SteamSetLobbyData('Name', new_name)
