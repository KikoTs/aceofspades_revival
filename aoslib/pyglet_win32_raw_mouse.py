import ctypes
import sys


WM_INPUT = 0x00FF
RID_INPUT = 0x10000003
RIM_TYPEMOUSE = 0
MOUSE_MOVE_ABSOLUTE = 0x0001
HID_USAGE_PAGE_GENERIC = 0x01
HID_USAGE_GENERIC_MOUSE = 0x02

_installed = False
_warned_messages = set()


def _warn_once(message):
    if message in _warned_messages:
        return
    _warned_messages.add(message)
    print message


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [('dwType', ctypes.c_ulong),
     ('dwSize', ctypes.c_ulong),
     ('hDevice', ctypes.c_void_p),
     ('wParam', ctypes.c_ulong)]


class RAWMOUSEBUTTONS(ctypes.Structure):
    _fields_ = [('usButtonFlags', ctypes.c_ushort),
     ('usButtonData', ctypes.c_ushort)]


class RAWMOUSEUNION(ctypes.Union):
    _fields_ = [('ulButtons', ctypes.c_ulong),
     ('buttons', RAWMOUSEBUTTONS)]


class RAWMOUSE(ctypes.Structure):
    _anonymous_ = ('buttons_union',)
    _fields_ = [('usFlags', ctypes.c_ushort),
     ('buttons_union', RAWMOUSEUNION),
     ('ulRawButtons', ctypes.c_ulong),
     ('lLastX', ctypes.c_long),
     ('lLastY', ctypes.c_long),
     ('ulExtraInformation', ctypes.c_ulong)]


class RAWINPUTUNION(ctypes.Union):
    _fields_ = [('mouse', RAWMOUSE)]


class RAWINPUT(ctypes.Structure):
    _anonymous_ = ('data',)
    _fields_ = [('header', RAWINPUTHEADER),
     ('data', RAWINPUTUNION)]


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [('usUsagePage', ctypes.c_ushort),
     ('usUsage', ctypes.c_ushort),
     ('dwFlags', ctypes.c_ulong),
     ('hwndTarget', ctypes.c_void_p)]


