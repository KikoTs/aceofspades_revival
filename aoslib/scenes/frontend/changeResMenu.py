from aoslib.scenes import Scene, ElementScene, MenuScene
from aoslib.common import wave, collides
from shared.constants import MENU_FONT_COLOR, MENU_FONT_COLOR2
from shared.common import clamp
from aoslib.text import title_font, settings_font, settings_changed_font, split_text_to_fit_screen
from aoslib.gui import TextButton
from aoslib.images import global_images
from pyglet import gl
from aoslib import strings, update_resolutions
from aoslib.media import MUSIC_AUDIO_ZONE, HUD_AUDIO_ZONE
DEFAULT_REVERT_COUNTDOWN = 15.0

class ChangeResolutionMenu(MenuScene):
    title = strings.CONFIRM
    config = None
    revert_countdown = DEFAULT_REVERT_COUNTDOWN
    countdown_text = ''

    def initialize(self):
        pass

    def on_menu_opened(self):
        self.elements = []
        self.revert_countdown = DEFAULT_REVERT_COUNTDOWN
        pad = 5
        x = 156 + pad
        width = 493 / 2 - pad * 2
        font_size = 30
        height = 71 - pad * 2
        y = 113 - pad
        self.confirm_button = TextButton(strings.KEEP_SETTING, x, y, width, height, font_size)
        self.confirm_button.add_handler(self.done_pressed)
        self.elements.append(self.confirm_button)
        x += width + pad
        self.cancel_button = TextButton(strings.REVERT, x, y, width, height, font_size)
        self.cancel_button.add_handler(self.cancel_pressed)
        self.elements.append(self.cancel_button)

    def on_start(self, menu=None, config=None):
        self.config = config
        self.on_menu_opened()

    def on_stop(self):
        pass

    def close(self):
        self.restore_resolution()

    def on_key_press(self, symbol, modifiers):
        pass

    def on_mouse_press(self, x, y, button, modifiers):
        width = 473
        x1 = 163
        x2 = x1 + width
        y1 = 467
        y2 = 500
        if collides(x1, y1, x2, y2, x, y, x, y):
            index = int((x - x1) / float(width / 3))
            self.set_tab(index)
            return
        ElementScene.on_mouse_press(self, x, y, button, modifiers)

    def done_pressed(self):
        self.media.play('menu_confirmA', zone=HUD_AUDIO_ZONE)
        self.config.save()
        from selectMenu import SelectMenu
        self.parent.set_menu(SelectMenu, back=True)

    def cancel_pressed(self):
        self.media.play('menu_backA', zone=HUD_AUDIO_ZONE)
        self.restore_resolution()
        from settingsMenu import SettingsMenu
        self.parent.set_menu(SettingsMenu, back=True, in_game_menu=self.in_game_menu, tab=1)
        if type(self.parent.menu) is SettingsMenu:
            self.parent.menu.set_graphics_tab_original_resolution(self.config.resolution)
        update_resolutions()

    def restore_resolution(self):
        self.config.restore()

    def update(self, dt):
        self.revert_countdown -= dt
        if self.revert_countdown <= 0.0:
            self.cancel_pressed()
        else:
            self.countdown_text = strings.KEEP_RESOLUTION.format(int(self.revert_countdown))
            self.countdown_text = split_text_to_fit_screen(settings_font, self.countdown_text, 400, 60)

    def draw(self):
        mid_x, mid_y = (400, 300)
        y = mid_y
        title_y = 534
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        global_images.small_frame.blit(mid_x, y)
        title_font.draw(self.title.upper(), mid_x, title_y, MENU_FONT_COLOR, center=True)
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        for element in self.elements:
            if not element.enabled:
                continue
            element.draw()

        countdown_texts = self.countdown_text.split('\n')
        y = mid_y + len(countdown_texts) / 2.0 * 20.0
        for str in countdown_texts:
            settings_font.draw(str, mid_x, y, MENU_FONT_COLOR, center=True)
            y -= 20.0
