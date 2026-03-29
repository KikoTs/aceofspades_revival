from aoslib.scenes.frontend.listPreviewMenuBase import ListPreviewMenuBase
from aoslib.scenes.frontend.previewPanelBase import PreviewPanelBase
from aoslib.scenes.frontend.listPanelBase import ListPanelBase
from aoslib.scenes.main.squadListItem import SquadListItem
from aoslib.scenes.gui.dropBoxControl import DropBoxControl
from aoslib.gui import TextButton
from aoslib.squadEventManager import *
from aoslib.scenes.frontend.squadChatLog import *
from aoslib import strings
from aoslib.scenes.main.matchSettings import get_list_items_as_string, get_default_playlist, reset_all_game_rules, get_default_match_length_for_playlist_in_minutes
from shared.steam import SteamEnumerateFriendLobbies, SteamEnumeratePublicLobbies, SteamGetLobbyMembers, SteamCreateLobby, SteamJoinLobby, SteamSetLobbyData, SteamGetPersonaName, SteamLeaveLobby, SteamRefreshLobbyData, SteamGetLobbyData, SteamActivateGameOverlayToStore, SteamClearAllPingRequests, SteamGetFriendList, SteamGetFriendLobbyOwner, SteamIsLoggedOn
from shared.constants_gamemode import A2435
from shared.constants_matchmaking import *
from shared.constants import SPADES_GAME_APP_ID, ERROR_LOBBY_FULL, ERROR_LOBBY_CLOSED, ERROR_LOBBY_UNKNOWN
from shared.constants_shop import DLC_APPID_LIST
from shared.hud_constants import TEXT_BACKGROUND_SPACING, LIST_PANEL_SPACING
from twisted.internet import reactor
import playlists
from aoslib.media import HUD_AUDIO_ZONE
from shared.steam import game_version