def install():
    global _installed
    if _installed:
        return
    if sys.platform != 'win32':
        return
    if '+legacymouse' in sys.argv:
        return
    import pyglet
    pyglet_version = getattr(pyglet, 'version', '')
    if not pyglet_version.startswith('1.2'):
        return
    from pyglet.window import mouse
    from pyglet.window import win32 as pyglet_win32
    window_cls = pyglet_win32.Win32Window
    if getattr(window_cls, '_raw_mouse_patch_installed', False):
        _installed = True
        return
    user32 = pyglet_win32._user32
    user32.RegisterRawInputDevices.argtypes = [ctypes.POINTER(RAWINPUTDEVICE), ctypes.c_uint, ctypes.c_uint]
    user32.RegisterRawInputDevices.restype = ctypes.c_int
    user32.GetRawInputData.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint), ctypes.c_uint]
    user32.GetRawInputData.restype = ctypes.c_uint
    user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
    user32.GetAsyncKeyState.restype = ctypes.c_short
    original_set_exclusive_mouse = window_cls.set_exclusive_mouse
    original_event_mousemove = window_cls._event_mousemove

    def use_raw_mouse(self):
        return getattr(self, '_raw_mouse_registered', False) and not getattr(self, '_raw_mouse_force_legacy', False)

    def force_legacy_mouse(self, reason):
        self._raw_mouse_force_legacy = True
        self._raw_mouse_registered = False
        _warn_once(reason)

    def prime_mouse_position(self):
        if not hasattr(self, '_exclusive_mouse_client'):
            self._reset_exclusive_mouse_screen()
        x, y = self._exclusive_mouse_client
        self._mouse_x = x
        self._mouse_y = self._height - y
        self._mouse_in_window = True

    def current_buttons(self):
        buttons = 0
        if user32.GetAsyncKeyState(pyglet_win32.VK_LBUTTON) & 32768:
            buttons |= mouse.LEFT
        if user32.GetAsyncKeyState(pyglet_win32.VK_MBUTTON) & 32768:
            buttons |= mouse.MIDDLE
        if user32.GetAsyncKeyState(pyglet_win32.VK_RBUTTON) & 32768:
            buttons |= mouse.RIGHT
        return buttons

    def ensure_raw_mouse_registration(self):
        if getattr(self, '_raw_mouse_force_legacy', False):
            return False
        view_hwnd = getattr(self, '_view_hwnd', None)
        if not view_hwnd:
            return False
        if getattr(self, '_raw_mouse_registered', False) and getattr(self, '_raw_mouse_hwnd', None) == view_hwnd:
            return True
        raw_input_device = RAWINPUTDEVICE(HID_USAGE_PAGE_GENERIC, HID_USAGE_GENERIC_MOUSE, 0, ctypes.c_void_p(view_hwnd))
        registered = user32.RegisterRawInputDevices(ctypes.byref(raw_input_device), 1, ctypes.sizeof(RAWINPUTDEVICE))
        if not registered:
            force_legacy_mouse(self, 'Warning: Raw mouse registration failed; falling back to legacy exclusive mouse.')
            return False
        self._raw_mouse_failure_count = 0
        self._raw_mouse_hwnd = view_hwnd
        self._raw_mouse_registered = True
        return True

    def read_raw_mouse(self, lParam):
        size = ctypes.c_uint(0)
        header_size = ctypes.c_uint(ctypes.sizeof(RAWINPUTHEADER))
        result = user32.GetRawInputData(ctypes.c_void_p(lParam), RID_INPUT, None, ctypes.byref(size), header_size.value)
        if result == 4294967295L or not size.value:
            return None
        data = ctypes.create_string_buffer(size.value)
        result = user32.GetRawInputData(ctypes.c_void_p(lParam), RID_INPUT, data, ctypes.byref(size), header_size.value)
        if result == 4294967295L:
            return None
        return ctypes.cast(data, ctypes.POINTER(RAWINPUT)).contents

    def set_exclusive_mouse(self, exclusive):
        result = original_set_exclusive_mouse(self, exclusive)
        if exclusive and getattr(self, '_has_focus', False):
            if ensure_raw_mouse_registration(self):
                prime_mouse_position(self)
        return result

    @pyglet_win32.ViewEventHandler
    @pyglet_win32.Win32EventHandler(pyglet_win32.WM_MOUSEMOVE)
    def _event_mousemove(self, msg, wParam, lParam):
        if not self._exclusive_mouse or not getattr(self, '_has_focus', False) or not use_raw_mouse(self):
            return original_event_mousemove(self, msg, wParam, lParam)
        x, y = self._get_location(lParam)
        if hasattr(self, '_exclusive_mouse_client') and (x, y) == self._exclusive_mouse_client:
            prime_mouse_position(self)
        return 0

    @pyglet_win32.ViewEventHandler
    @pyglet_win32.Win32EventHandler(WM_INPUT)
    def _event_rawinput(self, msg, wParam, lParam):
        if not self._exclusive_mouse or not getattr(self, '_has_focus', False) or not use_raw_mouse(self):
            return 0
        raw_input = read_raw_mouse(self, lParam)
        if raw_input is None:
            failure_count = getattr(self, '_raw_mouse_failure_count', 0) + 1
            self._raw_mouse_failure_count = failure_count
            if failure_count >= 3:
                force_legacy_mouse(self, 'Warning: Raw mouse input failed repeatedly; falling back to legacy exclusive mouse.')
            return 0
        self._raw_mouse_failure_count = 0
        if raw_input.header.dwType != RIM_TYPEMOUSE:
            return 0
        if raw_input.mouse.usFlags & MOUSE_MOVE_ABSOLUTE:
            return 0
        dx = raw_input.mouse.lLastX
        dy = -raw_input.mouse.lLastY
        if not dx and not dy:
            return 0
        prime_mouse_position(self)
        x = self._mouse_x
        y = self._mouse_y
        buttons = current_buttons(self)
        if buttons:
            modifiers = self._get_modifiers()
            self.dispatch_event('on_mouse_drag', x, y, dx, dy, buttons, modifiers)
        else:
            self.dispatch_event('on_mouse_motion', x, y, dx, dy)
        return 0

    window_cls._raw_mouse_patch_installed = True
    window_cls._raw_mouse_force_legacy = False
    window_cls._raw_mouse_registered = False
    window_cls._raw_mouse_failure_count = 0
    window_cls._raw_mouse_hwnd = None
    window_cls.set_exclusive_mouse = set_exclusive_mouse
    window_cls._event_mousemove = _event_mousemove
    window_cls._event_rawinput = _event_rawinput
    if '_event_rawinput' not in window_cls._platform_event_names:
        platform_event_names = set(window_cls._platform_event_names)
        platform_event_names.add('_event_rawinput')
        window_cls._platform_event_names = platform_event_names
    _installed = True
