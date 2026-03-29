from aoslib.scenes.main.listPanelItemBase import ListPanelItemBase
from aoslib.scenes.gui.dropBoxControl import DropBoxControl
from aoslib.gui import TextButton
from aoslib import strings
from aoslib.text import draw_text_with_alignment_and_size_validation, modify_name_to_fix_width
from pyglet import gl
from shared.constants import MENU_FONT_COLOR, TEAM_COLOURS, TEAM1, TEAM2, TEAM_NEUTRAL
from shared.constants_matchmaking import *
from aoslib.gui import SquareButton
from aoslib.images import global_images
from shared.steam import SteamGetPersonaName, SteamGetLobbyMemberName
from aoslib.common import tint_colour, to_float_color_alpha
from shared.hud_constants import TEXT_BACKGROUND_SPACING, ROW_TINT_DARK_GREY_COLOUR, ROW_TINT_LIGHT_GREY_COLOUR, ROW_DARK_GREY_COLOUR
import time
TEAM_FONT_COLOURS = {TEAM1: (81, 171, 255, 255), 
   TEAM2: (174, 255, 2, 255), 
   TEAM_NEUTRAL: MENU_FONT_COLOR}
LIST_ITEM_TEXT_AREA = 120
LIST_ITEM_ICON_AREA = 15
LIST_ITEM_DROPDOWN_AREA = 100
LIST_ITEM_IN_GAME_TEXT_AREA = 42
LIST_ITEM_SPACING = 7
UNKNOWN_NAME_UPDATE_TIME = 2.0

