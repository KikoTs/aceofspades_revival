from aoslib.scenes.frontend.listPanelBase import ListPanelBase
from aoslib.scenes.frontend.expandableListPanel import ExpandableListPanel
from aoslib.scenes.main.mapListItem import MapListItem
from aoslib.scenes.main.ownableItemBase import OwnableItemBase
from aoslib.scenes.main.categoryListItem import CategoryListItem
from aoslib.scenes.frontend.lobbyPanelBase import LobbyPanelBase
from aoslib.scenes.main.matchSettings import get_string_as_list, get_list_items_as_string, generate_ugc_map_filename_from_lobby, generate_ugc_map_filename, generate_ugc_map_title
from aoslib import strings
from aoslib.scenes import MenuScene
from aoslib.gui import SliderOption
from shared.constants_matchmaking import A2665
from shared.steam import SteamGetLobbyData, SteamSetLobbyData, SteamAmITheLobbyOwner, SteamGetSubscribedContentTitle
from shared.hud_constants import ROW_DARK_GREY_COLOUR, ROW_GREY_COLOUR
from aoslib.ugc_data import get_available_game_modes, get_map_baseplate, get_hosted_ugc_map_names, get_subscribed_ugc_map_names
from shared.constants_gamemode import A2450
from aoslib.ugc_data import get_ugc_data_from_file
import playlists

