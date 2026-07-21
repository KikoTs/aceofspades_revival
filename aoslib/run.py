from shared.steam import SteamInitializeClient, SteamRequestLobbyJoin
from shared import profiler
import shared.constants as constants
import shared.constants_ugc_objectives
import shared.constants_prefabs
from shared.common import enable_crashdump
import pyglet
pyglet.options['shadow_window'] = False

#fix mouse
#thx el Beshuele
from aoslib.pyglet_win32_raw_mouse import install as install_pyglet_win32_raw_mouse
install_pyglet_win32_raw_mouse()

SteamInitializeClient()
import sys
import ctypes
print 'Your Python version is %s.%s.%s' % sys.version_info[:3]
try:
    f = open('version.txt', 'r')
    game_build_version = f.read()
    f.close()
except:
    game_build_version = 0

print 'Current client build:', game_build_version
if 'fullcrashdump' in sys.argv:
    enable_crashdump(True)
else:
    enable_crashdump(False)
from aoslib import strings
print 'Strings imported'
from aoslib.config import Configuration
if '-reset' in sys.argv:
    global_config = Configuration('config.txt', reset=True)
else:
    try:
        global_config = Configuration('config.txt')
    except ValueError:
        import Tkinter, tkMessageBox
        root = Tkinter.Tk()
        root.withdraw()
        returnValue = tkMessageBox.askyesno(strings.CONFIG_FILE_ERROR_POPUP_TITLE, strings.CONFIG_FILE_ERROR_POPUP)
        if returnValue == True:
            global_config = Configuration('config.txt', reset=True)
        else:
            print 'Corrupt config file'
            sys.exit(1)

print 'Config loaded'
if global_config.antialias >= 3 or global_config.antialias < 0:
    global_config.antialias = 0
    global_config.save()
debug_gl = __debug__
pyglet.options['debug_gl'] = debug_gl
print 'debug_gl is', 'on' if debug_gl else 'off'

def is_good_screen_mode(mode):
    if mode.width >= 640 and mode.height >= 480:
        return True
    else:
        return False


platform = pyglet.window.get_platform()
display = platform.get_default_display()
screen = display.get_default_screen()
screen_modes = filter(is_good_screen_mode, screen.get_modes())

class Window(pyglet.window.Window):
    setting_fullscreen = False
    minimizing_fullscreen = False

    def __init__(self, *args, **kwargs):
        self.set_exclusive_keyboard()
        self.set_minimum_size(320, 240)
        super(Window, self).__init__(*args, **kwargs)

    def on_resize(self, width, height):
        if global_config.width == width and global_config.height == height:
            return

    def on_key_press(self, symbol, modifiers):
        pass

    def set_exclusive_mouse(self, value = True):
        pyglet.window.Window.set_exclusive_mouse(self, value)
        self.set_mouse_visible(not value)

    def on_deactivate(self):
        if not self.setting_fullscreen and global_config.fullscreen:
            self.setting_fullscreen = True
            self.minimizing_fullscreen = True
            self.set_fullscreen(False, width=global_config.width, height=global_config.height)
            self.minimize()

    def on_activate(self):
        if self.minimizing_fullscreen:
            self.setting_fullscreen = True
            self.set_fullscreen(True, width=global_config.width, height=global_config.height)
            self.minimizing_fullscreen = False
        self.setting_fullscreen = False

    def on_close(self):
        # Window close ends this runtime with os._exit below, which bypasses
        # atexit handlers. Retire a menu-owned hidden server explicitly first
        # so Alt+F4/the window close button cannot leave an orphan listener.
        try:
            import local_host
            local_host.stop_active_session()
        except Exception:
            try:
                local_host._append_local_host_log(
                    'window-close local server shutdown raised',
                    exc_info=sys.exc_info(),
                )
            except Exception:
                # Closing the game must remain possible even if the optional
                # local-host integration was not packaged or cannot log.
                pass
        super(Window, self).on_close()
        from twisted.internet import reactor
        if reactor.running:
            reactor.callFromThread(reactor.stop)
        import os
        os._exit(0)


options = {'double_buffer': True,
 'depth_size': 24}
