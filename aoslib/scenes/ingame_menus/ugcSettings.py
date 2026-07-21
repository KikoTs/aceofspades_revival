# uncompyle6 version 3.9.2
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.12.0 (tags/v3.12.0:0fb18b0, Oct  2 2023, 13:03:39) [MSC v.1935 64 bit (AMD64)]
# Embedded file name: C:\TeamCity\buildAgent\work\dc8eb0b1d2cf198a\Main\client\standalone\build\pyi.win32\run_obfuscated\out00-PYZ.pyz\aoslib.scenes.ingame_menus.ugcSettings
from aoslib.scenes.frontend.panelBase import BACKGROUND_NONE
from aoslib.scenes.frontend.expandableListPanel import ExpandableListPanel
from aoslib.scenes.main.settingsSliderControlListItem import SettingsSliderControlListItem
from aoslib.scenes.main.settingsToggleListItem import SettingsToggleListItem
from aoslib.scenes.main.settingsOptionCheckboxListItem import SettingsOptionCheckboxListItem
from aoslib.scenes.main.settingsRangeBarListItem import SettingsRangeBarListItem
from aoslib.scenes.main.settingsDropdownBoxListItem import SettingsDropdownListItem
from aoslib.scenes.main.categoryListItem import CategoryListItem
from aoslib.scenes.main.matchSettingsEditTextListItem import MatchSettingsEditTextListItem
from aoslib.scenes.main.settingsColourPreviewListItem import SettingsColourPreviewListItem
from aoslib.scenes.main.settingsButtonControlListItem import SettingsButtonControlListItem
from aoslib.images import global_images
from aoslib import strings
from aoslib.media import HUD_AUDIO_ZONE
from aoslib.tools import make_game_manager_favourite_key
from shared.hud_constants import CATEGORY_ROW_HEIGHT, SETTINGS_ROW_HEIGHT, SETTINGS_ROW_SPACING, ROW_GREY_COLOUR, ROW_DARK_GREY_COLOUR
import string
from shared.steam import SteamGetCurrentLobby, SteamGetLobbyData, SteamSetLobbyData
from aoslib.scenes import Scene, ElementScene, MenuScene
from aoslib.gui import TextButton
from aoslib.text import title_font, draw_text_with_size_validation
from pyglet import gl
from shared.constants import A1054, A986
from shared.common import get_skydomes_names, clamp
from aoslib.scenes.ingame_menus.screenshotHud import ScreenshotHud
from aoslib.scenes.frontend.ugcModePanel import get_ugc_lobby_modes
from aoslib.scenes.main.matchSettings import get_list_items_as_string
from shared.constants_gamemode import A2448, A2451
import os
import local_host

