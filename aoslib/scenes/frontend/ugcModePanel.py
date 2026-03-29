from aoslib.scenes.frontend.lobbyPanelBase import LobbyPanelBase
from aoslib.scenes.frontend.listPanelBase import ListPanelBase
from aoslib.scenes.main.listPanelItemBase import ListPanelItemBase
from aoslib.scenes.frontend.panelBase import BACKGROUND_NONE
from aoslib.scenes.main.matchSettings import get_list_items_as_string, get_game_info_data, get_string_as_list, get_default_match_length_for_playlist_in_minutes, get_playlist_with_id
from aoslib import strings
from aoslib.media import HUD_AUDIO_ZONE
from shared.constants_gamemode import A2448
from shared.steam import SteamSetLobbyData, SteamGetCurrentLobby, SteamGetLobbyData, SteamAmITheLobbyOwner
from aoslib.scenes.main.ownableItemBase import OwnableItemBase
import playlists

def get_ugc_lobby_modes(lobby_id):
    rows = []
    row_name_to_select = None
    mode_name = SteamGetLobbyData(lobby_id, 'UGC_MODES')
    for mode in A2448.keys():
        mode_title = strings.get_by_id(A2448[mode])
        if mode in ('tut', 'ugc', 'cctf'):
            continue
        if mode_title == strings.CTF_TITLE:
            mode_title = strings.CTF_AND_CLASSIC_CTF
        if mode_name == mode:
            row_name_to_select = mode_title
        rows.append(mode_title)

    return (rows, row_name_to_select)


class UGCModePanel(LobbyPanelBase):

    def initialize(self):
        super(UGCModePanel, self).initialize()
        self.list_panel = ListPanelBase(self.manager)

    def initialise_ui(self, lobby_id, x, y, width, height):
        super(UGCModePanel, self).initialise_ui(lobby_id, x, y, width, height)
        self.selected_server_type = None
        self.list_panel.initialise_ui(strings.CHOOSE_GAME_MODE, x, y, width, height, has_header=True)
        self.list_panel.set_background(BACKGROUND_NONE)
        self.list_panel.center_header_text = True
        self.list_panel.add_on_item_selected_handler(self.on_row_selected, 0)
        self.elements.append(self.list_panel)
        self.playlist = None
        self.__initialise()
        return

    def close(self):
        for row in [row for row in self.list_panel.rows if hasattr(row, 'close')]:
            row.close()

        return super(UGCModePanel, self).close()

    def __initialise(self):
        self.populate_playlist()

    def set_content_visibility(self, visible):
        super(UGCModePanel, self).set_content_visibility(visible)
        if not SteamAmITheLobbyOwner():
            return
        if visible:
            self.__initialise()

    def on_row_selected(self, index, row):
        if row is None:
            return
        else:
            modes = []
            row_name = row.name
            if row_name == strings.CTF_AND_CLASSIC_CTF:
                row_name = strings.CTF_TITLE
            for mode in A2448.keys():
                if strings.get_by_id(A2448[mode]) == row_name:
                    modes.append(mode)

            SteamSetLobbyData('UGC_MODES', get_list_items_as_string(modes))
            return

    def populate_playlist(self):
        if self.list_panel is None:
            return
        else:
            del self.list_panel.rows[:]
            rows, row_name_to_select = get_ugc_lobby_modes(self.lobby_id)
            for mode_title in rows:
                list_item = OwnableItemBase(mode_title, self.list_panel.manager.dlc_manager)
                list_item.center_text = False
                self.list_panel.rows.append(list_item)

            for row in [row for row in self.list_panel.rows if hasattr(row, 'close')]:
                row.close()

            self.list_panel.on_scroll(0, silent=True)
            if row_name_to_select is not None:
                self.list_panel.select_row_with_name(row_name_to_select)
            return

    def draw(self):
        super(UGCModePanel, self).draw()