print 'Starting MSAA Compatibility test'
test_config = screen.get_best_config(pyglet.gl.Config(**options))
temp_window = Window(resizable=True, config=test_config, visible=False, width=640, height=480)
temp_window.switch_to()
test_options = options.copy()
test_options['sample_buffers'] = 1
test_options['samples'] = 2
is_msaa_supported = False
try:
    test_config = screen.get_best_config(pyglet.gl.Config(**test_options))
    if test_config.is_complete() and test_config.sample_buffers == 1 and test_config.samples >= 2:
        is_msaa_supported = True
    else:
        is_msaa_supported = False
        print 'Anti-aliasing is not supported on this computer, turning it off.\n'
        global_config.antialias = 0
        global_config.save()
except pyglet.window.NoSuchConfigException:
    print 'Anti-aliasing is not supported on this computer, turning it off.\n'
    global_config.antialias = 0
    global_config.save()

print 'Finished MSAA Compatibility test'
from pyglet.gl.gl_info import GLInfo
info = GLInfo()
info.set_active_context()
constants.A1044 = info.have_version(2, 0)
if not constants.A1044:
    global_config.detail_level = -1
    print 'OpenGL 2.0 or above not detected. Falling back to compatibility shaders.\n'
info = None
temp_window.close()
print 'Loading images'
if global_config.detail_level < 0:
    print 'Compatibility shaders are enabled.\n'
    constants.A1044 = False
import aoslib.image as aosimage
print 'Setting texture quality'
pyglet.resource.path = ['png/ui']
aosimage.set_texture_quality(global_config.texture_quality)
print 'Indexing images'
pyglet.resource.reindex()
import graphicsManager as graphics_manager
the_graphics_manager = graphics_manager.graphics_manager
the_graphics_manager.screen_modes = screen_modes
the_graphics_manager.is_msaa_supported = is_msaa_supported
the_graphics_manager.initialise(global_config)
if global_config.antialias >= 1 and is_msaa_supported:
    import pyglet.gl as pyglet_gl
    pyglet.options['shadow_window'] = True
    pyglet_gl._create_shadow_window()
    options['sample_buffers'] = 1
    options['samples'] = the_graphics_manager.msaa_options[global_config.antialias]
options['debug'] = False
current_resolution = the_graphics_manager.current_resolution
compat_options_to_use = the_graphics_manager.compatible_options.copy()
try:
    py_config = screen.get_best_config(pyglet.gl.Config(**options))
except pyglet.window.NoSuchConfigException:
    pyglet.options['shadow_window'] = False
    print '(could not create OpenGL config - using most compatible config)'
    py_config = screen.get_best_config(pyglet.gl.Config(**compat_options_to_use))

window = Window(resizable=True, config=py_config, vsync=global_config.vsync, visible=False, width=current_resolution.width, height=current_resolution.height, caption='Ace of Spades')
if global_config.window_location_x < 0:
    global_config.window_location_x = 0
if global_config.window_location_y < 0:
    global_config.window_location_y = 0
if global_config.window_width <= 0:
    global_config.window_width = 800
if global_config.window_height <= 0:
    global_config.window_height = 600
max_x_res = 0
max_y_res = 0
screens_list = display.get_screens()
for test_screen in screens_list:
    max_x_res = max(max_x_res, test_screen.x + test_screen.width)
    max_y_res = max(max_y_res, test_screen.y + test_screen.height)

if global_config.window_location_x + global_config.window_width > max_x_res:
    global_config.window_location_x = max_x_res - global_config.window_width
if global_config.window_location_y + global_config.window_height > max_y_res:
    global_config.window_location_y = max_y_res - global_config.window_height
if global_config.window_location_x is 0 and global_config.window_location_y is 0:
    window.set_location(window.screen.width / 2 - window.width / 2, window.screen.height / 2 - window.height / 2)
else:
    window.set_location(global_config.window_location_x, global_config.window_location_y)
window.set_size(global_config.window_width, global_config.window_height)
if global_config.fullscreen:
    window.setting_fullscreen = True
    try:
        window.set_fullscreen(global_config.fullscreen, width=current_resolution.width, height=current_resolution.height)
    except:
        window.set_fullscreen(global_config.fullscreen, width=800, height=600)

