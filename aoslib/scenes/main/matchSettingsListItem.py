from aoslib.scenes.main.listPanelItemBase import ListPanelItemBase
from aoslib.images import global_images
from shared.constants import MENU_FONT_COLOR
from aoslib.text import draw_text_with_alignment_and_size_validation, medium_edo_ui_font
from aoslib.gui import SliderOption
from aoslib.scenes.gui.menuOptionControl import MenuOptionControl
from aoslib.scenes.main.matchSettings import get_list_items_as_string, get_default_settings_value, get_display_name, get_default_playlist, reset_all_game_rules, get_playlist_with_mode, get_game_mode_names
from aoslib import strings
from pyglet import gl
from shared.steam import SteamSetLobbyData, SteamGetLobbyData
from shared.constants_matchmaking import *
from shared.hud_constants import UI_CONTROL_GREY_BACKGROUND_COLOUR, MATCH_SETTINGS_ROW_COLOUR, UI_CONTROL_SPACING, TEXT_BACKGROUND_SPACING
from aoslib.scenes.main.matchSettings import generate_ugc_map_filename_from_lobby, generate_ugc_map_title
from shared.constants_matchmaking import A2663, A2664

class MatchSettingsListItem(ListPanelItemBase):

    def initialize(self, display_name, settings_id, lobby_id):
        super(MatchSettingsListItem, self).initialize()
        self.lobby_id = lobby_id
        self.settings_id = settings_id
        self.name = display_name
        self.name_width = 0
        self.pad_x = 0
        self.pad_y = 0
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.current_value = SteamGetLobbyData(self.lobby_id, self.settings_id)
        self.selectable_row = False

    def on_value_changed(self):
        pass

    def draw_selection_highlight(self):
        pass

    def draw_hovered_highlight(self):
        pass

    def draw_background(self, colour):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        gl.glPushMatrix()
        gl.glTranslatef(self.x1 + self.width / 2, self.y1 + self.height / 2, 0)
        gl.glScalef(self.scale_x, self.scale_y, 0.0)
        global_images.settings_matchsettings_frame.blit(0, 0)
        gl.glPopMatrix()

    def reset(self):
        pass

    def update_position(self, x, y, width, height, highlight_width):
        super(MatchSettingsListItem, self).update_position(x, y, width, height, highlight_width)
        self.name_width = self.width / 3
        height = self.height - UI_CONTROL_SPACING * 2
        width = self.width - TEXT_BACKGROUND_SPACING * 3 - self.name_width
        x = self.x1 + TEXT_BACKGROUND_SPACING + self.name_width + TEXT_BACKGROUND_SPACING
        y = self.y1 + UI_CONTROL_SPACING
        self.control.update_position(x, y, width, height)
        self.scale_x = float(self.width) / float(global_images.settings_matchsettings_frame.width)
        self.scale_y = float(self.height) / float(global_images.settings_matchsettings_frame.height)

    def draw_name(self):
        if self.name is not None and self.name_width > 0:
            draw_text_with_alignment_and_size_validation(self.name, self.x1 + TEXT_BACKGROUND_SPACING, self.y1, self.name_width, self.height, MENU_FONT_COLOR, medium_edo_ui_font, alignment_x='center', alignment_y='center')
        return


class MatchSettingsSliderListItem(MatchSettingsListItem):

    def initialize(self, display_name, settings_id, lobby_id, items, on_value_changed_callback=None, media=None, set_as_index=False):
        super(MatchSettingsSliderListItem, self).initialize(display_name, settings_id, lobby_id)
        self.set_as_index = set_as_index
        self.on_value_changed_callback = on_value_changed_callback
        if self.current_value == '':
            self.set_default_value()
        initial_index = -1
        for index, item in enumerate(items):
            value = str(index) if self.set_as_index else item
            if value == self.current_value:
                initial_index = index
                break

        self.control = SliderOption(initial_index, items, self.x1, self.y1, self.width, self.height, media=media)
        self.control.add_handler(self.on_value_changed, self.settings_id)
        self.elements.append(self.control)

    def get_item_index(self, items, value):
        for index, item in enumerate(items):
            if item == value:
                return index

        return 0

    def on_value_changed(self, index, value, settings_id):
        if self.set_as_index:
            self.current_value = str(index)
        else:
            self.current_value = value
        SteamSetLobbyData(self.settings_id, self.current_value)
        if self.on_value_changed_callback is not None:
            self.on_value_changed_callback(self.current_value)
        return

    def set_default_value(self):
        self.current_value = get_default_settings_value(self.settings_id)
        if self.set_as_index:
            self.current_value = str(self.current_value)
        SteamSetLobbyData(self.settings_id, self.current_value)
        if self.on_value_changed_callback is not None:
            self.on_value_changed_callback(self.current_value)
        return

    def reset(self):
        self.set_default_value()
        if self.set_as_index:
            index = int(self.current_value)
        else:
            index = self.control.get_index_by_name(self.current_value)
        self.control.set(index)