class MapsPanel(LobbyPanelBase):

    def __init__(self, manager, ugc_mode=False):
        self.ugc_mode = ugc_mode
        super(MapsPanel, self).__init__(manager)

    def initialize(self):
        super(MapsPanel, self).initialize()
        self.expandable_list_panel = ExpandableListPanel(self.manager)
        self.maps = {}
        self.original_maps = []

    def initialise_ui(self, lobby_id, x, y, width, height):
        super(MapsPanel, self).initialise_ui(lobby_id, x, y, width, height)
        self.elements.append(self.expandable_list_panel)
        self.select_all_text = strings.SELECT_ALL
        self.expandable_list_panel.initialise_ui(strings.MAPS, x, y, width, height, has_header=True)
        self.expandable_list_panel.center_header_text = True
        self.expandable_list_panel.add_on_item_selected_handler(self.on_row_selected, 0)
        self.__initialise()

    def close(self):
        for row in [row for row in self.expandable_list_panel.rows if hasattr(row, 'close')]:
            row.close()

        return super(MapsPanel, self).close()

    def __initialise(self):
        self.generate_maps_lists_per_dlc()
        self.populate_playlist()
        self.expandable_list_panel.scrollbar.set_scroll(0)

    def set_content_visibility(self, visible):
        super(MapsPanel, self).set_content_visibility(visible)
        if not SteamAmITheLobbyOwner():
            return
        if visible:
            self.__initialise()

    def generate_maps_lists_per_dlc(self):
        game_modes_string = SteamGetLobbyData(self.lobby_id, 'PLAYLIST')
        if self.ugc_mode and game_modes_string != 'ugc':
            game_modes_string = 'ugc'
        map_rotation_string = SteamGetLobbyData(self.lobby_id, 'MAP_ROTATION_FILENAME')
        game_modes = get_string_as_list(game_modes_string)
        self.original_maps = get_string_as_list(map_rotation_string)
        self.maps.clear()
        for id in A2665:
            self.maps[id] = {}

        self.maps['SAVED_MAPS'] = {}
        self.maps['SUBSCRIBED_MAPS'] = {}
        self.maps['TEMPLATES'] = {}
        for map_name, map_info in playlists.mapinfo.map_info.iteritems():
            valid_map = False
            for mode in game_modes:
                if mode == 'cctf':
                    test_mode = 'ctf'
                else:
                    test_mode = mode
                if test_mode not in map_info['invalid_modes']:
                    valid_map = True
                    break

            if valid_map:
                selected = map_name in self.original_maps
                if map_info['classic']:
                    self.maps['A2362'][map_name] = selected
                elif map_info['mafia']:
                    self.maps['MAFIA_PACK'][map_name] = selected
                elif 'Baseplate' in map_name:
                    self.maps['TEMPLATES'][map_name] = selected
                else:
                    self.maps['STANDARD'][map_name] = selected
            hosted_ugc_map_names = get_hosted_ugc_map_names()
            subscribed_ugc_map_names = get_subscribed_ugc_map_names()
            if not self.ugc_mode:
                for map_name in subscribed_ugc_map_names:
                    if A2450[game_modes[0]] not in get_available_game_modes(map_name, True) and not self.ugc_mode:
                        continue
                    selected = map_name in self.original_maps or map_name == self.manager.hosted_ugc_map_filename
                    self.maps['SUBSCRIBED_MAPS'][map_name] = selected

            for map_name in hosted_ugc_map_names:
                if map_name in subscribed_ugc_map_names:
                    continue
                if A2450[game_modes[0]] not in get_available_game_modes(map_name) and not self.ugc_mode:
                    continue
                selected = map_name in self.original_maps or map_name == self.manager.hosted_ugc_map_filename
                self.maps['SAVED_MAPS'][map_name] = selected

    def populate_playlist(self):
        self.expandable_list_panel.reset_list()
        row_name_to_select = None
        packs = [
         'SAVED_MAPS'] + ['SUBSCRIBED_MAPS'] + A2665 + ['TEMPLATES']
        current_map_selected = SteamGetLobbyData(self.lobby_id, 'MAP_ROTATION_FILENAME')
        for pack_name in packs:
            if pack_name not in self.maps.keys():
                continue
            maps = self.maps[pack_name]
            if (pack_name == 'SAVED_MAPS' or pack_name == 'SUBSCRIBED_MAPS') and len(maps) == 0:
                continue
            categoryItem = CategoryListItem(strings.get_by_id(pack_name), is_expandable=True, sub_row_colours=[ROW_GREY_COLOUR, ROW_DARK_GREY_COLOUR], sort_order=packs.index(pack_name))
            categoryItem.center_text = False
            available_map = True
            map_items = []
            custom_map = False
            author = ''
            for map_filename, selected in maps.iteritems():
                if pack_name == 'SAVED_MAPS':
                    data = get_ugc_data_from_file(map_filename)
                    if data is not None and 'title' in data:
                        display_map_name = data['title']
                        filename = map_filename
                        custom_map = True
                        if 'author' in data:
                            author = data['author']
                    else:
                        continue
                elif pack_name == 'SUBSCRIBED_MAPS':
                    get_ugc_data_from_file(map_filename)
                    display_map_name = SteamGetSubscribedContentTitle(map_filename)
                    filename = map_filename
                    custom_map = True
                    author = ''
                else:
                    filename = map_filename
                    display_map_name = map_filename
                    if pack_name == 'TEMPLATES':
                        custom_map = True
                        display_map_name = strings.get_by_id(map_filename)
                mapItem = OwnableItemBase(display_map_name, self.manager.dlc_manager, pack_name=pack_name, filename=filename, uid=map_filename, custom_map=custom_map, author=author)
                mapItem.center_text = False
                map_items.append(mapItem)

            self.expandable_list_panel.add_list_item(categoryItem, map_items)

        self.expandable_list_panel.on_scroll(0, silent=True)
        if current_map_selected is not None:
            row = self.expandable_list_panel.select_row_with_uid(current_map_selected)
            self.on_row_selected(0, row)
        return

    def on_row_selected(self, index, row):
        if row is None:
            print 'Chosen map row could not be selected'
            return
        else:
            if type(row) is CategoryListItem:
                return
            if not SteamAmITheLobbyOwner():
                return
            if row.filename is None or row.filename == '':
                map_rotation_name = row.name
            else:
                map_rotation_name = row.filename
            new_title = row.name
            SteamSetLobbyData('Custom_UGC_Map', str(row.custom_map))
            if row.custom_map:
                SteamSetLobbyData('Custom_UGC_Map_Author', row.author)
            else:
                SteamSetLobbyData('Custom_UGC_Map_Author', '')
            if len(self.maps['SAVED_MAPS']) + len(self.maps['SUBSCRIBED_MAPS']) > 0 or row.pack_name == 'TEMPLATES':
                if row.pack_name == 'SAVED_MAPS' or row.pack_name == 'SUBSCRIBED_MAPS':
                    self.manager.hosted_ugc_map_filename = map_rotation_name
                elif row.pack_name == 'TEMPLATES':
                    new_title = generate_ugc_map_title(row.name)
                    filename = generate_ugc_map_filename_from_lobby(self.lobby_id)
                    self.manager.hosted_ugc_map_filename = filename
                else:
                    new_title = row.name
            SteamSetLobbyData('MAP_ROTATION_ORIGINAL_TITLE', row.name)
            SteamSetLobbyData('MAP_ROTATION_FILENAME', map_rotation_name)
            SteamSetLobbyData('MAP_ROTATION_NEW_TITLE', new_title)
            return

    def draw(self):
        super(MapsPanel, self).draw()