window.invalid = False
print 'Starting loading screen...'
import loadingscreen
loadingscreen.init(window)
loadingscreen.update_progress()
loadingscreen.update_progress()
print 'Setting icons'
icons = []
from aoslib.image import load_image
for size in (16, 32, 64, 128):
    name = 'aos%s' % size
    icons.append(load_image(name, add_path=False))

window.set_icon(*icons)
loadingscreen.update_progress()
print 'Initializing GLEW'
from pyglet.lib import load_library
platform = pyglet.window.get_platform()
if sys.platform == 'win32':
    glew = ctypes.cdll.glew32
elif sys.platform == 'linux2':
    glew = load_library('GLEW')
elif sys.platform == 'darwin':
    glew = load_library('libGLEW.dylib')
ctypes.c_int.in_dll(glew, 'glewExperimental').value = 1
glew.glewInit()
from pyglet import gl
if debug_gl and __debug__:
    DEBUG_SOURCES = {gl.GL_DEBUG_SOURCE_API_ARB: 'OpenGL',
     gl.GL_DEBUG_SOURCE_WINDOW_SYSTEM_ARB: 'Windows',
     gl.GL_DEBUG_SOURCE_SHADER_COMPILER_ARB: 'Shader Compiler',
     gl.GL_DEBUG_SOURCE_THIRD_PARTY_ARB: 'Third Party',
     gl.GL_DEBUG_SOURCE_APPLICATION_ARB: 'Application',
     gl.GL_DEBUG_SOURCE_OTHER_ARB: 'Other'}
    DEBUG_TYPES = {gl.GL_DEBUG_TYPE_ERROR_ARB: 'Error',
     gl.GL_DEBUG_TYPE_DEPRECATED_BEHAVIOR_ARB: 'Deprecated behavior',
     gl.GL_DEBUG_TYPE_UNDEFINED_BEHAVIOR_ARB: 'Undefined behavior',
     gl.GL_DEBUG_TYPE_PORTABILITY_ARB: 'Portability',
     gl.GL_DEBUG_TYPE_PERFORMANCE_ARB: 'Performance',
     gl.GL_DEBUG_TYPE_OTHER_ARB: 'Other'}
    DEBUG_SEVERITIES = {gl.GL_DEBUG_SEVERITY_HIGH_ARB: 'High',
     gl.GL_DEBUG_SEVERITY_MEDIUM_ARB: 'Medium',
     gl.GL_DEBUG_SEVERITY_LOW_ARB: 'Low'}

    def on_error(source, typ, identifier, severity, length, message, user):
        source = DEBUG_SOURCES.get(source, source)
        typ = DEBUG_TYPES.get(typ, typ)
        severity = DEBUG_SEVERITIES.get(severity, severity)
        print length, message
        message = message[:length]
        import traceback
        traceback.print_stack()
        print 'type: %s, ID: %s, severity: %s, message: %s' % (typ,
         identifier,
         severity,
         message)


    if gl.gl_info.have_extension('GL_ARB_debug_output'):
        callback_c = gl.GLDEBUGPROCARB(on_error)
        gl.glDebugMessageCallbackARB(callback_c, None)
        gl.glEnable(gl.GL_DEBUG_OUTPUT_SYNCHRONOUS_ARB)
print 'Setting default OpenGL settings'
gl.glEnable(gl.GL_BLEND)
gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
gl.glTexEnvf(gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_MODULATE)
loadingscreen.show_window()
loadingscreen.update_progress()
print 'Creating pyglet reactor'
import pygletreactor
pygletreactor.install()
from twisted.internet import reactor
print 'Loading shaders'
from aoslib.shaders import load_shaders, unload_shaders
from shared.common import clamp
detail_level = clamp(global_config.detail_level, -1, 2)
original_detail = detail_level
detail_inc = -1
finished = False
failed = False
while not finished:
    try:
        if detail_level == -1:
            constants.A1044 = False
        else:
            constants.A1044 = True
        load_shaders(detail_level)
        finished = True
    except Exception as e:
        import traceback
        print traceback.format_exc()
        unload_shaders()
        detail_level += detail_inc
        if detail_inc < 0 and detail_level < -1:
            detail_inc = 1
            detail_level = original_detail + detail_inc
        if detail_inc > 0 and detail_level > 2:
            print 'GLSL and compatibility shaders failed to load.\n'
            finished = True
            failed = True

