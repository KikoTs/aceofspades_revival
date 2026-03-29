from aoslib.scenes.frontend.listPanelBase import ListPanelBase
from aoslib.scenes.main.prefabSetListItem import PrefabSetListItem
from aoslib.scenes.frontend.lobbyPanelBase import LobbyPanelBase
from aoslib import strings
from shared.steam import SteamGetLobbyData, SteamSetLobbyData, SteamAmITheLobbyOwner
from shared.constants_prefabs import A3056
import playlists

class PrefabSetsPanel(LobbyPanelBase):

    def initialize(self):
        super(PrefabSetsPanel, self).initialize()
        self.prefab_sets_list = ListPanelBase(self.manager)

    def initialise_ui(self, lobby_id, x, y, width, height):
        super(PrefabSetsPanel, self).initialise_ui(lobby_id, x, y, width, height)
        self.elements.append(self.prefab_sets_list)
        self.prefab_sets_list.initialise_ui(strings.PREFAB_SETS, x, y, width, height, has_header=True)
        self.prefab_sets_list.add_on_item_selected_handler(self.on_row_selected, 0)
        self.__initialise()

    def close(self):
        for row in [row for row in self.prefab_sets_list.rows if hasattr(row, 'close')]:
            row.close()

        return super(PrefabSetsPanel, self).close()

    def __initialise(self):
        self.populate_playlist()

    def set_content_visibility(self, visible):
        super(PrefabSetsPanel, self).set_content_visibility(visible)
        if not SteamAmITheLobbyOwner():
            return
        if visible:
            self.__initialise()

    def populate_playlist(self):
        del self.prefab_sets_list.rows[:]
        row_name_to_select = None
        row_id_to_select = SteamGetLobbyData(self.lobby_id, 'PREFAB_SET')
        row_id_to_select = int(row_id_to_select) if row_id_to_select != '' else 0
        for prefab_set_id, name in A3056.iteritems():
            row = PrefabSetListItem(strings.get_by_id(name), prefab_set_id)
            row.center_text = False
            self.prefab_sets_list.rows.append(row)
            if row_id_to_select == prefab_set_id:
                row_name_to_select = row.name

        self.prefab_sets_list.on_scroll(0, silent=True)
        if row_name_to_select is not None:
            self.prefab_sets_list.select_row_with_name(row_name_to_select)
        return

    def on_row_selected(self, index, row):
        SteamSetLobbyData('PREFAB_SET', str(row.id))

    def draw(self):
        super(PrefabSetsPanel, self).draw()
