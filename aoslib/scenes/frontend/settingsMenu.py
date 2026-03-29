from aoslib.scenes import Scene, ElementScene, MenuScene
from mainTab import MainTab
from controlsTab import ControlsTab
from graphicsTab import GraphicsTab
from aoslib.common import wave, collides
from shared.constants import MENU_FONT_COLOR, MENU_FONT_COLOR2
from shared.common import clamp
from aoslib.text import title_font, settings_font, settings_changed_font, Label, draw_text_with_size_validation, draw_text_with_alignment_and_size_validation, small_standard_ui_font
from aoslib.gui import TextButton
from aoslib.images import global_images
from pyglet import gl
from aoslib import strings
from aoslib.draw import draw_quad
from aoslib.common import draw_image_resized
from aoslib.media import MUSIC_AUDIO_ZONE, HUD_AUDIO_ZONE
from shared.hud_constants import TEXT_BACKGROUND_SPACING, BLACK_COLOUR, UI_CONTROL_BAR_BUTTON_SPACING, RED_COLOUR

class SettingsMenu(MenuScene):
    title = strings.SETTINGS
    current_tab = None
    current_index = 0

    def initialize(self):
        self.main_tab = MainTab(self.manager)
        self.graphics_tab = GraphicsTab(self.manager)
        self.controls_tab = ControlsTab(self.manager)
        self.tabs = [
         (
          strings.MAIN, self.main_tab),
         (
          strings.GRAPHICS, self.graphics_tab),
         (
          strings.CONTROLS, self.controls_tab)]
        self.on_menu_opened()

    def set_graphics_tab_original_resolution(self, resolution):
        if self.graphics_tab is None:
            return
        else:
            self.graphics_tab.set_original_resolution(resolution)
            return

    def on_menu_opened(self):
        self.elements = []
        for tab in self.tabs:
            tab[1].set_in_game_tab(self.in_game_menu)
            self.elements.append(tab[1])
            tab[1].on_menu_opened()

        self.graphics_tab.set_original_resolution(self.config.resolution)
        pad = 13
        font_size = 30
        if self.in_game_menu:
            width = 232
            height = 41
            x = 160
            y = 120
            self.cancel_button = TextButton(strings.CANCEL, x, y, width, height, font_size)
            self.cancel_button.add_handler(self.back_pressed)
            self.elements.append(self.cancel_button)
            x += width + 11
            self.save_button = TextButton(strings.DONE, x, y, width, height, font_size)
            self.save_button.add_handler(self.save_pressed)
            self.elements.append(self.save_button)
        else:
            width = 240
            height = 60
            x = 152
            y = 108
            self.cancel_button = TextButton(strings.CANCEL, x, y, width, height, font_size)
            self.cancel_button.add_handler(self.cancel_pressed)
            self.elements.append(self.cancel_button)
            x += width + pad
            self.confirm_button = TextButton(strings.DONE, x, y, width, height, font_size)
            self.confirm_button.add_handler(self.done_pressed)
            self.elements.append(self.confirm_button)
        self.default_button = TextButton(strings.DEFAULTS, 151, 166, 80, 30, 14)
        self.default_button.add_handler(self.default_pressed)
        self.elements.append(self.default_button)
        self.set_tab(0, False)
        self.graphics_tab.set_enabled_controls(self.in_game_menu == False)

    def on_start(self, menu=None, tab=-1, **kw):
        self.on_menu_opened()
        if tab >= 0:
            self.set_tab(tab, play_sound=False)
            self.tabs[tab][1].get_values_from_config()
            self.tabs[tab][1].update_display()

    def on_stop(self):
        self.update_display()

    def update_display(self):
        for name, tab in self.tabs:
            tab.update_display()

    def set_tab(self, index, play_sound=True):
        if self.current_index != index:
            if play_sound:
                self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        if self.current_tab:
            self.current_tab.enabled = False
        self.current_index = index
        self.current_name, self.current_tab = self.tabs[index]
        self.current_tab.enabled = True
        self.default_button.enabled = self.current_tab.controls_enabled
        self.current_tab.on_set()

    def on_key_press(self, symbol, modifiers):
        if not (self.current_tab == self.controls_tab and self.controls_tab.key_has_focus()):
            if symbol == self.config.menu:
                if self.in_game_menu:
                    from aoslib.scenes.main.gameScene import GameScene
                    self.config.restore()
                    self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
                    if not self.manager.game_scene.game_statistics_active:
                        self.set_scene(GameScene)
                    else:
                        from aoslib.hud.hud import ViewGameStats
                        self.manager.set_menu(ViewGameStats)
                else:
                    self.cancel_pressed()
        ElementScene.on_key_press(self, symbol, modifiers)

    def on_mouse_press(self, x, y, button, modifiers):
        width = 494
        x1 = 152
        x2 = x1 + width
        y1 = 467
        y2 = 500
        if collides(x1, y1, x2, y2, x, y, x, y):
            index = int((x - x1) / float(width / 3))
            index = min(2, index)
            self.set_tab(index)
            return
        ElementScene.on_mouse_press(self, x, y, button, modifiers)

    def back_pressed(self):
        self.graphics_tab.cancel_changes()
        self.controls_tab.restore_values()
        self.config.restore()
        self.main_tab.back_pressed()
        from aoslib.scenes.ingame_menus.escapeMenu import EscapeMenu
        self.manager.set_menu(EscapeMenu)

    def save_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        self.main_tab.save_pressed()
        self.config.save()
        if not self.manager.game_scene.game_statistics_active:
            from aoslib.scenes.main.gameScene import GameScene
            self.set_scene(GameScene)
        else:
            from aoslib.hud.hud import ViewGameStats
            self.manager.set_menu(ViewGameStats)

    def done_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        defer_confirm = False
        if self.current_tab == self.graphics_tab:
            defer_confirm = self.current_tab.apply_changes()
        else:
            self.config.save()
        if not defer_confirm:
            self.go_back()

    def cancel_pressed(self):
        self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
        self.graphics_tab.cancel_changes()
        self.controls_tab.restore_values()
        self.config.restore()
        self.main_tab.back_pressed()
        self.go_back()

    def default_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        if self.current_tab == self.graphics_tab:
            self.current_tab.set_defaults()
        elif self.current_tab == self.main_tab:
            self.config.set_defaults('Main')
        elif self.current_tab == self.controls_tab:
            self.config.set_defaults('Controls')
        self.current_tab.on_defaults_pressed()

    def go_back(self):
        from selectMenu import SelectMenu
        self.parent.set_menu(SelectMenu, back=True)

    def draw(self):
        mid_x, mid_y = (400, 300)
        y = mid_y
        title_y = 549
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        if self.in_game_menu:
            y += 10
            title_y -= 15
            global_images.ingame_settings_frame.blit(mid_x, y)
        else:
            global_images.small_frame.blit(mid_x, y)
        title_width = 300
        title_height = 80
        draw_text_with_size_validation(self.title.upper(), mid_x - title_width / 2, title_y - title_height / 2, title_width, title_height, MENU_FONT_COLOR, font=title_font)
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        self.current_tab.content_frame.blit(mid_x - 12, mid_y)
        self.current_tab.draw()
        tab_width = 145.0
        tab_height = 26.0
        tab_x = 160.0
        tab_y = 470
        for name, tab in self.tabs:
            if self.current_tab == tab:
                text_colour = MENU_FONT_COLOR2
            else:
                text_colour = MENU_FONT_COLOR
            draw_text_with_size_validation(name, tab_x, tab_y, tab_width, tab_height, text_colour, settings_font)
            tab_x += tab_width + 20.0

        if self.current_tab.in_game_tab and self.current_tab == self.graphics_tab:
            tooltip = strings.SETTINGS_GRAPHICS_DISABLED_MESSAGE
            text_colour = RED_COLOUR
            self.default_button.enabled = False
        else:
            tooltip = strings.SETTINGS_MESSAGE
            text_colour = MENU_FONT_COLOR
            self.default_button.enabled = True
        self.draw_defaults_panel_tooltip(tooltip, text_colour)
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        for element in self.elements:
            if not element.enabled:
                continue
            element.draw()

    def draw_defaults_panel_tooltip(self, text, text_colour):
        if self.default_button is None:
            return
        else:
            button_frame_spacing = 7
            x = self.default_button.x + self.default_button.width + button_frame_spacing
            y = self.default_button.y - self.default_button.height + 2
            width = 407
            if not self.default_button.enabled:
                difference = self.default_button.width + button_frame_spacing
                width += difference
                x -= difference
            height = self.default_button.height - 2
            image = global_images.settings_tooltip_frame_ingame if self.in_game_menu else global_images.settings_tooltip_frame
            draw_image_resized(image, x + width * 0.5, y + height * 0.5, width, height, clear_colours=True)
            draw_text_with_alignment_and_size_validation(text, x + TEXT_BACKGROUND_SPACING, y, width - TEXT_BACKGROUND_SPACING * 2, height, text_colour, small_standard_ui_font, alignment_x='center', alignment_y='center')
            return
