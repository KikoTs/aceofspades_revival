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

class UGCSelectMenu(MenuScene):

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
            self.manager.set_big_text_message(ERROR_DATA, False, 600.0)
        button_y += button_height - 1
        self.map_editor_subscribe_button = TextButton(strings.UGC_MENU_SUBSCRIBE, button_x, button_y, button_width, button_height, size=font_size)
        self.map_editor_subscribe_button.add_handler(self.map_editor_subscribe)
        self.elements.append(self.map_editor_subscribe_button)
        if GameManager.invalid_data_error:
            self.map_editor_subscribe_button.enabled = False
        button_y += button_height + y_pad
        self.map_editor_lobbies_button = TextButton(strings.UGC_MENU_PUBLISH_MAP, button_x, button_y, button_width, button_height, size=font_size)
        self.map_editor_lobbies_button.add_handler(self.map_editor_publish_map)
        self.elements.append(self.map_editor_lobbies_button)
        if GameManager.invalid_data_error:
            self.map_editor_lobbies_button.enabled = False
        button_y += button_height + y_pad
        self.publish_map_button = TextButton(strings.UGC_MENU_MAP_EDITOR, button_x, button_y, button_width, button_height, size=font_size)
        self.publish_map_button.add_handler(self.map_editor_lobbies_pressed)
        self.elements.append(self.publish_map_button)
        if GameManager.invalid_data_error:
            self.publish_map_button.enabled = False
        self.navigation_bar = NavigationBar(248, 32, 304, 26, False, False, False)
        self.navigation_bar.add_left_button()
        self.navigation_bar.add_handler(self.navigation_button_pressed)
        self.elements.append(self.navigation_bar)

    def on_start(self):
        if not self.media.is_playing_music('mainmenu'):
            self.media.play_music('mainmenu', self.config.music_volume)

    def close(self):
        self.media.stop_music(True)

    def update(self, dt):
        super(UGCSelectMenu, self).update(dt)

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

    def map_editor_lobbies_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        from aoslib.scenes.frontend.ugcSquadsMenu import UGCSquadsMenu
        self.manager.set_menu(UGCSquadsMenu, config=self.config, in_game_menu=False)

    def map_editor_subscribe(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        from shared.steam import SteamShowWebPage
        url = 'http://steamcommunity.com/workshop/browse/?appid=' + str(SPADES_GAME_APP_ID)
        SteamShowWebPage(url)

    def map_editor_publish_map(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        from aoslib.scenes.frontend.ugcPublishMenu import UGCPublishMenu
        self.manager.set_menu(UGCPublishMenu, config=self.config, in_game_menu=False)

    def navigation_button_pressed(self, navigation_button):
        self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
        from selectMenu import SelectMenu
        self.parent.set_menu(SelectMenu, back=True)