class BaseSquadsMenu(ListPreviewMenuBase):
    auto_data_refresh_callback = None
    last_squad_auto_refreshed = 0
    title = strings.SQUAD_LIST
    lobbyType = 'None'
    create_button_text = strings.CREATE_SQUAD
    join_button_text = strings.JOIN_SQUAD
    available_lobbies_text = strings.AVAILABLE_SQUADS

    def initialize(self):
        super(BaseSquadsMenu, self).initialize(self.title)
        self.list_panel = ListPanelBase(self.manager)
        self.preview_panel = PreviewPanelBase(self.manager)
        self.button_height = 50
        self.last_selected_filter_index = 1
        self.join_squad_button = None
        self.buy_now_button = None
        self.button_background_x = 0
        self.button_background_y = 0
        self.button_background_scale_x = 1.0
        self.button_background_scale_y = 1.0
        self.create_game_button = None
        return

    def on_start(self, *arg, **kw):
        SteamLeaveLobby()
        SteamClearAllPingRequests()
        self.elements = []
        self.buttons = []
        self.elements.append(self.navigation_bar)
        self.elements.append(self.list_panel)
        self.elements.append(self.preview_panel)
        button_y = 144
        button_width = 162
        self.buy_now_button = self.create_button(strings.BUY_NOW, 405, button_y, button_width, self.button_height, 18, self.on_buy_now_clicked)
        self.buy_now_button.tint = (0.2, 1.0, 0.2)
        self.buy_now_button.text_colour = (255, 255, 255, 255)
        if self.lobbyType == A2664:
            self.join_squad_button = self.create_button(self.join_button_text, 405, button_y, 332, self.button_height, 18, self.on_join_squad_clicked)
        else:
            self.join_squad_button = self.create_button(self.join_button_text, 405, button_y, button_width, self.button_height, 18, self.on_join_squad_clicked)
            self.create_game_button = self.create_button(self.create_button_text, 575, button_y, button_width, self.button_height, 18, self.create_squad)
        self.set_join_button_visibility()
        self.list_panel.initialise_ui(self.available_lobbies_text, 56, 505, 340, 413, row_height=25, has_header=True)
        self.list_panel.title_width = 150
        self.list_panel.add_on_item_selected_handler(self.on_row_selected, 0)
        self.preview_panel.initialise_ui(None, 401, 505, 340, 354, has_header=True)
        filter_width = 130
        filter_x = self.list_panel.x + self.list_panel.width - filter_width - TEXT_BACKGROUND_SPACING - LIST_PANEL_SPACING
        self.server_type_filter = DropBoxControl(self.manager, [strings.get_by_id('FRIENDS'), strings.get_by_id('OPEN')], self.last_selected_filter_index, filter_x, 462, filter_width, 24, 2)
        self.server_type_filter.add_handler(self.on_server_type_filter_changed)
        self.elements.append(self.server_type_filter)
        button_background_height = self.button_height + 4.0
        self.button_background_x = self.preview_panel.x + self.preview_panel.width / 2.0
        self.button_background_y = button_y - self.button_height - 1 + button_background_height / 2.0 + 1
        self.button_background_scale_x = float(self.preview_panel.width) / float(global_images.panel_frame.width)
        self.button_background_scale_y = float(button_background_height) / float(global_images.panel_frame.height)
        squadEventMgr.register_callback(squadEventMgr.on_data_changed, self.on_data_changed)
        self.on_refresh()
        chatLog.profanity_manager = self.manager.game_scene.profanity_manager
        chatLog.clear_log()
        self.auto_data_refresh_callback = reactor.callLater(1.0, self.on_auto_data_refresh)
        return

    def on_stop(self):
        if self.auto_data_refresh_callback:
            self.auto_data_refresh_callback.cancel()
            self.auto_data_refresh_callback = None
        self.last_selected_filter_index = self.server_type_filter.get_selected_index()
        self.selected_row = self.list_panel.get_selected_item()
        squadEventMgr.unregister_callback(squadEventMgr.on_data_changed, self.on_data_changed)
        return

    def update(self, dt):
        super(BaseSquadsMenu, self).update(dt)
        if not SteamIsLoggedOn():
            from aoslib.scenes.frontend.selectMenu import SelectMenu
            self.manager.set_menu(SelectMenu, back=True)

    def on_data_changed(self, lobby_id, success):
        if success:
            selected_row = self.list_panel.get_selected_item()
            if selected_row is not None:
                if lobby_id == selected_row.lobby_id:
                    selected_row.refresh()
                    self.preview_panel.update_display_data(selected_row.lobby_id)
            row = self.get_row_with_lobby_id(lobby_id)
            if row is not None:
                row.refresh()
        else:
            selected_row = self.list_panel.get_selected_item()
            if selected_row and lobby_id == selected_row.lobby_id:
                self.preview_panel.clear_display_data()
                self.list_panel.remove_row(selected_row)
                self.list_panel.on_scroll(self.list_panel.current_row_index - 1, silent=True)
            else:
                row = self.get_row_with_lobby_id(lobby_id)
                if row:
                    self.list_panel.remove_row(row)
        self.set_join_button_visibility()
        return

    def on_join_squad_clicked(self):
        squad = self.list_panel.get_selected_item()
        if squad is None:
            return
        else:
            if self.media:
                self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
            self.do_join_lobby(squad.lobby_id)
            return

    def on_buy_now_clicked(self):
        self.media.play('menu_buyA', zone=HUD_AUDIO_ZONE)
        SteamActivateGameOverlayToStore(DLC_APPID_LIST['mafia'])

    def do_join_lobby(self, lobby_id):
        SteamJoinLobby(self.on_lobby_join_success, self.on_lobby_join_error, lobby_id)

    def on_lobby_join_success(self, lobby_id):
        pass

    def on_lobby_join_error(self, error):
        if error == A2690:
            self.manager.set_big_text_message(ERROR_LOBBY_CLOSED, False, 5.0)
        elif error == A2692:
            self.manager.set_big_text_message(ERROR_LOBBY_FULL, False, 5.0)
        else:
            self.manager.set_big_text_message(ERROR_LOBBY_UNKNOWN, False, 5.0)
        self.on_refresh()

    def on_row_selected(self, index, row):
        if row is None:
            return
        else:
            self.preview_panel.title = row.name
            self.preview_panel.update_display_data(row.lobby_id)
            self.set_join_button_visibility()
            return

    def set_join_button_visibility(self):
        show_buy = False
        for row in self.preview_panel.info_list.rows:
            if hasattr(row, 'owned') and not row.owned:
                show_buy = True
                break

        if show_buy:
            self.join_squad_button.set_visible(False)
            self.join_squad_button.set_enabled(False)
            self.buy_now_button.set_visible(True)
            self.buy_now_button.set_enabled(True)
            return
        else:
            self.join_squad_button.set_visible(True)
            self.buy_now_button.set_visible(False)
            self.buy_now_button.set_enabled(False)
            selected_row = self.list_panel.get_selected_item()
            join_enabled = len(self.preview_panel.info_list.rows) > 0 and selected_row is not None and selected_row.is_open() and not selected_row.is_squad_full()
            self.join_squad_button.set_enabled(join_enabled)
            return

    def on_server_type_filter_changed(self, selected_index, repopulate=True):
        if repopulate:
            del self.list_panel.rows[:]
        server_type = self.server_type_filter.get_row_value_for_index(selected_index)
        if server_type == strings.get_by_id('OPEN'):
            SteamEnumeratePublicLobbies(self.friend_lobby_found)
        else:
            SteamEnumerateFriendLobbies(self.friend_lobby_found)
        if len(self.list_panel.rows) > 0:
            selected_row = self.list_panel.get_selected_item()
            if selected_row is None:
                self.list_panel.select_row(self.list_panel.rows[0], True)
            elif selected_row.get_is_selected() == False:
                self.list_panel.select_row(selected_row, True)
        return

    def friend_lobby_found(self, lobby_id):
        add_lobby = False
        server_type = self.server_type_filter.get_row_value_for_index(self.server_type_filter.get_selected_index())
        if server_type != strings.get_by_id('OPEN'):
            self.friend_list = SteamGetFriendList()
            owner_id = SteamGetFriendLobbyOwner(lobby_id)
            if owner_id in self.friend_list:
                add_lobby = True
        else:
            add_lobby = True
        if add_lobby:
            if SteamGetLobbyData(lobby_id, 'Version') in (str(game_version()), ''):
                if SteamGetLobbyData(lobby_id, 'LobbyType') in (str(self.lobbyType), ''):
                    self.add_available_squad_row(lobby_id)

    def add_available_squad_row(self, lobby_id):
        row = self.get_row_with_lobby_id(lobby_id)
        if row is None:
            new_row = SquadListItem(lobby_id)
            self.list_panel.rows.append(new_row)
            self.list_panel.on_scroll(0, silent=True)
            if self.selected_row is not None:
                self.list_panel.select_row(self.selected_row, silent=True)
        return

    def get_row_with_lobby_id(self, lobby_id):
        for row in self.list_panel.rows:
            if row.lobby_id == lobby_id:
                return row

        return

    def open_parent_menu(self):
        from selectMenu import SelectMenu
        self.parent.set_menu(SelectMenu, back=True)

    def draw_buttons_background(self):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        gl.glPushMatrix()
        gl.glTranslatef(self.button_background_x, self.button_background_y, 0)
        gl.glScalef(self.button_background_scale_x, self.button_background_scale_y, 0.0)
        global_images.panel_frame.blit(0, 0)
        gl.glPopMatrix()

    def draw(self):
        super(BaseSquadsMenu, self).draw()

    def on_auto_data_refresh(self):
        self.on_refresh()
        self.auto_data_refresh_callback = reactor.callLater(1.0, self.on_auto_data_refresh)
        other_row = None
        if len(self.list_panel.rows) > 0:
            next_squad = self.last_squad_auto_refreshed + 1
            next_squad = int((next_squad - self.list_panel.min_index) % min(self.list_panel.noof_visible_items, len(self.list_panel.rows)) + self.list_panel.min_index)
            other_row = self.list_panel.rows[next_squad]
            SteamRefreshLobbyData(other_row.lobby_id)
            self.last_squad_auto_refreshed = next_squad
        row = self.list_panel.get_selected_item()
        if row in (None, other_row):
            return
        else:
            SteamRefreshLobbyData(row.lobby_id)
            return

    def on_refresh(self):
        self.on_server_type_filter_changed(self.server_type_filter.get_selected_index(), False)
        if not self.list_panel.get_selected_item():
            self.preview_panel.clear_display_data()
            self.set_join_button_visibility()

    def lobby_created_callback(self, lobby_id):
        pass

    def lobby_create_error_callback(self, reason):
        pass

    def create_squad(self):
        self.media.stop_sounds()
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        SteamCreateLobby(self.lobby_created_callback, self.lobby_create_error_callback)