if failed:
    from pyglet.gl.lib import GLException
    window.on_deactivate()
    import Tkinter, tkMessageBox
    root = Tkinter.Tk()
    root.withdraw()
    tkMessageBox.showerror(strings.ERROR, strings.GL_ERROR_SHADERS_INIT)
    raise GLException(strings.GL_ERROR_SHADERS_INIT)
global_config.set('detail_level', detail_level)
import time
print 'Loading images...'
import aoslib.images
print 'Initializing draw'
import aoslib.draw
print 'Initializing common'
import aoslib.common
print 'Initializing shape'
import aoslib.shape
print 'Initializing gui'
import aoslib.gui
import aoslib.scenes.ingame_menus.ugcSettings
loadingscreen.update_progress()
import os
print 'Initializing Scene'
from aoslib.scenes import Scene
from aoslib.squadEventManager import *
loadingscreen.update_progress()
WAIT_RUN = False
loadingscreen.update_progress()
from aoslib.gamemanager import GameManager

class BootClass:

    def main(self, dt):
        print 'Checking arguments'
        if not GameManager.invalid_data_error and len(sys.argv) > 1:
            go_to_main_menu = False
            print 'Arguments passed: ', sys.argv
            invite_received = False
            try:
                connect_lobby_arg = sys.argv.index('+connect_lobby')
                connect_lobby_arg += 1
                identifier = sys.argv[connect_lobby_arg]
                invite_received = True
                if not SteamRequestLobbyJoin(int(identifier), block=True):
                    self.manager.set_big_text_message(constants.A965, disconnected=False)
                    go_to_main_menu = True
            except:
                go_to_main_menu = True

            if not invite_received:
                try:
                    connect_arg = sys.argv.index('+connect')
                    connect_arg += 1
                    identifier = sys.argv[connect_arg]
                    if identifier == 'local':
                        identifier = '127.0.0.1:32887'
                    from aoslib.scenes.ingame_menus.loadingMenu import LoadingMenu
                    self.manager.set_menu(LoadingMenu, identifier=identifier, from_server_menu=True)
                except:
                    go_to_main_menu = True

        else:
            go_to_main_menu = True
        if go_to_main_menu:
            print 'Starting main menu'
            from aoslib.scenes.frontend.menuScene import MenuScene
            if WAIT_RUN:

                class WaitScene(Scene):

                    def on_key_press(self, button, modifiers):
                        self.set_scene(MenuScene)

                scene = WaitScene
            else:
                scene = MenuScene
            self.manager.set_scene(scene)
        pyglet.clock.schedule_interval_soft(self.manager.update, constants.A1004)
        window.set_visible(True)

    def __init__(self):
        global loadingscreen
        from shared.constants import A2265
        print 'Hiding cursor'
        cursor_image = load_image('cursor')
        cursor = pyglet.window.ImageMouseCursor(cursor_image, 6, cursor_image.height - 4)
        window.set_mouse_cursor(cursor)
        print 'Loading models...'
        from aoslib import physfs
        path = os.getcwd()
        physfs.append_path(path)
        physfs.append_path(os.path.join(path, '../Common'))
        physfs.append_path(os.path.join(path, '../../Common'))
        import aoslib.models
        aoslib.models.load_models(global_config.orig_detail_level, global_config.model_detail)
        print 'Creating game manager...'
        from aoslib.gamemanager import GameManager
        self.manager = GameManager(global_config, window)
        self.manager.preload_favourite_servers()
        print 'Game manager created'
        loadingscreen.finished()
        pyglet.clock.schedule_once(self.main, 0)
        if A2265:
            import cProfile
            profile_name = 'profile.dat'
            i = 0
            while os.path.isfile(profile_name):
                profile_name = 'profile_%s.dat' % i
                i += 1

            cProfile.runctx('reactor.run()', locals(), globals(), profile_name)
        else:
            reactor.run()


BootClass()