class SquadFriendListItem(ListPanelItemBase):
    kick_button = None
    is_in_game = False

    def initialize(self, manager, id, name, team_id, drop_box_options=[], initial_option_index=0, is_leader=False, show_host_options=False, show_kick_button=False, is_in_game=False, player_connection=None, show_ping=False, player_client_id=-1, profanity_manager=None):
        super(SquadFriendListItem, self).initialize()
        self.id = id
        self.name = profanity_manager.sanitise_string(name)
        self.update_name_needed = self.name == '[unknown]' or len(self.name) < 1
        self.name_update_timer = time.time()
        self.__team_id = team_id
        self.is_ready = False
        self.is_leader = is_leader
        self.is_in_game = is_in_game
        self.local_player_name = SteamGetPersonaName()
        self.name_x = 0
        self.name_width = 0
        self.drop_box_area = 0
        self.drop_box_area_x = 0
        self.icon_x = 0
        self.icon_area = 0
        self.in_game_text_x = 0
        self.in_game_text_area = 0
        self.on_drop_box_option_changed_callback = None
        self.on_kick_button_selected_callback = None
        self.show_host_options = show_host_options
        self.show_kick_button = show_kick_button
        self.manager = manager
        self.silent_control = True
        self.show_ping = show_ping
        self.player_client_id = player_client_id
        if self.player_client_id == -1:
            self.show_ping = False
        if drop_box_options is None:
            drop_box_options = []
        self.drop_box_control = DropBoxControl(manager, drop_box_options, initial_option_index, 0, 0, 100, 20, len(drop_box_options))
        self.drop_box_control.add_handler(self.on_drop_box_option_changed)
        self.elements.append(self.drop_box_control)
        self.drop_box_control.set_enabled(self.show_host_options)
        self.kick_button_control = TextButton(strings.KICK_PLAYER, 0, 0, 100, 20, 18)
        self.kick_button_control.add_handler(self.on_kick_button_selected)
        self.elements.append(self.kick_button_control)
        self.kick_button_control.set_enabled(self.show_kick_button)
        self.kick_button_control.set_visible(self.show_kick_button)
        return

    def set_team_id(self, new_team_id):
        self.__team_id = new_team_id

    def set_dropdown_box_options(self, options, selected_index=-1):
        self.drop_box_control.update_rows(options, selected_index)

    def set_show_host_options(self, show_host_options):
        self.show_host_options = show_host_options
        self.drop_box_control.set_enabled(self.show_host_options)

    def set_show_kick_button(self, show_kick_button):
        self.show_kick_button = show_kick_button
        self.kick_button_control.set_enabled(self.show_kick_button)
        self.kick_button_control.set_visible(self.show_kick_button)

    def get_team_id(self):
        return self.__team_id

    def set_hovered(self, hovered):
        pass

    def set_selected(self, selected, media):
        pass

    def on_mouse_motion(self, x, y, dx, dy):
        pass

    def on_mouse_release(self, x, y, button, modifiers):
        pass

    def on_drop_box_option_changed(self, index):
        if self.on_drop_box_option_changed_callback:
            self.on_drop_box_option_changed_callback(self.drop_box_control.get_row_value_for_index(index), self)

    def on_kick_button_selected(self):
        if self.on_kick_button_selected_callback:
            self.on_kick_button_selected_callback(self)

    def mouse_collides(self, x, y):
        if super(SquadFriendListItem, self).mouse_collides(x, y):
            return True
        else:
            if self.drop_box_control is not None and self.drop_box_control.selected == True:
                for row in self.drop_box_control.list_panel.rows:
                    if row.mouse_collides(x, y):
                        return True

            return False

    def update_position(self, x, y, width, height, highlight_width):
        super(SquadFriendListItem, self).update_position(x, y, width, height, highlight_width)
        text_spacing = LIST_ITEM_SPACING
        self.icon_area = LIST_ITEM_ICON_AREA
        self.in_game_text_area = LIST_ITEM_IN_GAME_TEXT_AREA
        self.drop_box_area = LIST_ITEM_DROPDOWN_AREA
        self.name_width = LIST_ITEM_TEXT_AREA
        self.name_x = self.x1 + TEXT_BACKGROUND_SPACING
        self.icon_x = self.name_x + self.name_width + text_spacing
        self.in_game_text_x = self.icon_x + self.icon_area + text_spacing
        self.drop_box_area_x = self.x2 - 9 - self.drop_box_area
        if self.drop_box_control is not None:
            box_height = 20
            y = self.y1 + self.height / 2.0 - box_height / 2.0
            self.drop_box_control.update_position(self.drop_box_area_x, y, self.drop_box_area, box_height)
        if self.kick_button_control is not None:
            self.kick_button_control.x = self.drop_box_area_x
            self.kick_button_control.y = self.y2 - self.height / 2.0 + self.kick_button_control.height / 2.0
            self.kick_button_control.width = self.drop_box_area
        if self.kick_button_control is not None:
            self.kick_button_control.x = self.drop_box_area_x
            self.kick_button_control.y = self.y2 - self.height / 2.0 + self.kick_button_control.height / 2.0
            self.kick_button_control.width = self.drop_box_area
        return

    def update_name(self):
        if self.update_name_needed:
            current_time = time.time()
            if current_time - self.name_update_timer > UNKNOWN_NAME_UPDATE_TIME:
                self.name = SteamGetLobbyMemberName(self.id)
                self.update_name_needed = self.name == '[unknown]' or len(self.name) < 1
                self.name_update_timer = current_time

    def draw_name(self):
        self.update_name()
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        colour = A2707
        if self.is_leader and not self.is_in_game:
            colour = A2704
        if self.is_in_game:
            draw_text_with_alignment_and_size_validation('[' + strings.IN_GAME + ']', self.in_game_text_x, self.y1, self.in_game_text_area, self.height, colour, self.font, alignment_x='left', alignment_y='center')
        team_id = self.get_team_id()
        if team_id in TEAM_FONT_COLOURS:
            colour = TEAM_FONT_COLOURS[team_id]
        else:
            colour = MENU_FONT_COLOR
        text = modify_name_to_fix_width(self.name, self.name_width, self.font)
        draw_text_with_alignment_and_size_validation(text, self.name_x, self.y1, self.name_width, self.height, colour, self.font, alignment_x='left', alignment_y='center')
        if self.drop_box_control is not None:
            self.drop_box_control.title_bar.text_colour = colour
        if self.show_ping:
            if self.player_client_id in self.manager.game_scene.players:
                ping = self.manager.game_scene.players[self.player_client_id].ping
                ping_x = self.x1 + self.width - TEXT_BACKGROUND_SPACING - self.name_width
                ping_text = strings.PING + ': ' + str(ping)
                draw_text_with_alignment_and_size_validation(ping_text, ping_x, self.y1, self.name_width, self.height, colour, self.font, alignment_x='right', alignment_y='center')
        if self.is_leader:
            scale_x = self.icon_area / float(global_images.host_icon.width)
            scale_y = self.icon_area / float(global_images.host_icon.height)
            x = self.icon_x + self.icon_area / 2 + global_images.host_icon.width * scale_x
            y = self.y1 + self.height / 2
            if not self.show_host_options and not self.show_ping:
                x = self.x1 + self.width - TEXT_BACKGROUND_SPACING - global_images.host_icon.width * scale_x
            gl.glColor4f(1.0, 1.0, 1.0, 1.0)
            gl.glPushMatrix()
            gl.glTranslatef(x, y, 0)
            gl.glScalef(scale_x, scale_y, 0.0)
            global_images.host_icon.blit(0, 0)
            gl.glPopMatrix()
        return

    def draw_elements(self):
        pass

    def draw(self, colour):
        if self.__team_id == TEAM_NEUTRAL:
            team_colour = colour
        else:
            if colour == ROW_DARK_GREY_COLOUR:
                colour = ROW_TINT_DARK_GREY_COLOUR
            else:
                colour = ROW_TINT_LIGHT_GREY_COLOUR
            team_colour = TEAM_COLOURS[self.__team_id] + (255, )
            team_colour = tint_colour(colour, to_float_color_alpha(team_colour))
        super(SquadFriendListItem, self).draw(team_colour)
