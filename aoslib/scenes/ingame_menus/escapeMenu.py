# uncompyle6 version 3.9.2
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.12.0 (tags/v3.12.0:0fb18b0, Oct  2 2023, 13:03:39) [MSC v.1935 64 bit (AMD64)]
# Embedded file name: C:\TeamCity\buildAgent\work\dc8eb0b1d2cf198a\Main\client\standalone\build\pyi.win32\run_obfuscated\out00-PYZ.pyz\aoslib.scenes.ingame_menus.escapeMenu
from aoslib.scenes import MenuScene, ElementScene
from aoslib.gui import TextButton
from aoslib.images import global_images
from aoslib.text import title_font
from pyglet.window import key
from pyglet import gl
from shared.constants import A1054, A2437, A2445, A2442, A554, A79, A516, A517, A518, A515, A84, A85
from aoslib import strings
from aoslib.media import HUD_AUDIO_ZONE
from aoslib.hud.hud import ViewGameStats
from aoslib.scenes.gui.messageBox import *
import local_host
MESSAGE_SAVE_BEFORE_QUIT, MESSAGE_ON_SAVE, MESSAGE_QUIT_AFTER_SAVE = xrange(3)

class EscapeMenu(MenuScene):
    title = strings.PAUSE
    clears_scene_lock = False

    def initialize(self):
        button_width = 265
        button_height = 55
        y_pad = 7
        button_x = 400 - button_width / 2.0
        button_y = 125 + button_height
        button_size = 30
        self.message_box = MessageBox(400, 300)
        self.message_box.set_buttons_callback(self.message_box_button_one_pressed, self.message_box_button_two_pressed)
        self.is_ugc_host = False
        self.message_id = None
        self.disconnect_button = TextButton(strings.DISCONNECT, button_x, button_y, button_width, button_height, button_size)
        self.disconnect_button.add_handler(self.disconnect_button_pressed)
        y = button_y - y_pad - button_height
        self.quit_button = TextButton(strings.QUIT, button_x, y, button_width, button_height, button_size)
        self.quit_button.add_handler(self.on_quit_button_pressed)
        self.save_button = TextButton(strings.SAVE, button_x, button_y, button_width, button_height, button_size)
        self.save_button.add_handler(self.save_button_pressed)
        button_y += button_height + y_pad
        self.settings_button = TextButton(strings.SETTINGS, button_x, button_y, button_width, button_height, button_size)
        self.settings_button.add_handler(self.settings_button_pressed)
        button_y += button_height + y_pad
        self.change_team_button = TextButton(strings.CHANGE_TEAM, button_x, button_y, button_width, button_height, button_size)
        self.change_team_button.add_handler(self.change_team_button_pressed)
        self.game_data_button = TextButton(strings.UGC_GAME_DATA, button_x, button_y, button_width, button_height, button_size)
        self.game_data_button.add_handler(self.game_data_button_pressed)
        button_y += button_height + y_pad
        self.change_class_button = TextButton(strings.CHANGE_CLASS, button_x, button_y, button_width, button_height, button_size)
        self.change_class_button.add_handler(self.change_class_button_pressed)
        self.constructs_button = TextButton(strings.UGC_CONSTRUCTS, button_x, button_y, button_width, button_height, button_size)
        self.constructs_button.add_handler(self.constructs_button_pressed)
        button_y += button_height + y_pad
        self.resume_button = TextButton(strings.RESUME, button_x, button_y, button_width, button_height, button_size)
        self.resume_button.add_handler(self.resume_button_pressed)
        self.elements = [
         self.disconnect_button, self.quit_button, self.save_button, self.settings_button, self.change_team_button, self.change_class_button, self.constructs_button, self.game_data_button, self.resume_button, self.message_box]
        return

    def on_start(self, *arg, **kw):
        super(EscapeMenu, self).on_start(*arg, **kw)
        self.setup_correct_buttons()
        self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
        self.hide_message_box()

    def setup_correct_buttons(self):
        game_scene = self.manager.game_scene
        # Dedicated Map Creator sockets must stay UGC CLIENT on packet 114 or
        # retail enters a Steam-lobby loading branch and crashes.  Local menu
        # ownership is therefore a separate, process-scoped capability.
        self.is_ugc_host = (
            game_scene.is_ugc_host()
            or local_host.is_local_ugc_host(self.manager)
        )
        self.save_button.enabled = self.is_ugc_host
        self.disconnect_button.enabled = not self.is_ugc_host
        self.quit_button.visible = self.is_ugc_host
        self.quit_button.enabled = self.is_ugc_host
        self.save_button.visible = self.is_ugc_host
        self.disconnect_button.visible = not self.is_ugc_host
        if game_scene.player is None or game_scene.player.team is None:
            self.change_class_button.enabled = False
            self.change_team_button.enabled = False
            self.game_data_button.enabled = False
            self.constructs_button.enabled = False
            self.change_class_button.visible = True
            self.change_team_button.visible = True
            self.game_data_button.visible = False
            self.constructs_button.visible = False
        else:
            in_ugc_mode = game_scene.is_in_ugc_mode()
            self.change_class_button.enabled = not in_ugc_mode and game_scene.class_selection_has_choices()
            self.change_team_button.enabled = not in_ugc_mode and game_scene.team_selection_has_choices()
            self.constructs_button.enabled = in_ugc_mode
            self.game_data_button.enabled = in_ugc_mode
            self.change_class_button.visible = not in_ugc_mode
            self.change_team_button.visible = not in_ugc_mode
            self.game_data_button.visible = in_ugc_mode
            self.constructs_button.visible = in_ugc_mode
        if game_scene.current_mode is A2445:
            self.change_class_button.enabled = False
            self.change_class_button.visible = False
            self.change_team_button.enabled = False
            self.change_team_button.visible = False
        return

    def on_key_press(self, symbol, modifiers):
        ElementScene.on_key_press(self, symbol, modifiers)
        if symbol == self.config.menu:
            self.hide_message_box()
            self.resume()

    def resume(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        self.close_menu()

    def close_menu(self):
        from aoslib.scenes.main.gameScene import GameScene
        game_scene = self.manager.get_scene(GameScene)
        if game_scene.game_statistics_active:
            self.manager.set_menu(ViewGameStats)
        else:
            self.set_scene(GameScene)

    def disconnect_button_pressed(self):
        from aoslib.scenes.main.gameScene import GameScene
        game_scene = self.manager.get_scene(GameScene)
        if game_scene:
            game_scene.disconnect()
        else:
            self.manager.disconnect()
        self.media.stop_sounds()
        self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
        # The child has no console window.  Closing the client must drive its
        # stdin shutdown channel so round cleanup and UGC VXL persistence run.
        local_host.stop_active_session(self.manager)

    def message_box_button_one_pressed(self):
        self.hide_message_box()
        if self.message_id == MESSAGE_ON_SAVE:
            self.resume()
            self.message_id = None
        elif self.message_id == MESSAGE_QUIT_AFTER_SAVE:
            self.disconnect_button_pressed()
            self.message_id = None
        elif self.message_id == MESSAGE_SAVE_BEFORE_QUIT:
            self.save_button_pressed(True)
        return

    def message_box_button_two_pressed(self):
        self.hide_message_box()
        if self.message_id == MESSAGE_ON_SAVE:
            self.resume()
        elif self.message_id == MESSAGE_SAVE_BEFORE_QUIT:
            self.disconnect_button_pressed()
        self.message_id = None
        return

    def hide_message_box(self):
        if self.message_box.visible:
            self.message_box.set_visible(False)
            for element in self.elements:
                if element == self.message_box:
                    continue
                element.enabled = True

            self.setup_correct_buttons()

    def show_message_box(self, message_id, dialog_type, buttons_type, text):
        for element in self.elements:
            if element == self.message_box:
                continue
            element.enabled = False

        self.message_id = message_id
        self.message_box.set_dialog_message_type(dialog_type, buttons_type, text)
        self.message_box.set_visible(True)

    def on_quit_button_pressed(self):
        self.show_message_box(MESSAGE_SAVE_BEFORE_QUIT, DIALOG_WITH_BUTTONS, BUTTONS_YES_NO, strings.UGC_QUIT_WITHOUT_SAVING)

    def save_button_pressed(self, quit_on_save=False):
        from aoslib.scenes.main.gameScene import GameScene
        game_scene = self.manager.get_scene(GameScene)
        if game_scene:
            game_scene.save_ugc_file()
            game_scene.save_vxl_file()
            game_scene.save_png_file()
            message_id = MESSAGE_QUIT_AFTER_SAVE if quit_on_save else MESSAGE_ON_SAVE
            self.show_message_box(message_id, DIALOG_WITH_BUTTONS, BUTTONS_OK, strings.UGC_MAP_SAVE_SUCCESSFULLY)
            return
        self.show_message_box(MESSAGE_ON_SAVE, DIALOG_WITH_BUTTONS, BUTTONS_RETRY_CANCEL, strings.UGC_MAP_SAVE_ERROR)

    def settings_button_pressed(self):
        from aoslib.scenes.frontend.settingsMenu import SettingsMenu
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        self.parent.set_menu(SettingsMenu, in_game_menu=True)

    def change_class_button_pressed(self):
        game_scene = self.manager.game_scene
        if game_scene.current_mode is A2437 and game_scene.player and game_scene.player.team and game_scene.player.team.locked_class:
            game_scene.hud.add_big_message(strings.ZOMBIE_OUTBREAK_CLASS_SELECT)
            self.close_menu()
        else:
            from aoslib.scenes.ingame_menus.selectClass import SelectClass
            self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
            if game_scene.force_team_join:
                game_scene.team_selected(game_scene.teams[game_scene.force_team_join])
            else:
                game_scene.team_selected(game_scene.player.team)
            self.parent.set_menu(SelectClass, in_game_menu=True)

    def change_team_button_pressed(self):
        from aoslib.scenes.ingame_menus.changeTeam import ChangeTeam
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        self.parent.set_menu(ChangeTeam, in_game_menu=True)

    def constructs_button_pressed(self):
        from aoslib.scenes.ingame_menus.selectPrefabs import SelectPrefabs
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        self.parent.set_menu(SelectPrefabs, in_game_menu=True)

    def game_data_button_pressed(self):
        from aoslib.scenes.ingame_menus.selectGameData import SelectGameData
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        self.parent.set_menu(SelectGameData, in_game_menu=True)

    def resume_button_pressed(self):
        self.resume()

    def update(self, dt):
        game_scene = self.manager.game_scene
        if game_scene:
            in_ugc_mode = self.manager.game_scene.is_in_ugc_mode()
            if not in_ugc_mode and game_scene.game_statistics_active:
                self.change_team_button.enabled = False
                self.change_class_button.enabled = False
        if game_scene.current_mode is A2442:
            self.change_class_button.enabled = False
            self.change_class_button.visible = False
            if game_scene.player is not None and game_scene.player.current_class is not None and (game_scene.player.current_class.id is A84 or game_scene.player.current_class.id is A85):
                self.change_team_button.enabled = False
                self.change_team_button.visible = False
        return super(EscapeMenu, self).update(dt)

    def draw(self):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        x = 400
        y = 300
        if self.is_ugc_host:
            title_y = y + 150
            global_images.pause_menu_frame_big.blit(x, y - 30)
        else:
            title_y = y + 160
            global_images.pause_menu_frame.blit(x, y)
        title_font.draw(self.title.upper(), x, title_y, A1054, center=True)
        for element in self.elements:
            element.draw()
