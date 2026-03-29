import time
from aoslib.scenes import MenuScene
from aoslib.text import welcome_font, START_FONT, split_text_to_fit_screen
from aoslib.gui import TextButton, NavigationBar, Label, SquareButton, NAVBAR_LEFT, NAVBAR_RIGHT
from aoslib.images import global_images
from pyglet import gl
from aoslib import strings
from shared.steam import SteamShowAchievements, SteamActivateGameOverlayToStore
from aoslib.media import HUD_AUDIO_ZONE
from shared.constants import *
from joiningGameMenu import JoiningGameMenu
from creditsMenu import CreditsMenu
from shared.hud_constants import MAIN_MENU_BOTTOM_BUTTON_Y_SPACE, MAIN_MENU_BUTTON_HEIGHT, MAIN_MENU_BUTTON_WIDTH, MAIN_MENU_BUTTON_FONT_SIZE, MAIN_MENU_SPACE_BETEWEEN_BUTTONS, MAIN_MENU_SPACE_BETWEEN_BUTTON_GROUPS

class JoinMatchMenu(MenuScene):

    def initialize(self):
        self.bottom_frame_pos_y = 270 - MAIN_MENU_BUTTON_HEIGHT + MAIN_MENU_SPACE_BETEWEEN_BUTTONS
        button_width = MAIN_MENU_BUTTON_WIDTH
        button_height = MAIN_MENU_BUTTON_HEIGHT
        y_pad = MAIN_MENU_SPACE_BETEWEEN_BUTTONS
        button_x = 800 / 2.0 - button_width / 2.0
        button_y = self.bottom_frame_pos_y + MAIN_MENU_BUTTON_HEIGHT * 0.5 + MAIN_MENU_SPACE_BETEWEEN_BUTTONS
        font_size = MAIN_MENU_BUTTON_FONT_SIZE
        self.elements = []
        from aoslib.gamemanager import GameManager
        if GameManager.invalid_data_error:
            self.manager.set_big_text_message(A952, False, 600.0)
        button_y += button_height - 1
        self.quick_match_button = TextButton(strings.PUBLIC_MATCH, button_x, button_y, button_width, button_height, size=font_size)
        self.quick_match_button.add_handler(self.quick_match_pressed)
        self.elements.append(self.quick_match_button)
        if GameManager.invalid_data_error:
            self.quick_match_button.enabled = False
        button_y += button_height + y_pad
        self.join_match_button = TextButton(strings.BUTTON_CONNECT_IP, button_x, button_y, button_width, button_height, size=font_size)
        self.join_match_button.add_handler(self.join_match_pressed)
        self.elements.append(self.join_match_button)
        if GameManager.invalid_data_error:
            self.join_match_button.enabled = False
        button_y += button_height + y_pad
        self.server_browser_button = TextButton(strings.SERVER_BROWSER, button_x, button_y, button_width, button_height, size=font_size)
        self.server_browser_button.add_handler(self.server_browser_pressed)
        self.elements.append(self.server_browser_button)
        if GameManager.invalid_data_error:
            self.server_browser_button.enabled = False
        self.navigation_bar = NavigationBar(248, 32, 304, 26, False, False, False)
        self.navigation_bar.add_left_button()
        self.navigation_bar.add_handler(self.navigation_button_pressed)
        self.elements.append(self.navigation_bar)

    def on_start(self, *arg, **kw):
        if not self.media.is_playing_music('mainmenu'):
            self.media.play_music('mainmenu', self.config.music_volume)

    def close(self):
        self.media.stop_music(True)

    def update(self, dt):
        super(JoinMatchMenu, self).update(dt)

    def draw(self):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        global_images.frame_3button_menu.blit(400, self.bottom_frame_pos_y + global_images.frame_3button_menu.height * 0.5)
        global_images.frame_nav_bar_small.blit(400, 46)
        for element in self.elements:
            element.draw()

        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        gl.glPushMatrix()
        gl.glTranslatef(412, 510, 0.0)
        gl.glScalef(0.75, 0.75, 1.0)
        global_images.splash_image.blit(0, 0)
        gl.glPopMatrix()

    def server_browser_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        from aoslib.scenes.frontend.serverMenu import ServerMenu
        self.manager.set_menu(ServerMenu, config=self.config, in_game_menu=False)

    def quick_match_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        from aoslib.scenes.frontend.quickPlayMenu import QuickPlayMenu
        self.manager.set_menu(QuickPlayMenu, config=self.config, in_game_menu=False)

    def join_match_pressed(self):
        #self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        #from aoslib.scenes.frontend.matchSquadsMenu import MatchSquadsMenu
        #self.manager.set_menu(MatchSquadsMenu, config=self.config, in_game_menu=False)
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        from aoslib.scenes.frontend.InputServer import InputServer
        self.manager.set_menu(InputServer, config=self.config, in_game_menu=False)

    def navigation_button_pressed(self, navigation_button):
        self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
        from selectMenu import SelectMenu
        self.parent.set_menu(SelectMenu, back=True)
