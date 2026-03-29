import time
from aoslib.scenes import MenuScene
from aoslib.text import welcome_font, START_FONT, split_text_to_fit_screen, ALDO_FONT, draw_text_with_alignment_and_size_validation, draw_text_within_boundaries
from aoslib.gui import TextButton, NavigationBar, Label, SquareButton, NAVBAR_LEFT, NAVBAR_MIDDLE, NAVBAR_RIGHT
from aoslib.images import global_images
from pyglet import gl
from aoslib import strings
from shared.steam import SteamShowAchievements, SteamActivateGameOverlayToStore, SteamIsDemoRunning, SteamCreateLobby, SteamAmITheLobbyOwner, SteamSetLobbyData, SteamGetPersonaName, SteamGetLobbyOwner, SteamIsLoggedOn, SteamClearRichPresence
from aoslib.media import HUD_AUDIO_ZONE
from shared.constants import *
from joiningGameMenu import JoiningGameMenu
from creditsMenu import CreditsMenu
from shared.hud_constants import MAIN_MENU_BOTTOM_BUTTON_Y_SPACE, MAIN_MENU_BUTTON_HEIGHT, MAIN_MENU_BUTTON_WIDTH, MAIN_MENU_BUTTON_FONT_SIZE, MAIN_MENU_SPACE_BETEWEEN_BUTTONS, MAIN_MENU_SPACE_BETWEEN_BUTTON_GROUPS, LIST_PANEL_SPACING
from shared.constants_matchmaking import A2664
from aoslib.scenes.main.matchSettings import get_default_playlist, reset_all_game_rules, get_default_match_length_for_playlist_in_minutes, DEFAULT_MATCH_SETTINGS
from shared.steam import game_version

