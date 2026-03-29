from pyglet import gl
from pyglet.window import key
from aoslib.scenes import HUDScene
from aoslib.text import help_font, translate_controls_in_message, draw_text_with_alignment_and_size_validation
from aoslib.images import global_images
from shared.constants import *
from aoslib.scenes.ingame_menus import draw_player_list
from aoslib import media, strings
from shared.constants import MENU_FONT_COLOR
from aoslib.hud.helpPanel import HelpPanel
from pyglet.window.mouse import LEFT, MIDDLE, RIGHT
import pyglet
from aoslib.customimage import *
from aoslib import image
from aoslib.common import draw_image_resized
from aoslib.draw import draw_quad
from aoslib.images import global_images

class ScreenshotHud(HUDScene):

    def initialize(self):
        scene = self.manager.game_scene
        self.help_panel = HelpPanel(scene.hud)
        max_width = self.manager.window.width * 0.8
        self.help_panel.set_max_width(max_width)
        self.take_screenshot_queued = False

    def on_start(self, menu=None, **kw):
        super(ScreenshotHud, self).on_start(menu, **kw)
        self.help_panel.set_text([strings.SCREENSHOT_HUD_TEXT], 0.0, True, play_sound=False)
        self.help_panel.force_open()
        scene = self.manager.game_scene
        scene.returned_from_map_preview_editor = True
        scene.map_temp_preview_overhead = self.manager.client.ugc_data.use_overhead_image

    def take_control(self):
        self.control = True
        self.parent.current_x = 1.0

    def on_stop(self):
        super(ScreenshotHud, self).on_stop()
        self.control = False

    def update(self, dt):
        scene = self.manager.game_scene
        return super(ScreenshotHud, self).update(dt)

    def draw(self):
        if self.take_screenshot_queued:
            return
        scene = self.manager.game_scene
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        for element in self.elements:
            element.draw()

    def draw_hud(self):
        if self.take_screenshot_queued:
            self.take_screenshot()
            return
        scene = self.manager.game_scene
        map_preview_image = self.get_map_preview_image()
        if map_preview_image:
            if scene.window.width < scene.window.height:
                width = scene.window.width * 0.3
                height = width
            else:
                height = scene.window.height * 0.3
                width = height
            padding = 10
            image_padding = 5
            y = padding
            x = scene.window.width - width - padding
            draw_quad(x, y, width, height, (0, 0, 0, 100))
            gl.glColor4f(1.0, 1.0, 1.0, 1.0)
            draw_image_resized(map_preview_image, x + image_padding, y + image_padding, width - image_padding * 2.0, height - image_padding * 2.0)
        self.help_panel.draw()
        if scene.hud:
            scene.hud.draw_chat()

    def on_key_release(self, symbol, modifiers):
        if self.manager.locked_to_scene:
            return
        if symbol == self.config.menu:
            from aoslib.scenes.ingame_menus.ugcSettings import UGCSettings
            self.manager.set_menu(UGCSettings, back=True)
            self.manager.game_scene.disable_player_input = False
            self.manager.game_scene.camera_manager.deactivate_controller()

    def on_key_press(self, button, modifiers):
        scene = self.manager.game_scene
        chat_is_active = scene.hud.has_input
        if button == scene.config.global_chat or button == scene.config.team_chat or chat_is_active:
            scene.hud.on_key_press(button, modifiers)
        elif button == scene.config.tool_help:
            self.help_panel.toggle_show()

    def on_mouse_press(self, x, y, button, modifiers):
        if button == LEFT:
            self.queue_take_screenshot()
        elif button == RIGHT:
            scene = self.manager.game_scene
            if not self.manager.client.ugc_data:
                return
            self.manager.game_scene.set_temp_ugc_preview_image(minimap=True)

    def on_text_motion(self, motion):
        scene = self.manager.game_scene
        if scene.hud:
            scene.hud.on_text_motion(motion)

    def on_text(self, value):
        scene = self.manager.game_scene
        if scene.hud:
            scene.hud.on_text(value)

    def queue_take_screenshot(self):
        if not self.manager.client.ugc_data:
            return
        self.take_screenshot_queued = True

    def take_screenshot(self):
        if not self.take_screenshot_queued:
            return
        image_data = pyglet.image.get_buffer_manager().get_color_buffer().get_image_data()
        width = image_data.width
        height = image_data.height
        smallest_size = int(min(width, height))
        x = int(width - smallest_size) / 2
        y = int(height - smallest_size) / 2
        if smallest_size > 512:
            cropped_image = custom_image_crop(image_data.data, 4, int(width), int(height), x, y, x + smallest_size - 1, y + smallest_size - 1)
            scaled_image = custom_image_scale(cropped_image, 3, smallest_size, smallest_size, 512, 512)
            resized_image_data = pyglet.image.ImageData(512, 512, 'RGB', scaled_image)
            preview_image = resized_image_data
        else:
            preview_image = image_data.get_region(x, y, smallest_size, smallest_size)
        self.manager.game_scene.set_temp_ugc_preview_image(minimap=False, image=preview_image)
        self.take_screenshot_queued = False

    def get_map_preview_image(self):
        scene = self.manager.game_scene
        map_preview_image = None
        if scene.map_temp_preview_overhead:
            map_preview_image = scene.map.minimap_texture
        if not map_preview_image:
            map_preview_image = scene.map_temp_preview_image
        if not map_preview_image and self.manager.client.ugc_data and self.manager.client.ugc_data.local_png_data:
            map_preview_image_data = self.manager.client.ugc_data.local_png_data
            map_preview_image = image.load_texture_from_memory(map_preview_image_data)
            scene.map_preview_image = map_preview_image
        if not map_preview_image:
            scene.map.minimap_texture
        return map_preview_image
