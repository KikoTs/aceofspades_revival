import time
from aoslib.scenes import MenuScene
from aoslib.text import welcome_font, START_FONT, split_text_to_fit_screen
from aoslib.gui import TextButton, NavigationBar, Label, SquareButton, NAVBAR_LEFT, NAVBAR_RIGHT

from aoslib.scenes.gui.editBoxControl import EditBoxControl
from aoslib.text import split_text_to_fit_screen, chat_font, chat_font_tuffy, input_ip, draw_text_with_size_validation

from aoslib.images import global_images
from pyglet import gl
from aoslib import strings
from shared.steam import SteamShowAchievements, SteamActivateGameOverlayToStore
from aoslib.media import HUD_AUDIO_ZONE
from shared.constants import *
from joiningGameMenu import JoiningGameMenu
from creditsMenu import CreditsMenu
from shared.hud_constants import MAIN_MENU_BOTTOM_BUTTON_Y_SPACE, MAIN_MENU_BUTTON_HEIGHT, MAIN_MENU_BUTTON_WIDTH, MAIN_MENU_BUTTON_FONT_SIZE, MAIN_MENU_SPACE_BETEWEEN_BUTTONS, MAIN_MENU_SPACE_BETWEEN_BUTTON_GROUPS

class InputServer(MenuScene):

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
        self.quick_match_button = TextButton(strings.CONNECT, button_x, button_y, button_width, button_height, size=font_size)
        self.quick_match_button.add_handler(self.connect_to_srv)
        self.elements.append(self.quick_match_button)

        self.input_adr = EditBoxControl('', 267, 325, 270, 100, center=False, empty_text="IP:PORT", draw_background=True, return_on_focus_loss=False)
        self.input_adr.on_return_callback = self.connect_to_srv
        self.input_adr.font = input_ip
        self.input_adr.allow_over_typing = True
        self.elements.append(self.input_adr)

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
        super(InputServer, self).update(dt)

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

    def navigation_button_pressed(self, navigation_button):
        self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
        from aoslib.scenes.frontend.joinMatchMenu import JoinMatchMenu
        self.manager.set_menu(JoinMatchMenu, config=self.config, in_game_menu=False)

    def connect_to_srv(self, from_game=False, address=None):
        identifier = self.input_adr.text
        if identifier == '':
            return
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        if identifier == 'local':
            identifier = '127.0.0.1:32887'

        from aoslib.scenes.ingame_menus.loadingMenu import LoadingMenu
        self.manager.set_menu(LoadingMenu, identifier=identifier, from_server_menu=True)