class SelectMenu(MenuScene):

    def initialize(self):
        self.dlc_manager = self.manager.dlc_manager
        button_width = MAIN_MENU_BUTTON_WIDTH
        button_height = MAIN_MENU_BUTTON_HEIGHT
        y_pad = MAIN_MENU_SPACE_BETEWEEN_BUTTONS
        button_x = 800 / 2.0 - button_width / 2.0
        button_y = MAIN_MENU_BOTTOM_BUTTON_Y_SPACE + button_height
        font_size = MAIN_MENU_BUTTON_FONT_SIZE
        self.elements = []
        button_y += button_height
        noof_square_buttons = 4.0
        spacing = 2.0
        square_button_width = (button_width - (spacing * noof_square_buttons - 1.0)) / noof_square_buttons
        square_button_x = button_x + square_button_width / 2.0 - spacing
        square_button_y = button_y - square_button_width / 2.0 + spacing
        self.tutorial_button = SquareButton(global_images.tutorial_icon, square_button_x, square_button_y, square_button_width)
        self.tutorial_button.set_images(global_images.main_menu_button_square, global_images.main_menu_button_square_hover, global_images.main_menu_button_square_press, False)
        self.tutorial_button.add_handler(self.tutorial_pressed)
        self.elements.append(self.tutorial_button)
        square_button_x += spacing * 2 + square_button_width
        self.achievements_button = SquareButton(global_images.achievements_icon, square_button_x, square_button_y, square_button_width)
        self.achievements_button.set_images(global_images.main_menu_button_square, global_images.main_menu_button_square_hover, global_images.main_menu_button_square_press, False)
        self.achievements_button.add_handler(self.achievements_pressed)
        self.elements.append(self.achievements_button)
        square_button_x += spacing * 2 + square_button_width
        self.leaderboard_button = SquareButton(global_images.leaderboard_icon, square_button_x, square_button_y, square_button_width)
        self.leaderboard_button.set_images(global_images.main_menu_button_square, global_images.main_menu_button_square_hover, global_images.main_menu_button_square_press, False)
        self.leaderboard_button.add_handler(self.leaderboard_pressed)
        self.elements.append(self.leaderboard_button)
        square_button_x += spacing * 2 + square_button_width
        self.settings_button = SquareButton(global_images.options_icon, square_button_x, square_button_y, square_button_width)
        self.settings_button.set_images(global_images.main_menu_button_square, global_images.main_menu_button_square_hover, global_images.main_menu_button_square_press, False)
        self.settings_button.add_handler(self.settings_pressed)
        self.elements.append(self.settings_button)
        button_y += button_height + y_pad + MAIN_MENU_SPACE_BETWEEN_BUTTON_GROUPS
        self.user_content_button = TextButton(strings.UGC_MAIN_MENU_UGC_BUTTON, button_x, button_y, button_width, button_height, size=font_size)
        self.user_content_button.add_handler(self.user_content_pressed)
        self.elements.append(self.user_content_button)
        button_y += button_height + y_pad
        self.player_profile_button = TextButton(strings.PLAYER_PROFILE, button_x, button_y, button_width, button_height, size=font_size)
        self.player_profile_button.add_handler(self.player_profile_pressed)
        self.elements.append(self.player_profile_button)
        button_y += button_height + y_pad
        self.squad_play_button = TextButton(strings.CREATE_MATCH, button_x, button_y, button_width, button_height, size=font_size)
        self.squad_play_button.add_handler(self.squad_play_pressed)
        self.elements.append(self.squad_play_button)
        button_y += button_height + y_pad
        self.quick_play_button = TextButton(strings.JOIN_MATCH, button_x, button_y, button_width, button_height, size=font_size)
        self.quick_play_button.add_handler(self.quick_play_pressed)
        self.elements.append(self.quick_play_button)
        self.navigation_bar = NavigationBar(248, 32, 304, 26, False, False, False)
        self.navigation_bar.add_middle_button(strings.QUIT, global_images.quit_icon)
        self.navigation_bar.add_handler(self.navigation_button_pressed)
        self.elements.append(self.navigation_bar)
        self.dlc_buy_button = TextButton(strings.BUY_NOW, 40, 328, 160, 40, size=25)
        self.dlc_buy_button.add_handler(self.buy_pressed)
        self.dlc_buy_button.tint = (0.2, 1.0, 0.2)
        self.dlc_buy_button.text_colour = (255, 255, 255, 255)
        if strings.language == 'english':
            dlc_font_size = 12
        else:
            dlc_font_size = 11
        self.dlc_description = Label('', x=118, y=450, width=180, height=100, anchor_x='center', anchor_y='top', font_name=START_FONT, font_size=dlc_font_size, color=(255, 255, 255, 255))
        dlc_description_text = strings.get_by_id(strings.DLC_PACK_3_DESCRIPTION_1) + '\n'
        dlc_description_text += strings.get_by_id(strings.DLC_PACK_3_DESCRIPTION_2) + '\n'
        dlc_description_text += strings.get_by_id(strings.DLC_PACK_3_DESCRIPTION_3) + '\n'
        dlc_description_text += strings.get_by_id(strings.DLC_PACK_3_DESCRIPTION_4) + '\n'
        dlc_description_text += strings.get_by_id(strings.DLC_PACK_3_DESCRIPTION_5) + '\n'
        self.dlc_description.text = split_text_to_fit_screen(self.dlc_description.font, dlc_description_text, self.dlc_description.width, 0)
        self.game_buy_button = TextButton(strings.BUY_NOW, 620, 75, 120, 30, size=20)
        self.game_buy_button.add_handler(self.buy_game_pressed)
        self.game_buy_button.tint = (0.2, 1.0, 0.2)
        self.game_buy_button.text_colour = (255, 255, 255, 255)
        if strings.language == 'english':
            game_font_size = 11
        else:
            game_font_size = 10
        self.buy_game_title = Label(strings.GET_THE_FULL_GAME, font_name=ALDO_FONT, font_size=40, x=628, y=170, width=100, height=80, anchor_x='center', anchor_y='top', color=(255, 255, 255, 255))
        self.game_description = Label('', x=678, y=125, width=180, height=100, anchor_x='center', anchor_y='top', font_name=START_FONT, font_size=game_font_size, color=(255, 255, 255, 255))
        game_description_text = strings.get_by_id(strings.BUY_GAME_DESCRIPTION_1) + '\n'
        game_description_text += strings.get_by_id(strings.BUY_GAME_DESCRIPTION_2) + '\n'
        game_description_text += strings.get_by_id(strings.BUY_GAME_DESCRIPTION_3) + '\n'
        self.game_description.text = split_text_to_fit_screen(self.game_description.font, game_description_text, self.game_description.width, 0)
        self.showing_dlc_buy_button = False
        self.showing_game_buy_button = False
        if SteamIsDemoRunning():
            self.showing_game_buy_button = True
            self.elements.append(self.game_buy_button)
        elif not self.dlc_manager.is_installed_dlc('mafia'):
            self.showing_dlc_buy_button = True
            self.elements.append(self.dlc_buy_button)
        self.showing_error = False

    def on_start(self):
        self.update_active_buttons()
        if not self.media.is_playing_music('mainmenu'):
            self.media.play_music('mainmenu', self.config.music_volume)

    def update_active_buttons(self):
        from aoslib.gamemanager import GameManager
        if GameManager.invalid_data_error:
            if not self.showing_error:
                self.manager.set_big_text_message(A952, False, 600.0)
                self.tutorial_button.enabled = False
                self.achievements_button.enabled = False
                self.leaderboard_button.enabled = False
                self.settings_button.enabled = False
                self.user_content_button.enabled = False
                self.player_profile_button.enabled = False
                self.squad_play_button.enabled = False
                self.quick_play_button.enabled = False
                self.showing_error = True
        elif not SteamIsLoggedOn():
            if not self.showing_error:
                self.manager.set_big_text_message(A944, False, 600.0)
                self.tutorial_button.enabled = False
                self.achievements_button.enabled = False
                self.leaderboard_button.enabled = False
                self.settings_button.enabled = True
                self.user_content_button.enabled = False
                self.player_profile_button.enabled = False
                self.squad_play_button.enabled = False
                self.quick_play_button.enabled = False
                self.showing_error = True
        else:
            if self.showing_error:
                SteamClearRichPresence()
                self.manager.clear_big_text_message()
            self.tutorial_button.enabled = True
            self.achievements_button.enabled = True
            self.leaderboard_button.enabled = True
            self.settings_button.enabled = True
            self.user_content_button.enabled = True
            self.player_profile_button.enabled = True
            self.squad_play_button.enabled = True
            self.quick_play_button.enabled = True
            self.showing_error = False

    def on_stop(self):
        self.showing_error = False
        self.manager.clear_big_text_message()
        super(SelectMenu, self).on_stop()

    def close(self):
        self.manager.clear_big_text_message()
        self.media.stop_music(True)

    def update(self, dt):
        super(SelectMenu, self).update(dt)
        if self.showing_dlc_buy_button and self.dlc_manager.is_installed_dlc('mafia'):
            self.showing_dlc_buy_button = False
            self.elements.remove(self.dlc_buy_button)
        self.update_active_buttons()

    def draw(self):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        if self.showing_game_buy_button:
            gl.glColor4f(1.0, 1.0, 1.0, 1.0)
            if global_images.buy_game_background is not None:
                global_images.buy_game_background.blit(677, 170)
            self.game_description.draw()
            draw_text_within_boundaries(self.buy_game_title._text, self.buy_game_title.x, self.buy_game_title.y, self.buy_game_title.width, self.buy_game_title.height, self.buy_game_title.font, 5, self.buy_game_title.color, alignment='center')
        global_images.main_menu_frame.blit(400, 236)
        window = self.window
        welcome_text = strings.WELCOME + ' '
        username_text = self.config.name[0:32]
        text = welcome_text + username_text
        text_width = float(welcome_font.get_content_width(text))
        min_width = 86.0
        right_side = max(800.0, 600.0 * window.width / window.height)
        top_side = max(600.0, 800.0 * window.height / window.width)
        frame_width = float(global_images.name_frame.width + (text_width - min_width))
        frame_height = float(global_images.name_frame.height)
        x = right_side - frame_width - LIST_PANEL_SPACING - (right_side - 800.0) * 0.5
        y = top_side - frame_height - LIST_PANEL_SPACING - (top_side - 600.0) * 0.5
        scale_x = frame_width / global_images.name_frame.width
        gl.glPushMatrix()
        gl.glTranslatef(x, y, 0.0)
        gl.glScalef(scale_x, 1.0, 1.0)
        global_images.name_frame.blit(0, 0)
        gl.glPopMatrix()
        mid_x = x + text_width * 0.5 + 15
        mid_y = y + frame_height * 0.5 - 5
        welcome_font.draw_multi(((welcome_text, (255, 255, 255, 255)), (username_text, (34, 177, 76, 255))), mid_x, mid_y, True)
        if self.showing_dlc_buy_button:
            gl.glColor4f(1.0, 1.0, 1.0, 1.0)
            self.dlc_description.draw()
        for element in self.elements:
            element.draw()

        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        gl.glPushMatrix()
        gl.glTranslatef(412, 510, 0.0)
        gl.glScalef(0.75, 0.75, 1.0)
        global_images.splash_image.blit(0, 0)
        gl.glPopMatrix()

    def tutorial_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        self.manager.set_menu(JoiningGameMenu, config=self.config, in_game_menu=False, server_mode=A2389)

    def credits_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        self.parent.set_menu(CreditsMenu)

    def play_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        from serverMenu import ServerMenu
        self.parent.set_menu(ServerMenu)

    def quick_match_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        self.manager.set_menu(JoiningGameMenu, config=self.config, in_game_menu=False, server_mode=A2387)

    def quick_play_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        from aoslib.scenes.frontend.joinMatchMenu import JoinMatchMenu
        self.manager.set_menu(JoinMatchMenu, config=self.config, in_game_menu=False)

    def lobby_created_callback(self, lobby_id):
        if not SteamAmITheLobbyOwner():
            return
        SteamSetLobbyData('Name', SteamGetPersonaName())
        SteamSetLobbyData('Version', str(game_version()))
        SteamSetLobbyData('LobbyType', str(A2664))
        SteamSetLobbyData('LobbyCreator', str(SteamGetLobbyOwner()))
        default_playlist = get_default_playlist()
        if default_playlist is not None:
            game_rules = ''
            SteamSetLobbyData('PlaylistID', str(default_playlist.id))
            SteamSetLobbyData('PLAYLIST', str(default_playlist.modes[0]))
            SteamSetLobbyData('UGC_MODES', str([]))
            map_rotation_name = sorted(default_playlist.map_names)[0]
            SteamSetLobbyData('MAP_ROTATION_FILENAME', map_rotation_name)
            SteamSetLobbyData('MAP_ROTATION_ORIGINAL_TITLE', map_rotation_name)
            SteamSetLobbyData('MAP_ROTATION_NEW_TITLE', map_rotation_name)
            SteamSetLobbyData('Custom_UGC_Map', 'False')
            teams = ['TEAM1', 'TEAM2']
            for team in teams:
                SteamSetLobbyData(team, '0')

            SteamSetLobbyData('TEAM_NEUTRAL', '1')
            reset_all_game_rules()
        default_match_length = get_default_match_length_for_playlist_in_minutes(default_playlist.id)
        SteamSetLobbyData('MATCH_LENGTH', str(default_match_length))
        SteamSetLobbyData('MAX_PLAYERS', DEFAULT_MATCH_SETTINGS['MAX_PLAYERS'])
        self.manager.hosted_ugc_map_filename = ''
        from aoslib.scenes.frontend.matchSquadLobbyMenu import MatchSquadLobbyMenu
        self.parent.set_menu(MatchSquadLobbyMenu)

    def lobby_create_error_callback(self, reason):
        self.manager.set_big_text_message(A968, False, 5.0)

    def squad_play_pressed(self):
        self.media.stop_sounds()
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        SteamCreateLobby(self.lobby_created_callback, self.lobby_create_error_callback)

    def ranked_match_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        self.manager.set_menu(JoiningGameMenu, config=self.config, in_game_menu=False, server_mode=A2388)

    def player_profile_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        from playerProfileMenu import PlayerProfileMenu
        self.parent.set_menu(PlayerProfileMenu)

    def user_content_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        from aoslib.scenes.frontend.ugcSelectMenu import UGCSelectMenu
        self.manager.set_menu(UGCSelectMenu)

    def achievements_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        if not SteamShowAchievements():
            pass

    def leaderboard_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        from LeaderboardMenu import LeaderboardMenu
        self.parent.set_menu(LeaderboardMenu)

    def settings_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        from settingsMenu import SettingsMenu
        self.parent.set_menu(SettingsMenu)

    def buy_pressed(self):
        self.media.play('menu_buyA', zone=HUD_AUDIO_ZONE)
        SteamActivateGameOverlayToStore(DLC_APPID_LIST['mafia'])

    def buy_game_pressed(self):
        self.media.play('menu_buyA', zone=HUD_AUDIO_ZONE)
        SteamActivateGameOverlayToStore(A0)

    def navigation_button_pressed(self, navigation_button):
        if navigation_button == NAVBAR_LEFT or navigation_button == NAVBAR_MIDDLE:
            self.manager.close_window()
        elif navigation_button == NAVBAR_RIGHT:
            self.credits_pressed()
