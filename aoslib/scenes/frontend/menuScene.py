import sys, time, random, math
from aoslib import calculate_scale_on_window_resize, update_resolutions
from aoslib.scenes import Scene, ElementScene, MenuScene
from aoslib.draw import draw_offset, draw_quad
from aoslib.images import global_images
from pyglet import gl
from pyglet.window import key
import gc
MENU_MOVE_NORMALIZE = 10.0

class MenuScene(ElementScene):
    current_x = 0.0
    tile_x = 0.0
    tile_y = 0.0
    old_menu = old_back = None
    menu = None
    tile_alpha = 0.0
    grey_alpha = 0.0
    random_noise = 0.0
    constant_timestep = False
    background = None
    mouse_transform = None
    background_alpha = 1.0
    menu_class = None
    clears_scene_lock = True
    hide_menu = False
    hide_hud = False
    scale_w = 1.0
    scale_h = 1.0

    def initialize(self):
        self.menus = {}
        self.background = global_images.main_image
        self.hide_menu = False
        self.hide_hud = False

    def on_start(self, menu=None, **kw):
        if menu == None:
            from selectMenu import SelectMenu
            menu = SelectMenu
        if menu.control:
            self.manager.reset_input()
        self.set_menu(menu, **kw)
        return

    def on_stop(self):
        if self.menu is not None:
            self.menu.on_stop()
        self.window.set_exclusive_mouse(True)
        self.menu = old_menu = None
        self.current_x = 0.0
        return

    def close(self):
        if self.manager.game_scene.map:
            self.manager.game_scene.destroy_map()
        if self.menu is not None:
            self.menu.close()
        return

    def set_menu(self, klass, back=False, in_game_menu=False, **kw):
        freed = gc.collect()
        if self.menu is not None and klass is not self.menu_class:
            self.on_mouse_motion(-800, 0, 0, 0)
            if back:
                self.current_x = -1.0
            else:
                self.current_x = 1.0
            self.old_menu = self.menu
            self.old_back = back
            self.menu.on_stop()
        try:
            self.menu = self.menus[klass]
        except KeyError:
            self.menu = klass(self.manager, in_game_menu)
            self.menus[klass] = self.menu

        self.menu_class = klass
        self.menu.parent = self
        self.menu.in_game_menu = in_game_menu
        self.menu.on_start(**kw)
        if self.menu:
            self.menu.on_mouse_motion(-800, 0, 0, 0)
            self.window.set_exclusive_mouse(not self.menu.control)
        return

    def update(self, dt):
        from aoslib.common import interpolate
        if self.menu:
            self.menu.update(dt)
        self.current_x = interpolate(self.current_x, 0.0, MENU_MOVE_NORMALIZE)
        if math.fabs(self.current_x) < 0.005:
            self.old_menu = None
        if self.manager.show_game_scene:
            add = -dt
            self.manager.game_scene.update(dt)
        else:
            add = dt
        self.background_alpha = max(0.0, min(1.0, self.background_alpha + add))
        if self.background_alpha >= 1.0 and self.manager.game_scene.map:
            self.manager.game_scene.destroy_map()
        return

    def on_key_release(self, *arg, **kw):
        if not self.enabled:
            return
        for element in self.get_elements():
            element.on_key_release(*arg, **kw)

    def draw(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        if self.background_alpha < 1.0:
            self.manager.game_scene.draw(True)
        self.set_normal_perspective()
        gl.glLoadIdentity()
        window = self.window
        gl.glColor4f(1.0, 1.0, 1.0, self.background_alpha)
        x, y, scale_w, scale_h, custom_resolution = calculate_scale_on_window_resize(window, self.background, False, True)
        if x == 0 and y == 0 and scale_w == 0 and scale_h == 0 and custom_resolution == False:
            return
        else:
            if (scale_w != self.scale_w or scale_h != self.scale_h) and not self.manager.config.fullscreen and custom_resolution:
                self.manager.save_window_position()
                from changeResMenu import ChangeResolutionMenu
                if self.menu_class is ChangeResolutionMenu:
                    self.manager.config.save(set_old_config=False)
                else:
                    self.manager.config.save()
                self.scale_h = scale_h
                self.scale_w = scale_w
                update_resolutions()
            self.background.blit(x, y, 0, self.background.width * scale_w, self.background.height * scale_h)
            x, y, width, height, ratio = self.manager.get_aspect(800, 600)
            self.mouse_transform = (x, y, ratio)
            gl.glPushMatrix()
            gl.glTranslatef(int(x + self.current_x * window.width), y, 0.0)
            if ratio != 1.0:
                gl.glScalef(ratio, ratio, 1.0)
            if self.old_menu is not None:
                if self.old_back:
                    offset = window.width
                else:
                    offset = -window.width
                draw_offset(self.old_menu.draw, int(offset / ratio), 0)
            if self.menu and not self.hide_menu:
                self.menu.draw()
            gl.glPopMatrix()
            if self.menu and not self.hide_hud:
                self.menu.draw_hud()
            return

    def is_menu_available(self):
        return math.fabs(self.current_x) < 0.5

    def get_elements(self):
        elements = []
        if self.menu:
            if not self.menu.control:
                elements.append(self.manager.game_scene)
            if self.is_menu_available():
                elements.append(self.menu)
        return elements

    def transform_mouse(self, x, y):
        if not self.mouse_transform:
            return (x, y)
        off_x, off_y, ratio = self.mouse_transform
        x = (x - off_x) / ratio
        y = (y - off_y) / ratio
        return (x, y)

    def on_connect(self):
        if self.menu:
            self.menu.on_connect()
        self.manager.game_scene.on_connect()

    def packet_received(self, packet, sent_time):
        if self.manager.show_game_scene:
            self.manager.game_scene.packet_received(packet, sent_time)
        if self.menu:
            self.menu.packet_received(packet, sent_time)

    def on_map_transfer(self):
        if self.menu:
            self.menu.on_map_transfer()

    def on_pack_transfer(self):
        if self.menu:
            self.menu.on_pack_transfer()