class UGCSettings(MenuScene):
    content_frame = global_images.ingame_settings_content_frame

    def initialize(self):
        if not (
            self.manager.game_scene.is_ugc_host()
            or local_host.is_local_ugc_host(self.manager)
        ):
            self.cancel_pressed()
        self.x = 152
        self.y = 495
        self.width = 494
        self.height = 351
        self.elements = []
        self.controls_enabled = True
        self.in_game_tab = False
        self.list_panel = ExpandableListPanel(self.manager)
        self.list_panel.initialise_ui('', self.x, self.y, self.width, self.height)
        self.list_panel.set_row_height(CATEGORY_ROW_HEIGHT, SETTINGS_ROW_HEIGHT)
        self.list_panel.set_background(BACKGROUND_NONE)
        self.list_panel.line_spacing = SETTINGS_ROW_SPACING
        self.elements.append(self.list_panel)
        self.skybox_row = None
        self.ugc_mode_row = None
        self.water_preview_row = None
        width = 232
        height = 41
        x = 160
        y = 120
        self.cancel_button = TextButton(strings.CANCEL, x, y, width, height, 30)
        self.cancel_button.add_handler(self.cancel_pressed)
        x += width + 11
        self.save_button = TextButton(strings.APPLY, x, y, width, height, 30)
        self.save_button.add_handler(self.save_pressed)
        self.elements.append(self.save_button)
        self.elements.append(self.cancel_button)
        self.scene = self.manager.game_scene
        self.valid_skyboxes = get_skydomes_names()
        return

    def populate_list(self):
        self.list_panel.reset_list()
        self.lobby_id = SteamGetCurrentLobby()
        self.map_title = SteamGetLobbyData(self.lobby_id, 'MAP_ROTATION_NEW_TITLE')
        self.water_red, self.water_green, self.water_blue = self.scene.get_water_color()
        self.water_colour = (self.water_red, self.water_green, self.water_blue, 255)
        self.ugc_edit_mode = A2451[self.manager.ugc_mode]
        if len(self.valid_skyboxes) > 0:
            skybox_filename = self.scene.get_skybox_name()
            skybox_name = os.path.splitext(skybox_filename)[0]
            if skybox_name in self.valid_skyboxes:
                self.skybox = skybox_name
        skybox_index = self.valid_skyboxes.index(self.skybox)
        sky_category_item = CategoryListItem(strings.SKY, is_expandable=True, sub_row_colours=[ROW_GREY_COLOUR, ROW_DARK_GREY_COLOUR], sort_order=0)
        water_category_item = CategoryListItem(strings.WATER, is_expandable=True, sub_row_colours=[ROW_GREY_COLOUR, ROW_DARK_GREY_COLOUR], sort_order=1)
        config_category_item = CategoryListItem(strings.CONFIG, is_expandable=True, sub_row_colours=[ROW_GREY_COLOUR, ROW_DARK_GREY_COLOUR], sort_order=2)
        if len(self.valid_skyboxes) > 0:
            sky_rows = []
            self.skybox_row = SettingsDropdownListItem(strings.SKYDOME, 'skydome', self.valid_skyboxes, self.manager, skybox_index, self.set_skybox)
            sky_rows.append(self.skybox_row)
            self.list_panel.add_list_item(sky_category_item, sky_rows)
        water_rows = []
        row = SettingsSliderControlListItem(strings.RED, 'water_red', self.water_red, self.on_red_slider_change, 0, 255, 0, has_edit_box=False)
        water_rows.append(row)
        row = SettingsSliderControlListItem(strings.GREEN, 'water_green', self.water_green, self.on_green_slider_change, 0, 255, 0, has_edit_box=False)
        water_rows.append(row)
        row = SettingsSliderControlListItem(strings.BLUE, 'water_blue', self.water_blue, self.on_blue_slider_change, 0, 255, 0, has_edit_box=False)
        water_rows.append(row)
        self.water_preview_row = SettingsColourPreviewListItem(strings.PREVIEW, 'preview', self.water_colour)
        water_rows.append(self.water_preview_row)
        self.list_panel.add_list_item(water_category_item, water_rows)
        config_rows = []
        ugc_modes, mode_to_select = get_ugc_lobby_modes(self.lobby_id)
        if len(ugc_modes) > 0:
            selected_mode_index = ugc_modes.index(mode_to_select)
            self.ugc_mode_row = SettingsDropdownListItem(strings.CHOOSE_GAME_MODE, 'ugc_mode', ugc_modes, self.manager, selected_mode_index, self.set_ugc_mode)
            config_rows.append(self.ugc_mode_row)
        map_title = SteamGetLobbyData(self.lobby_id, 'MAP_ROTATION_NEW_TITLE')
        self.title_row = MatchSettingsEditTextListItem(map_title, strings.UGC_MAP_TITLE, 'MAP_TITLE', self.lobby_id, self.on_save_map_modified, self.manager.game_scene.profanity_manager)
        config_rows.append(self.title_row)
        row = SettingsButtonControlListItem(strings.MAP_PREVIEW_IMAGE, strings.SET, 'map_preview', self.on_map_preview_set_clicked)
        config_rows.append(row)
        self.list_panel.add_list_item(config_category_item, config_rows)
        for row in self.list_panel.rows:
            row.set_enabled(True)

        self.list_panel.on_scroll(0, silent=True)
        self.skybox_row.control.list_panel.recreate_scrollbar()
        self.ugc_mode_row.control.list_panel.recreate_scrollbar()

    def get_row_with_id(self, id):
        for row in self.list_panel.rows:
            if row.id == id:
                return row

        return

    def on_start(self):
        if self.scene.returned_from_map_preview_editor:
            self.scene.returned_from_map_preview_editor = False
        else:
            self.scene.reset_ugc_preview_image()
            self.populate_list()
            self.list_panel.on_scroll(0, silent=True)
            self.list_panel.scrollbar.set_scroll(0, force_callback_call=True, silent=True)

    def on_key_press(self, symbol, modifiers):
        if symbol == self.config.menu or symbol == self.config.ugc_settings and not self.title_row.control.focus:
            from aoslib.scenes.main.gameScene import GameScene
            self.set_scene(GameScene)
            self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
        ElementScene.on_key_press(self, symbol, modifiers)

    def draw(self):
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        mid_x, mid_y = (400, 300)
        y = mid_y
        y += 10
        global_images.ingame_settings_frame.blit(mid_x, y)
        self.content_frame.blit(mid_x - 12, mid_y)
        title_y = 534
        title_width = 300
        title_height = 80
        draw_text_with_size_validation(strings.SETTINGS.upper(), mid_x - title_width / 2, title_y - title_height / 2, title_width, title_height, A1054, font=title_font)
        for element in self.elements:
            element.draw()

        if self.ugc_mode_row is not None and self.ugc_mode_row.visible and self.ugc_mode_row.control:
            self.ugc_mode_row.control.draw()
        if self.skybox_row is not None and self.skybox_row.visible and self.skybox_row.control:
            self.skybox_row.control.draw()
        return

    def update_display(self):
        pass

    def on_defaults_pressed(self):
        pass

    def on_map_preview_set_clicked(self):
        self.scene.disable_player_input = True
        self.scene.camera_manager.activate_controller(A986, None, self.scene.player)
        self.manager.set_menu(ScreenshotHud)
        return

    def cancel_pressed(self):
        from aoslib.scenes.main.gameScene import GameScene
        self.set_scene(GameScene)
        self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
        self.scene.reset_ugc_preview_image()

    def save_pressed(self):
        from aoslib.scenes.main.gameScene import GameScene
        self.set_scene(GameScene)
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        self.scene.set_ugc_preview_image()
        SteamSetLobbyData('MAP_ROTATION_NEW_TITLE', self.map_title)
        # The local dedicated editor, not the Steam-emulator lobby, owns the
        # persisted sidecar.  Relay the title over its private host-only
        # command so the next checkpoint cannot restore the old value.
        local_host.send_local_ugc_title(self.manager, self.map_title)
        ugc_data = self.manager.client.ugc_data
        self.manager.game_scene.set_water_color(self.water_colour)
        if self.skybox and len(self.skybox) > 0:
            self.manager.game_scene.set_skybox_name(self.skybox + '.txt')
        SteamSetLobbyData('UGC_MODES', get_list_items_as_string([self.ugc_edit_mode]))
        self.manager.game_scene.send_ugc_edit_mode(self.ugc_edit_mode)

    def set_ugc_mode(self, value, value_as_string, config_name):
        self.ugc_edit_mode = None
        for mode in A2448.keys():
            if strings.get_by_id(A2448[mode]) == self.ugc_mode_row.control.list_panel.rows[value].name:
                self.ugc_edit_mode = mode
                break

        if not self.ugc_edit_mode:
            self.ugc_edit_mode = 'ctf'
        return

    def set_skybox(self, value, value_as_string, config_name):
        if value_as_string and len(value_as_string) > 0:
            skybox_index = value
            if skybox_index >= 0 and skybox_index < len(self.valid_skyboxes):
                self.skybox = self.valid_skyboxes[skybox_index]

    def on_red_slider_change(self, value, set_on_click=True):
        if set_on_click:
            self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
        self.water_red = int(value)
        self.water_colour = (self.water_red, self.water_green, self.water_blue, 255)
        if self.water_preview_row:
            self.water_preview_row.set_value(self.water_colour)

    def on_green_slider_change(self, value, set_on_click=True):
        if set_on_click:
            self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
        self.water_green = int(value)
        self.water_colour = (self.water_red, self.water_green, self.water_blue, 255)
        if self.water_preview_row:
            self.water_preview_row.set_value(self.water_colour)

    def on_blue_slider_change(self, value, set_on_click=True):
        if set_on_click:
            self.media.play('menu_scrollA', zone=HUD_AUDIO_ZONE)
        self.water_blue = int(value)
        self.water_colour = (self.water_red, self.water_green, self.water_blue, 255)
        if self.water_preview_row:
            self.water_preview_row.set_value(self.water_colour)

    def on_save_map_modified(self, name):
        if not (
            self.manager.game_scene.is_ugc_host()
            or local_host.is_local_ugc_host(self.manager)
        ):
            return
        self.map_title = name

    def on_mouse_release(self, x, y, button, modifiers):
        if self.skybox_row and not self.skybox_row.control.selected and self.ugc_mode_row and not self.ugc_mode_row.control.selected:
            super(UGCSettings, self).on_mouse_release(x, y, button, modifiers)
        if self.skybox_row is not None and self.skybox_row.enabled:
            self.skybox_row.control.on_mouse_release(x, y, button, modifiers)
            if self.skybox_row.control.selected:
                return
        if self.ugc_mode_row is not None and self.ugc_mode_row.enabled:
            self.ugc_mode_row.control.on_mouse_release(x, y, button, modifiers)
            if self.ugc_mode_row.control.selected:
                return
        return

    def on_mouse_motion(self, x, y, dx, dy):
        if self.skybox_row and not self.skybox_row.control.selected and self.ugc_mode_row and not self.ugc_mode_row.control.selected:
            super(UGCSettings, self).on_mouse_motion(x, y, dx, dy)
        if self.skybox_row is not None and self.skybox_row.enabled:
            self.skybox_row.control.on_mouse_motion(x, y, dx, dy)
            if self.skybox_row.control.selected:
                return
        if self.ugc_mode_row is not None and self.ugc_mode_row.enabled:
            self.ugc_mode_row.control.on_mouse_motion(x, y, dx, dy)
            if self.ugc_mode_row.control.selected:
                return
        return

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        if self.skybox_row and not self.skybox_row.control.selected and self.ugc_mode_row and not self.ugc_mode_row.control.selected:
            super(UGCSettings, self).on_mouse_drag(x, y, dx, dy, button, modifiers)
        if self.skybox_row is not None and self.skybox_row.enabled:
            self.skybox_row.control.on_mouse_drag(x, y, dx, dy, button, modifiers)
            if self.skybox_row.control.selected:
                return
        if self.ugc_mode_row is not None and self.ugc_mode_row.enabled:
            self.ugc_mode_row.control.on_mouse_drag(x, y, dx, dy, button, modifiers)
            if self.ugc_mode_row.control.selected:
                return
        return

    def on_mouse_scroll(self, x, y, dx, dy):
        if self.skybox_row and not self.skybox_row.control.selected and self.ugc_mode_row and not self.ugc_mode_row.control.selected:
            super(UGCSettings, self).on_mouse_scroll(x, y, dx, dy)
        if self.skybox_row is not None and self.skybox_row.enabled:
            self.skybox_row.control.on_mouse_scroll(x, y, dx, dy)
            if self.skybox_row.control.selected:
                return
        if self.ugc_mode_row is not None and self.ugc_mode_row.enabled:
            self.ugc_mode_row.control.on_mouse_scroll(x, y, dx, dy)
            if self.ugc_mode_row.control.selected:
                return
        return

    def on_mouse_press(self, x, y, button, modifiers):
        if self.skybox_row and not self.skybox_row.control.selected and self.ugc_mode_row and not self.ugc_mode_row.control.selected:
            super(UGCSettings, self).on_mouse_press(x, y, button, modifiers)
        if self.skybox_row is not None and self.skybox_row.enabled:
            self.skybox_row.control.on_mouse_press(x, y, button, modifiers)
            if self.skybox_row.control.selected:
                return
        if self.ugc_mode_row is not None and self.ugc_mode_row.enabled:
            self.ugc_mode_row.control.on_mouse_press(x, y, button, modifiers)
            if self.ugc_mode_row.control.selected:
                return
        return