class MatchSettingsMenuListItem(MatchSettingsListItem):

    def initialize(self, display_name, settings_id, lobby_id, on_button_clicked, default_text=strings.DEFAULT):
        super(MatchSettingsMenuListItem, self).initialize(display_name, settings_id, lobby_id)
        self.default_text = default_text
        self.control = MenuOptionControl(self.default_text, self.x1, self.y1, self.width, self.height, on_button_clicked, background_colour=UI_CONTROL_GREY_BACKGROUND_COLOUR)
        self.elements.append(self.control)

    def reset(self):
        lobby_type = SteamGetLobbyData(self.lobby_id, 'LobbyType')
        if self.settings_id == 'PLAYLIST' and lobby_type == str(A2664):
            default_playlist = get_default_playlist()
            if default_playlist is not None:
                SteamSetLobbyData('PlaylistID', str(default_playlist.id))
                SteamSetLobbyData('PLAYLIST', default_playlist.modes[0])
            self.current_value = get_display_name(self.settings_id, self.lobby_id)
            self.control.name = self.current_value
            return
        else:
            if self.settings_id == 'PLAYLIST' and lobby_type == str(A2663):
                return
            if self.settings_id == 'UGC_MODES' and lobby_type == str(A2663):
                playlist = get_playlist_with_mode('ugc')
                if playlist is not None:
                    SteamSetLobbyData('PlaylistID', str(playlist.id))
                    names = get_game_mode_names(playlist.ugc_modes)
                    if len(names) > 0:
                        self.current_value = names[0]
                        self.control.name = names[0]
                        SteamSetLobbyData('UGC_MODES', playlist.ugc_modes[0])
                        return
                self.current_value = strings.DEFAULT
                self.control.name = self.current_value
                return
            if self.settings_id == 'UGC_MODES' and lobby_type == str(A2664):
                return
            if self.settings_id == 'GAME_RULES':
                reset_all_game_rules()
                self.control.name = get_display_name(self.settings_id, self.lobby_id)
                return
            if self.settings_id == 'MAP_ROTATION_FILENAME':
                if SteamGetLobbyData(self.lobby_id, 'LobbyType') == str(A2664):
                    self.current_value = get_default_settings_value(self.settings_id)
                    self.control.name = self.current_value
                    SteamSetLobbyData('MAP_ROTATION_ORIGINAL_TITLE', self.current_value)
                    SteamSetLobbyData('MAP_ROTATION_FILENAME', self.current_value)
                    SteamSetLobbyData('MAP_ROTATION_NEW_TITLE', self.current_value)
                elif SteamGetLobbyData(self.lobby_id, 'LobbyType') == str(A2663):
                    playlist = get_playlist_with_mode('ugc')
                    if playlist is not None and len(playlist.map_names) > 0:
                        map_rotation = sorted(playlist.map_names)[0]
                        map_name = strings.get_by_id(map_rotation)
                        new_title = generate_ugc_map_title(map_name)
                        SteamSetLobbyData('MAP_ROTATION_ORIGINAL_TITLE', map_name)
                        SteamSetLobbyData('MAP_ROTATION_FILENAME', map_rotation)
                        SteamSetLobbyData('MAP_ROTATION_NEW_TITLE', new_title)
                    else:
                        map_name = strings.DEFAULT
                    self.current_value = map_name
                    self.control.name = map_name
                return
            if self.settings_id == 'PREFAB_SET':
                self.current_value = get_default_settings_value(self.settings_id)
            else:
                self.current_value = get_default_settings_value(self.settings_id)
            current_value_string = get_list_items_as_string(self.current_value)
            SteamSetLobbyData(self.settings_id, current_value_string)
            self.control.name = get_display_name(self.settings_id, self.lobby_id)
            return
