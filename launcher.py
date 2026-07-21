# -*- coding: utf-8 -*-
"""AoS Revival launcher, compatible with the shipped Python 2.7 runtime."""
from __future__ import print_function, unicode_literals

import codecs
import ctypes
import os
import re
import subprocess
import sys
import threading
import time
import traceback
import webbrowser

try:
    import Queue as queue
except ImportError:
    import queue

try:
    import ConfigParser as configparser
    import Tkinter as tk
    import tkMessageBox as messagebox
    import tkSimpleDialog as simpledialog
    import ttk
except ImportError:
    import configparser
    import tkinter as tk
    from tkinter import messagebox, simpledialog, ttk

from revival_api import RevivalApiError, RevivalClient, service_unavailable


SITE_URL = "https://www.aosplay.net"
DISCORD_URL = "https://discord.gg/gmBBGKpEgY"
STEAM_APP_URL = "steam://run/224540"

INK = "#171912"
PANEL = "#25281d"
PANEL_LIGHT = "#343827"
OLIVE = "#626b2d"
OLIVE_DARK = "#3c421d"
GOLD = "#d9bf55"
GOLD_LIGHT = "#f3dd78"
CREAM = "#fff0b0"
RED = "#e74a21"
GREEN = "#9abb36"
MUTED = "#b5b393"

_LAUNCHER_MUTEX = None


def app_directory():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


APP_DIR = app_directory()
ASSET_DIR = os.path.join(APP_DIR, "png", "ui")
EMU_CONFIG_PATH = os.path.join(APP_DIR, "steam_emu.ini")


class CaseConfigParser(configparser.RawConfigParser):
    def __init__(self):
        configparser.RawConfigParser.__init__(self)
        self.optionxform = str


def load_emulator_config():
    parser = CaseConfigParser()
    try:
        parser.read(EMU_CONFIG_PATH)
    except (configparser.Error, IOError, OSError):
        # A partial/manual extraction must still reach the launcher so the
        # user can repair settings instead of seeing a cx_Freeze traceback.
        parser = CaseConfigParser()
    if not parser.has_section("Settings"):
        parser.add_section("Settings")
    defaults = {
        "UserName": "Player",
        "Language": "english",
        "AppId": "224540",
    }
    for key, value in defaults.items():
        if not parser.has_option("Settings", key):
            parser.set("Settings", key, value)
    return parser


EMU_CONFIG = load_emulator_config()


try:
    TEXT_TYPE = unicode
except NameError:
    TEXT_TYPE = str


def launcher_executable_path():
    """Return a real Unicode path even under the frozen Python 2 runtime."""
    if os.name == "nt" and getattr(sys, "frozen", False):
        buffer = ctypes.create_unicode_buffer(32768)
        length = ctypes.windll.kernel32.GetModuleFileNameW(None, buffer, len(buffer))
        if length:
            return buffer.value

    path = os.path.abspath(__file__)
    if not isinstance(path, TEXT_TYPE):
        encoding = sys.getfilesystemencoding() or ("mbcs" if os.name == "nt" else "utf-8")
        path = path.decode(encoding, "replace")
    return path


def check_launcher_path():
    """Stop early when the recovered game cannot represent its install path."""
    if os.name != "nt":
        return
    path = launcher_executable_path()
    try:
        path.encode("ascii")
        return
    except UnicodeEncodeError:
        pass

    message = (
        u"Ace of Spades cannot start from a folder containing non-English "
        u"characters.\n\nCurrent path:\n%s\n\nMove the game to a path such as "
        u"C:\\Games\\AceOfSpades and try again."
    ) % path
    flags = 0x00000010 | 0x00010000 | 0x00040000
    ctypes.windll.user32.MessageBoxW(None, message, u"Unsupported installation path", flags)
    raise SystemExit(1)


def display_text(value):
    if isinstance(value, TEXT_TYPE):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return TEXT_TYPE(value)


def launcher_data_directory():
    """Return the writable per-user launcher directory."""
    root = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(root, "AoS Revival")


def launcher_log_path():
    """Return a per-user log without placing secrets beside the game."""
    return os.path.join(launcher_data_directory(), "logs", "launcher.log")


def eula_marker_path():
    """Store notice acceptance outside the game directory when possible."""
    return os.path.join(launcher_data_directory(), "eula_true")


def acquire_launcher_mutex():
    """Keep a second launcher from overwriting the active join identity."""
    global _LAUNCHER_MUTEX
    if os.name != "nt":
        return True
    mutex_name = u"Local\\AoSRevivalLauncherProtocol168"
    # Isolated build validation has its own config and LOCALAPPDATA state, so
    # it needs a separate mutex without weakening the production default.
    test_scope = os.environ.get("AOS_LAUNCHER_MUTEX_SCOPE")
    if test_scope:
        test_scope = re.sub(r"[^A-Za-z0-9_.-]", "_", test_scope)[:48]
        mutex_name += u"-" + test_scope
    create_mutex = ctypes.windll.kernel32.CreateMutexW
    create_mutex.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
    create_mutex.restype = ctypes.c_void_p
    handle = create_mutex(
        None,
        False,
        mutex_name,
    )
    if not handle:
        raise ctypes.WinError()
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        close_handle = ctypes.windll.kernel32.CloseHandle
        close_handle.argtypes = [ctypes.c_void_p]
        close_handle.restype = ctypes.c_int
        close_handle(handle)
        return False
    _LAUNCHER_MUTEX = handle
    return True


def append_launcher_log(event, exc_info=None):
    """Append a sanitized launcher event and optional traceback."""
    path = launcher_log_path()
    directory = os.path.dirname(path)
    try:
        if not os.path.isdir(directory):
            os.makedirs(directory)
        with codecs.open(path, "a", encoding="utf-8") as stream:
            stream.write(
                u"[%s] %s\n"
                % (display_text(time.strftime("%Y-%m-%d %H:%M:%S")), display_text(event))
            )
            if exc_info:
                for line in traceback.format_exception(*exc_info):
                    stream.write(display_text(line))
            stream.write(u"\n")
    except (IOError, OSError, UnicodeError, ValueError):
        # Diagnostics must never replace the original launcher failure.
        return None
    return path


def show_native_error(title, message):
    """Show a Unicode-safe error even before Tk has initialized."""
    title = display_text(title)
    message = display_text(message)
    if os.name == "nt":
        flags = 0x00000010 | 0x00010000 | 0x00040000
        ctypes.windll.user32.MessageBoxW(None, message, title, flags)
    else:
        try:
            sys.stderr.write(message + u"\n")
        except TypeError:
            sys.stderr.write((message + u"\n").encode("utf-8"))


def game_command(arguments):
    """Build the isolated client command for source and frozen launchers."""
    if getattr(sys, "frozen", False):
        return [sys.executable] + list(arguments)
    return [sys.executable, os.path.abspath(__file__)] + list(arguments)


def spawn_isolated_game(command):
    """Start one game child with valid, non-growing output handles.

    The frozen launcher is a Windows GUI executable and therefore has no
    usable console descriptors to inherit.  Stock client code still contains
    a few diagnostic ``print`` statements; inheriting the launcher's invalid
    stdout/stderr makes those otherwise harmless diagnostics raise
    ``IOError(EBADF)`` inside the game loop.  Route both streams to the null
    device and close the launcher's copy immediately after ``Popen`` has
    duplicated/inherited it for the child.
    """

    output_stream = None
    child_environment = os.environ.copy()
    # cx_Freeze initializes Python's standard streams before ``game_start``.
    # Give that bootstrap a valid codec as the first line of defense; the
    # in-process wrapper below remains authoritative because old Win32GUI
    # bases may still derive ``cp0`` from the absent console code page.
    # ``unicode_literals`` is enabled in this Python 2-compatible module, but
    # Python 2's Windows CreateProcess wrapper rejects Unicode environment
    # keys/values with ``TypeError: environment can only contain strings``.
    # ``str`` preserves native text on Python 3 and produces the required
    # byte strings in the retail Python 2 runtime.
    child_environment[str("PYTHONIOENCODING")] = str("utf-8")
    try:
        output_stream = open(os.devnull, "ab", 0)
        return subprocess.Popen(
            command,
            cwd=APP_DIR,
            env=child_environment,
            stdout=output_stream,
            stderr=subprocess.STDOUT,
        )
    finally:
        if output_stream is not None:
            try:
                output_stream.close()
            except (IOError, OSError):
                # A successful child must not become orphaned merely because
                # the parent could not close its duplicate null-device handle.
                pass


class _Utf8GameOutput(object):
    """Binary UTF-8 output used by the windowless frozen game process.

    cx_Freeze's Python 2 Win32GUI bootstrap derives ``sys.stdout.encoding``
    from the process console code page.  A GUI process has no console, so the
    Windows API reports code page zero and the bootstrap exposes the invalid
    codec name ``cp0``.  The first Unicode diagnostic then raises
    ``LookupError`` even when the OS handle itself was safely redirected.

    The isolated game does not have a visible console.  Encode diagnostics
    explicitly and write them to a binary sink so a print statement can never
    terminate packet processing.  ``encoding`` remains a real codec because
    Python 2's print statement consults it before calling ``write``.
    """

    encoding = "utf-8"
    errors = "replace"
    softspace = 0

    def __init__(self, stream):
        self._stream = stream

    @property
    def closed(self):
        return self._stream.closed

    def write(self, value):
        if value is None:
            return
        if isinstance(value, TEXT_TYPE):
            value = value.encode(self.encoding, self.errors)
        elif not isinstance(value, bytes):
            value = display_text(value).encode(self.encoding, self.errors)
        try:
            self._stream.write(value)
        except (IOError, OSError, ValueError):
            # Diagnostics are intentionally best-effort in the GUI child.
            return

    def flush(self):
        try:
            self._stream.flush()
        except (IOError, OSError, ValueError):
            return

    def fileno(self):
        return self._stream.fileno()

    def isatty(self):
        return False

    def close(self):
        try:
            self._stream.close()
        except (IOError, OSError, ValueError):
            return


def install_game_output_streams():
    """Replace GUI-child stdout/stderr before importing recovered game code.

    The launcher log is written independently with ``codecs.open`` and is not
    affected.  Both streams use separate unbuffered handles so closing or
    redirecting one (for example by Twisted debug logging) cannot invalidate
    the other.
    """

    output_stream = _Utf8GameOutput(open(os.devnull, "wb", 0))
    error_stream = _Utf8GameOutput(open(os.devnull, "wb", 0))
    sys.stdout = output_stream
    sys.stderr = error_stream


def missing_game_files():
    """List essential client files absent from this install.

    The PyInstaller release packs the Python client code into ``aos.pkg``
    (loaded by the bootloader), so there is no loose ``lib/run.py`` to probe as
    the old cx_Freeze layout had. Verify the packaged archive plus the loose
    asset folders that a partial extraction would drop; when running from source
    the client modules are loose ``.py`` files instead.
    """
    required = [
        os.path.join(APP_DIR, "config.txt"),
        os.path.join(APP_DIR, "png"),
        os.path.join(APP_DIR, "sounds"),
        os.path.join(APP_DIR, "maps"),
    ]
    if getattr(sys, "frozen", False):
        required.append(os.path.join(APP_DIR, "aos.pkg"))
    else:
        required.append(os.path.join(APP_DIR, "run.py"))
        required.append(os.path.join(APP_DIR, "aoslib", "run.py"))
    return [path for path in required if not os.path.exists(path)]


def account_display(account):
    """Return fully Unicode launcher labels for a persisted account payload."""
    nickname = display_text(
        account.get("nickname") or account.get("username") or "Player"
    )
    ranked = bool(account.get("ranked_eligible"))
    if account.get("offline"):
        profile_kind = "OFFLINE GUEST"
    else:
        profile_kind = "RANKED PROFILE" if ranked else "PERSISTENT GUEST"
    legacy_id = display_text(account.get("legacy_id") or "—")
    return nickname.upper(), u"%s  •  ID %s" % (profile_kind, legacy_id)


def server_supports_join_tickets(server):
    """Return whether a discovered server can consume the 15-byte join code.

    The code is a transport credential, not a player nickname. Sending it to
    an A2S-only host exposes the temporary ``~...`` value and usually causes
    rejection. A server must explicitly advertise the identity bridge.
    """

    if not isinstance(server, dict):
        return False
    tags = server.get("tags") or []
    if not isinstance(tags, (list, tuple)):
        return False
    return any(
        display_text(tag).strip().lower() == "identity=ticket-v1"
        for tag in tags
    )


def emulator_value(name, fallback=""):
    try:
        # ConfigParser returns UTF-8 byte strings in the shipped Python 2
        # runtime. Normalize at the boundary so even a localized legacy name
        # cannot trigger implicit ASCII coercion during launcher startup.
        return display_text(EMU_CONFIG.get("Settings", name))
    except (configparser.Error, ValueError):
        return display_text(fallback)


def save_emulator_config(nickname, language):
    """Persist emulator settings as UTF-8 with an atomic Windows replacement."""
    EMU_CONFIG.set("Settings", "UserName", display_text(nickname))
    EMU_CONFIG.set("Settings", "Language", display_text(language))
    temporary = EMU_CONFIG_PATH + ".tmp"
    try:
        with codecs.open(temporary, "w", encoding="utf-8") as stream:
            defaults = getattr(EMU_CONFIG, "_defaults", {})
            if defaults:
                stream.write(u"[%s]\n" % display_text(configparser.DEFAULTSECT))
                for key, value in defaults.items():
                    stream.write(
                        u"%s=%s\n"
                        % (
                            display_text(key),
                            display_text(value).replace(u"\n", u"\n\t"),
                        )
                    )
                stream.write(u"\n")
            for section in EMU_CONFIG.sections():
                stream.write(u"[%s]\n" % display_text(section))
                values = getattr(EMU_CONFIG, "_sections", {}).get(section, {})
                for key, value in values.items():
                    if key == "__name__":
                        continue
                    stream.write(
                        u"%s=%s\n"
                        % (
                            display_text(key),
                            display_text(value).replace(u"\n", u"\n\t"),
                        )
                    )
                stream.write(u"\n")
            stream.flush()
            try:
                os.fsync(stream.fileno())
            except (AttributeError, OSError):
                pass

        if os.name == "nt":
            replace_existing = 0x1
            write_through = 0x8
            moved = ctypes.windll.kernel32.MoveFileExW(
                display_text(temporary),
                display_text(EMU_CONFIG_PATH),
                replace_existing | write_through,
            )
            if not moved:
                raise ctypes.WinError()
        else:
            if os.path.exists(EMU_CONFIG_PATH):
                os.remove(EMU_CONFIG_PATH)
            os.rename(temporary, EMU_CONFIG_PATH)
    except Exception:
        try:
            if os.path.exists(temporary):
                os.remove(temporary)
        except (IOError, OSError):
            pass
        raise


def available_languages():
    candidates = [
        os.path.join(APP_DIR, "aoslib", "strings"),
        os.path.join(APP_DIR, "lib", "aoslib", "strings"),
    ]
    values = set()
    for directory in candidates:
        if not os.path.isdir(directory):
            continue
        for name in os.listdir(directory):
            stem, extension = os.path.splitext(name)
            if extension.lower() in (".py", ".pyc") and stem != "__init__":
                values.add(stem)
    return sorted(values) or ["english"]


def normalize_server_address(value):
    value = str(value or "").strip()
    if value.lower() == "local":
        return "127.0.0.1:27015"
    if not re.match(r"^[A-Za-z0-9.-]+:[0-9]{1,5}$", value):
        raise ValueError("Use a host and port, for example play.example.com:32887")
    host, raw_port = value.rsplit(":", 1)
    port = int(raw_port)
    if not host or not 1 <= port <= 65535:
        raise ValueError("The server address or port is invalid.")
    return "%s:%s" % (host, port)


class CanvasButton(object):
    def __init__(
        self,
        launcher,
        x,
        y,
        width,
        height,
        text,
        command,
        accent=False,
        small=False,
    ):
        self.launcher = launcher
        self.canvas = launcher.canvas
        self.command = command
        self.enabled = True
        self.accent = accent
        self.base = RED if accent else OLIVE
        self.hover = "#ff5a2b" if accent else "#7e8939"
        self.pressed = "#b73217" if accent else OLIVE_DARK
        self.rect = self.canvas.create_rectangle(
            x,
            y,
            x + width,
            y + height,
            fill=self.base,
            outline=INK,
            width=3,
        )
        self.top_line = self.canvas.create_line(
            x + 3, y + 3, x + width - 3, y + 3, fill=GOLD, width=2
        )
        font_size = 10 if small else 14
        self.label = self.canvas.create_text(
            x + width // 2,
            y + height // 2 + 1,
            text=text,
            fill=CREAM,
            font=("Arial Narrow", font_size, "bold"),
        )
        self.items = (self.rect, self.top_line, self.label)
        for item in self.items:
            self.canvas.tag_bind(item, "<Enter>", self._enter)
            self.canvas.tag_bind(item, "<Leave>", self._leave)
            self.canvas.tag_bind(item, "<ButtonPress-1>", self._press)
            self.canvas.tag_bind(item, "<ButtonRelease-1>", self._release)

    def _enter(self, event=None):
        if self.enabled:
            self.canvas.itemconfig(self.rect, fill=self.hover)
            self.canvas.config(cursor="hand2")

    def _leave(self, event=None):
        self.canvas.itemconfig(self.rect, fill=self.base if self.enabled else "#494b3e")
        self.canvas.config(cursor="")

    def _press(self, event=None):
        if self.enabled:
            self.canvas.itemconfig(self.rect, fill=self.pressed)

    def _release(self, event=None):
        if not self.enabled:
            return
        self.canvas.itemconfig(self.rect, fill=self.hover)
        if callable(self.command):
            self.command()

    def set_text(self, value):
        self.canvas.itemconfig(self.label, text=value)

    def set_command(self, command):
        self.command = command

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
        color = self.base if self.enabled else "#494b3e"
        text_color = CREAM if self.enabled else "#8e8e82"
        self.canvas.itemconfig(self.rect, fill=color)
        self.canvas.itemconfig(self.label, fill=text_color)


class Launcher(object):
    WIDTH = 1000
    HEIGHT = 700

    def __init__(self, root):
        self.root = root
        self.api = RevivalClient()
        self.servers = []
        self.busy = False
        self._ui_queue = queue.Queue()
        self._game_process = None
        self._game_started_at = None
        self._previous_emulator = None
        self.debug_enabled = "+debug" in sys.argv
        self.legacy_name = emulator_value("UserName", "Player")
        if self.legacy_name.startswith("~"):
            self.legacy_name = "Player"
        self.language = emulator_value("Language", "english")

        root.title("Ace of Spades Revival — Battle Builder Launcher")
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.report_callback_exception = self._handle_callback_exception
        self._center()
        icon_path = os.path.join(APP_DIR, "game.ico")
        if os.name == "nt" and os.path.isfile(icon_path):
            try:
                root.iconbitmap(icon_path)
            except tk.TclError:
                pass

        self.canvas = tk.Canvas(
            root,
            width=self.WIDTH,
            height=self.HEIGHT,
            bd=0,
            highlightthickness=0,
            bg=PANEL,
        )
        self.canvas.pack()
        self.root.after(50, self._drain_ui_queue)
        self._draw_background()
        self._draw_interface()
        self._bind_shortcuts()
        self._render_account()
        # Discovery enriches the launcher but must never gate the preserved
        # game. Keep every local launch control active during an outage.
        self.refresh_servers(quiet=True)
        if self.api.access_token:
            self._run_async("Checking account…", self.api.refresh_identity, self._identity_refreshed, quiet=True)

    def _center(self):
        self.root.update_idletasks()
        x = max((self.root.winfo_screenwidth() - self.WIDTH) // 2, 0)
        y = max((self.root.winfo_screenheight() - self.HEIGHT) // 2, 0)
        self.root.geometry("%dx%d+%d+%d" % (self.WIDTH, self.HEIGHT, x, y))

    def _draw_background(self):
        # Tk 8.5 (the bundled runtime) only decodes GIF and PPM/PGM in
        # PhotoImage, not PNG, so ship the launcher background as a PPM sized to
        # the window. Try PPM first, then GIF, then PNG (for a Tk 8.6 dev run).
        self._background_original = None
        for candidate in (
            os.path.join(ASSET_DIR, "background.ppm"),
            os.path.join(ASSET_DIR, "background.gif"),
            os.path.join(ASSET_DIR, "background.png"),
        ):
            if not os.path.isfile(candidate):
                continue
            try:
                self._background_original = tk.PhotoImage(file=candidate)
                break
            except tk.TclError:
                continue
        if self._background_original is not None:
            # The PPM is authored at the window size, so draw it 1:1.
            self.background = self._background_original
            self.canvas.create_image(0, 0, image=self.background, anchor="nw")
        else:
            self.background = None
            self.canvas.create_rectangle(0, 0, self.WIDTH, self.HEIGHT, fill=OLIVE_DARK, outline="")
            append_launcher_log(
                "Launcher background is missing; using the safe solid-color fallback."
            )
        self.canvas.create_rectangle(500, 145, 980, 683, fill=PANEL, outline=INK, width=4)
        self.canvas.create_rectangle(510, 155, 970, 673, fill="", outline=OLIVE, width=2)

    def _draw_interface(self):
        self.canvas.create_text(
            740,
            168,
            text="REVIVAL COMMAND CENTER",
            fill=GOLD_LIGHT,
            font=("Impact", 21),
        )
        self.canvas.create_text(
            740,
            195,
            text="BUILD  •  BATTLE  •  REBUILD",
            fill=MUTED,
            font=("Arial", 9, "bold"),
        )

        self.canvas.create_rectangle(525, 214, 955, 277, fill=PANEL_LIGHT, outline=OLIVE_DARK, width=2)
        self.account_dot = self.canvas.create_oval(539, 228, 551, 240, fill=RED, outline=INK)
        self.account_title = self.canvas.create_text(
            560, 226, anchor="nw", text="NOT SIGNED IN", fill=CREAM, font=("Arial", 11, "bold")
        )
        self.account_detail = self.canvas.create_text(
            560, 248, anchor="nw", text="Sign in or create a persistent guest.", fill=MUTED, font=("Arial", 9)
        )
        self.account_primary = CanvasButton(self, 786, 225, 76, 35, "SIGN IN", self.open_identity_dialog, small=True)
        self.account_secondary = CanvasButton(self, 868, 225, 76, 35, "GUEST", self.play_as_guest, small=True)

        self.canvas.create_text(527, 295, anchor="w", text="ACTIVE BATTLEFIELDS", fill=GOLD_LIGHT, font=("Arial", 10, "bold"))
        self.refresh_button = CanvasButton(self, 884, 283, 70, 26, "REFRESH", self.refresh_servers, small=True)

        list_frame = tk.Frame(self.root, bg=OLIVE_DARK, bd=0, highlightthickness=0)
        self.server_list = tk.Listbox(
            list_frame,
            bg="#181b15",
            fg=CREAM,
            selectbackground=OLIVE,
            selectforeground="#ffffff",
            activestyle="none",
            bd=0,
            highlightthickness=1,
            highlightbackground=OLIVE,
            highlightcolor=GOLD,
            font=("Consolas", 10),
            exportselection=False,
            takefocus=True,
        )
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.server_list.yview)
        self.server_list.configure(yscrollcommand=scrollbar.set)
        self.server_list.pack(side="left", fill="both", expand=True, padx=(2, 0), pady=2)
        scrollbar.pack(side="right", fill="y", padx=(0, 2), pady=2)
        self.canvas.create_window(525, 313, width=430, height=145, anchor="nw", window=list_frame)
        self.server_list.bind("<Double-Button-1>", lambda event: self.join_selected())

        self.status_text = self.canvas.create_text(
            527,
            469,
            anchor="w",
            text="Ready.",
            fill=MUTED,
            font=("Arial", 9),
        )

        self.join_button = CanvasButton(self, 525, 488, 430, 48, "JOIN SELECTED SERVER", self.join_selected, accent=True)
        self.menu_button = CanvasButton(self, 525, 548, 136, 39, "MAIN MENU", self.play_main_menu, small=True)
        self.local_button = CanvasButton(self, 672, 548, 136, 39, "LOCAL SERVER", self.join_local, small=True)
        self.direct_button = CanvasButton(self, 819, 548, 136, 39, "DIRECT CONNECT", self.direct_connect, small=True)
        self.steam_button = CanvasButton(self, 525, 597, 210, 36, "PLAY OFFICIAL STEAM", self.open_official_steam, small=True)
        self.settings_button = CanvasButton(self, 745, 597, 100, 36, "SETTINGS", self.open_settings, small=True)
        self.site_button = CanvasButton(self, 855, 597, 100, 36, "WEBSITE", lambda: webbrowser.open(SITE_URL), small=True)

        self.canvas.create_text(
            525,
            652,
            anchor="w",
            text="F5 refresh  •  Enter join  •  Ctrl+L direct  •  Ctrl+I identity",
            fill="#898970",
            font=("Arial", 8),
        )
        self.discord_hotspot = self.canvas.create_text(
            952,
            652,
            anchor="e",
            text="DISCORD ↗",
            fill=GOLD_LIGHT,
            font=("Arial", 9, "bold"),
        )
        self.canvas.tag_bind(self.discord_hotspot, "<Button-1>", lambda event: webbrowser.open(DISCORD_URL))
        self.canvas.tag_bind(self.discord_hotspot, "<Enter>", lambda event: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind(self.discord_hotspot, "<Leave>", lambda event: self.canvas.config(cursor=""))

    def _bind_shortcuts(self):
        self.root.bind("<F5>", lambda event: self.refresh_servers())
        self.root.bind("<Return>", lambda event: self.join_selected())
        self.root.bind("<Control-l>", lambda event: self.direct_connect())
        self.root.bind("<Control-i>", lambda event: self.open_identity_dialog())
        self.root.bind("<Control-g>", lambda event: self.play_as_guest())
        self.root.bind("<Alt-m>", lambda event: self.play_main_menu())
        self.root.bind("<Escape>", lambda event: self.close())

    def set_status(self, text, error=False):
        self.canvas.itemconfig(
            self.status_text,
            text=display_text(text),
            fill=RED if error else MUTED,
        )

    def _handle_callback_exception(self, error_type, error, trace):
        """Turn otherwise invisible Tk callback errors into an actionable report."""
        path = append_launcher_log(
            "Unhandled Tk callback error: %s" % display_text(error),
            (error_type, error, trace),
        )
        message = (
            u"The launcher recovered from an unexpected interface error.\n\n"
            u"Details were written to:\n%s"
        ) % display_text(path or launcher_log_path())
        try:
            self.set_status(display_text(error) or "Unexpected launcher error.", error=True)
            messagebox.showerror("AoS Revival", message, parent=self.root)
        except tk.TclError:
            show_native_error("AoS Revival", message)

    def _post_to_ui(self, callback):
        """Queue a callback without invoking Tcl from a worker thread."""
        self._ui_queue.put(callback)

    def _drain_ui_queue(self):
        """Execute completed network work exclusively on Tk's main thread."""
        while True:
            try:
                callback = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            try:
                callback()
            except Exception:
                self._handle_callback_exception(*sys.exc_info())
        try:
            self.root.after(50, self._drain_ui_queue)
        except tk.TclError:
            return

    def _set_busy(self, busy):
        self.busy = bool(busy)
        for button in (
            self.refresh_button,
            self.join_button,
            self.menu_button,
            self.local_button,
            self.direct_button,
            self.account_primary,
            self.account_secondary,
        ):
            button.set_enabled(not self.busy)

    def _run_async(
        self,
        label,
        operation,
        callback,
        quiet=False,
        error_callback=None,
    ):
        if self.busy and not quiet:
            return
        if not quiet:
            self._set_busy(True)
        self.set_status(label)

        def worker():
            try:
                outcome = (True, operation())
            except Exception as error:
                outcome = (False, error)
            self._post_to_ui(lambda value=outcome: complete(value))

        def complete(outcome):
            if not quiet:
                self._set_busy(False)
            success, value = outcome
            if success:
                callback(value)
            else:
                if error_callback is not None:
                    error_callback(value)
                    return
                message = display_text(value) or "Unexpected launcher error."
                if quiet:
                    append_launcher_log("Background service check failed: %s" % message)
                    return
                self.set_status(message, error=True)
                messagebox.showerror("AoS Revival", message, parent=self.root)

        thread = threading.Thread(target=worker, name="aos-revival-request")
        thread.daemon = True
        thread.start()

    def _render_account(self):
        account = self.api.account
        if account:
            nickname, detail = account_display(account)
            offline = bool(account.get("offline"))
            self.canvas.itemconfig(self.account_dot, fill=GOLD if offline else GREEN)
            self.canvas.itemconfig(self.account_title, text=nickname)
            self.canvas.itemconfig(self.account_detail, text=detail)
            self.account_primary.set_text("SYNC" if offline else "ACCOUNT")
            self.account_primary.set_command(
                self.play_as_guest if offline else self.show_account
            )
            self.account_secondary.set_text("LOG OUT")
            self.account_secondary.set_command(self.logout)
        else:
            self.canvas.itemconfig(self.account_dot, fill=RED)
            self.canvas.itemconfig(self.account_title, text="NOT SIGNED IN")
            self.canvas.itemconfig(self.account_detail, text="Sign in for ranked stats, or create a persistent guest.")
            self.account_primary.set_text("SIGN IN")
            self.account_primary.set_command(self.open_identity_dialog)
            self.account_secondary.set_text("GUEST")
            self.account_secondary.set_command(self.play_as_guest)

    def _identity_refreshed(self, account):
        self._render_account()
        if account:
            self.set_status("Account verified. Choose a battlefield.")

    def refresh_servers(self, quiet=False):
        self.server_list.delete(0, "end")
        self.server_list.insert("end", "  Checking the Revival master…")
        self._run_async(
            "Calling the Revival master server…",
            self.api.servers,
            self._servers_loaded,
            quiet=quiet,
            error_callback=self._servers_unavailable,
        )

    def _servers_unavailable(self, error):
        self.servers = []
        self.server_list.delete(0, "end")
        if service_unavailable(error):
            self.server_list.insert(
                "end",
                "  Master offline — Main Menu, Local Server and Direct Connect still work",
            )
            self.set_status(
                "Offline mode ready. Public discovery and ranked tickets are unavailable."
            )
            return
        message = display_text(error) or "Server discovery is unavailable."
        self.server_list.insert(
            "end",
            "  Server discovery unavailable — local play still works",
        )
        self.set_status(message, error=True)

    def _servers_loaded(self, servers):
        self.servers = list(servers)
        self.server_list.delete(0, "end")
        for server in self.servers:
            name = display_text(server.get("name") or "AoS Revival Server")[:25]
            players = "%s/%s" % (server.get("players", 0), server.get("max_players", 0))
            map_name = display_text(server.get("map") or "unknown")[:12]
            mode = display_text(server.get("mode_tla") or server.get("game_mode") or "").upper()[:5]
            official = u"★" if server.get("official") else u"•"
            self.server_list.insert(
                "end",
                u"%s %-25s %7s  %-12s %s" % (official, name, players, map_name, mode),
            )
        if self.servers:
            self.server_list.selection_set(0)
            self.server_list.activate(0)
            self.set_status("%s live server%s found." % (len(self.servers), "" if len(self.servers) == 1 else "s"))
        else:
            self.server_list.insert("end", "  No live heartbeats yet — try Local Server or Direct Connect")
            self.set_status("No public servers are advertising right now.")

    def selected_server(self):
        selection = self.server_list.curselection()
        if not selection or not self.servers:
            return None
        index = int(selection[0])
        return self.servers[index] if index < len(self.servers) else None

    def require_identity(self):
        if self.api.account and self.api.access_token:
            return True
        messagebox.showinfo(
            "Identity required",
            "Choose SIGN IN for a ranked profile or GUEST for a persistent guest identity before joining directly.",
            parent=self.root,
        )
        self.open_identity_dialog()
        return False

    def join_selected(self):
        if self.busy:
            return
        server = self.selected_server()
        if not server:
            messagebox.showinfo("AoS Revival", "Select a live server first, or use Direct Connect.", parent=self.root)
            return
        identifier = display_text(server.get("identifier"))
        if server_supports_join_tickets(server):
            self._join_authenticated(identifier)
            return
        self._launch_unranked(identifier, "A2S-only server")

    def join_local(self):
        self._launch_unranked("127.0.0.1:27015", "local server")

    def direct_connect(self):
        value = simpledialog.askstring(
            "Direct Connect",
            "Server address (host:port)",
            initialvalue=self.api.state.get("last_server") or "127.0.0.1:27015",
            parent=self.root,
        )
        if not value:
            return
        try:
            identifier = normalize_server_address(value)
        except ValueError as error:
            messagebox.showerror("Invalid address", str(error), parent=self.root)
            return
        self._join_direct(identifier)

    def _preferred_play_name(self):
        account = self.api.account or {}
        return display_text(
            account.get("nickname") or self.legacy_name or "Player"
        )

    def _remember_server(self, identifier):
        self.api.state["last_server"] = identifier
        try:
            from revival_store import save_state
            save_state(self.api.state)
        except (IOError, OSError, TypeError, ValueError) as error:
            append_launcher_log(
                "Could not remember the last direct server: %s"
                % display_text(error)
            )

    def _launch_unranked(self, identifier, reason="offline fallback"):
        self._remember_server(identifier)
        append_launcher_log(
            "Launching unranked %s connection to %s without a master ticket."
            % (display_text(reason), display_text(identifier))
        )
        self._launch_game(self._preferred_play_name(), identifier)

    def _join_direct(self, identifier):
        discovered = next(
            (
                server for server in getattr(self, "servers", [])
                if display_text(server.get("identifier")) == identifier
            ),
            None,
        )
        if (
            discovered is not None
            and server_supports_join_tickets(discovered)
            and
            self.api.account
            and self.api.access_token
            and self.api.service_available is True
        ):
            self._join_authenticated(identifier)
            return
        self._launch_unranked(identifier, "direct")

    def _join_authenticated(self, identifier):
        try:
            identifier = normalize_server_address(identifier)
        except ValueError as error:
            messagebox.showerror("Invalid address", str(error), parent=self.root)
            return
        if not self.require_identity():
            return

        def request_ticket():
            return self.api.game_ticket(identifier)

        def ticket_ready(ticket):
            self._remember_server(identifier)
            self._launch_game(ticket, identifier)

        def ticket_failed(error):
            if service_unavailable(error):
                self._launch_unranked(identifier, "master-outage fallback")
                return
            message = display_text(error) or "Could not create a ranked join ticket."
            self.set_status(message, error=True)
            messagebox.showerror("AoS Revival", message, parent=self.root)

        self._run_async(
            "Forging a one-use join pass for %s…" % identifier,
            request_ticket,
            ticket_ready,
            error_callback=ticket_failed,
        )

    def play_main_menu(self):
        self._launch_game(self._preferred_play_name(), None)

    def _launch_game(self, wire_name, identifier):
        if self._game_process is not None:
            messagebox.showinfo(
                "AoS Revival",
                "The game client is already running.",
                parent=self.root,
            )
            return
        missing = missing_game_files()
        if missing:
            append_launcher_log(
                "Game extraction is incomplete: %s"
                % ", ".join(display_text(path) for path in missing)
            )
            messagebox.showerror(
                "Incomplete Ace of Spades installation",
                "Required game files are missing. Re-extract or rebuild the complete "
                "client before launching.\n\n%s"
                % u"\n".join(display_text(path) for path in missing),
                parent=self.root,
            )
            return
        wire_name = display_text(wire_name)
        try:
            wire_bytes = wire_name.encode("utf-8")
        except AttributeError:
            wire_bytes = str(wire_name)
        if len(wire_bytes) > 15:
            wire_bytes = wire_bytes[:15]
            while True:
                try:
                    wire_name = wire_bytes.decode("utf-8")
                    break
                except UnicodeDecodeError:
                    wire_bytes = wire_bytes[:-1]
        previous_name = emulator_value("UserName", self.legacy_name or "Player")
        if display_text(previous_name).startswith("~"):
            previous_name = self.legacy_name or "Player"
        self._previous_emulator = (previous_name, self.language)
        try:
            save_emulator_config(wire_name, self.language)
        except (IOError, OSError, configparser.Error, UnicodeError) as error:
            self._previous_emulator = None
            append_launcher_log(
                "Could not save game identity settings: %s" % display_text(error),
                sys.exc_info(),
            )
            messagebox.showerror(
                "Cannot start Ace of Spades",
                "The launcher could not update steam_emu.ini. Check that the game "
                "folder is writable and try again.\n\n%s" % display_text(error),
                parent=self.root,
            )
            return

        arguments = self._game_arguments(identifier)
        command = game_command(arguments)
        self.set_status("Deploying to %s…" % (identifier or "the main menu"))
        self.root.update_idletasks()
        try:
            self._game_process = spawn_isolated_game(command)
        except (IOError, OSError, ValueError) as error:
            append_launcher_log(
                "Could not create game process: %s" % display_text(error),
                sys.exc_info(),
            )
            self._restore_emulator_identity()
            messagebox.showerror(
                "Cannot start Ace of Spades",
                "The recovered game process could not be started.\n\n%s\n\nLog: %s"
                % (display_text(error), launcher_log_path()),
                parent=self.root,
            )
            return

        self._game_started_at = time.time()
        append_launcher_log(
            "Started isolated game process pid=%s target=%s"
            % (self._game_process.pid, display_text(identifier or "main-menu"))
        )
        self.root.withdraw()
        self.root.after(250, self._poll_game_process)

    def _game_arguments(self, identifier):
        arguments = ["+s"]
        if identifier:
            arguments.extend(["+connect", identifier])
        if self.debug_enabled:
            arguments.append("+debug")
        return arguments

    def _restore_emulator_identity(self):
        previous = self._previous_emulator
        self._previous_emulator = None
        if not previous:
            return
        try:
            save_emulator_config(previous[0], previous[1])
        except (IOError, OSError, configparser.Error, UnicodeError):
            append_launcher_log(
                "Could not restore the display name after game shutdown.",
                sys.exc_info(),
            )

    @staticmethod
    def _exit_code_text(exit_code):
        unsigned = int(exit_code) & 0xFFFFFFFF
        if unsigned == 0xC0000005:
            return "access violation (0xC0000005)"
        if unsigned == 1:
            return "game bootstrap error (exit code 1)"
        return "%s (0x%08X)" % (exit_code, unsigned)

    def _poll_game_process(self):
        process = self._game_process
        if process is None:
            return
        exit_code = process.poll()
        if exit_code is None:
            try:
                self.root.after(250, self._poll_game_process)
            except tk.TclError:
                return
            return

        duration = max(0.0, time.time() - (self._game_started_at or time.time()))
        self._game_process = None
        self._game_started_at = None
        self._restore_emulator_identity()
        try:
            self.root.deiconify()
            self.root.lift()
        except tk.TclError:
            return

        if int(exit_code) == 0:
            self.set_status("Game closed normally. Ready for another deployment.")
            append_launcher_log("Game process exited normally after %.1f seconds." % duration)
            return

        code_text = self._exit_code_text(exit_code)
        append_launcher_log(
            "Game process failed after %.1f seconds with %s." % (duration, code_text)
        )
        self.set_status("Game process failed: %s" % code_text, error=True)
        messagebox.showerror(
            "Ace of Spades stopped unexpectedly",
            "The game process stopped with %s. The launcher stayed alive and "
            "restored your profile settings.\n\nDiagnostic log:\n%s"
            % (code_text, launcher_log_path()),
            parent=self.root,
        )

    def play_as_guest(self):
        account = self.api.account or {}
        self._run_async(
            "Securing this installation's guest identity…",
            lambda: self.api.guest_login(
                self.legacy_name,
                force_online=bool(account.get("offline")),
            ),
            self._guest_ready,
        )

    def _guest_ready(self, response):
        self._render_account()
        nickname = (response.get("account") or {}).get("nickname", "Guest")
        if response.get("offline"):
            self.set_status(
                "%s is ready offline. Main Menu, Local Server and Direct Connect are available."
                % nickname
            )
        else:
            self.set_status("%s is ready. Guest progress is durable but unranked." % nickname)

    def logout(self):
        self._run_async("Signing out…", self.api.logout, lambda result: self._logout_ready())

    def _logout_ready(self):
        self._render_account()
        self.set_status("Signed out. Your local guest key is still protected on this PC.")

    def show_account(self):
        account = self.api.account or {}
        lines = [
            "Nickname: %s" % account.get("nickname", "—"),
            "Profile ID: %s" % account.get("legacy_id", "—"),
            "Identity: %s" % account.get("identity_type", "—"),
            "Ranked: %s" % ("yes" if account.get("ranked_eligible") else "no (guest)"),
        ]
        messagebox.showinfo("Revival account", "\n".join(lines), parent=self.root)

    def open_identity_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Revival Identity")
        dialog.resizable(False, False)
        dialog.configure(bg=PANEL)
        dialog.transient(self.root)
        dialog.grab_set()
        tk.Label(dialog, text="CLAIM YOUR CALLSIGN", bg=PANEL, fg=GOLD_LIGHT, font=("Impact", 18)).grid(row=0, column=0, columnspan=2, padx=24, pady=(20, 6))
        tk.Label(dialog, text="No email required. Save the recovery code shown after registration.", bg=PANEL, fg=MUTED, font=("Arial", 9)).grid(row=1, column=0, columnspan=2, padx=24, pady=(0, 16))
        tk.Label(dialog, text="Username", bg=PANEL, fg=CREAM, anchor="w").grid(row=2, column=0, sticky="w", padx=(24, 10), pady=6)
        username = tk.Entry(dialog, width=27, bg="#f5ebbc", fg=INK, bd=2, relief="flat", font=("Arial", 11))
        username.grid(row=2, column=1, padx=(0, 24), pady=6)
        tk.Label(dialog, text="Password", bg=PANEL, fg=CREAM, anchor="w").grid(row=3, column=0, sticky="w", padx=(24, 10), pady=6)
        password = tk.Entry(dialog, width=27, show="•", bg="#f5ebbc", fg=INK, bd=2, relief="flat", font=("Arial", 11))
        password.grid(row=3, column=1, padx=(0, 24), pady=6)
        status = tk.Label(dialog, text="", bg=PANEL, fg=RED, font=("Arial", 9), wraplength=340)
        status.grid(row=4, column=0, columnspan=2, padx=24, pady=(5, 0))

        actions = tk.Frame(dialog, bg=PANEL)
        actions.grid(row=5, column=0, columnspan=2, padx=24, pady=18)

        def submit(mode):
            name = username.get().strip()
            secret = password.get()
            if not name or not secret:
                status.config(text="Enter both username and password.")
                return
            login_button.config(state="disabled")
            register_button.config(state="disabled")

            def operation():
                return self.api.register(name, secret) if mode == "register" else self.api.login(name, secret)

            def complete(outcome):
                success, value = outcome
                if success:
                    dialog.grab_release()
                    dialog.destroy()
                    self._render_account()
                    self.set_status("Welcome, %s." % (self.api.account or {}).get("nickname", name))
                    recovery = value.get("recovery_code")
                    if recovery:
                        self.root.clipboard_clear()
                        self.root.clipboard_append(recovery)
                        messagebox.showinfo(
                            "Save your recovery code",
                            "Your one-time recovery code has been copied to the clipboard:\n\n%s\n\nStore it somewhere safe. We do not collect an email address." % recovery,
                            parent=self.root,
                        )
                else:
                    status.config(text=display_text(value))
                    login_button.config(state="normal")
                    register_button.config(state="normal")

            def worker():
                try:
                    result = (True, operation())
                except Exception as error:
                    result = (False, error)
                self._post_to_ui(lambda result=result: complete(result))

            thread = threading.Thread(target=worker, name="aos-revival-identity")
            thread.daemon = True
            thread.start()

        login_button = tk.Button(actions, text="SIGN IN", command=lambda: submit("login"), bg=OLIVE, fg=CREAM, activebackground="#7e8939", relief="flat", width=13, font=("Arial", 10, "bold"))
        login_button.pack(side="left", padx=5)
        register_button = tk.Button(actions, text="CREATE ACCOUNT", command=lambda: submit("register"), bg=RED, fg="white", activebackground="#ff5a2b", relief="flat", width=16, font=("Arial", 10, "bold"))
        register_button.pack(side="left", padx=5)
        recover_button = tk.Button(dialog, text="Use recovery code", command=lambda: self.open_recovery_dialog(dialog), bg=PANEL, fg=GOLD_LIGHT, activebackground=PANEL_LIGHT, activeforeground=CREAM, relief="flat", font=("Arial", 9, "underline"))
        recover_button.grid(row=6, column=0, columnspan=2, pady=(0, 18))
        username.focus_set()
        dialog.bind("<Return>", lambda event: submit("login"))
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + (self.WIDTH - dialog.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.HEIGHT - dialog.winfo_height()) // 2
        dialog.geometry("+%d+%d" % (x, y))

    def open_recovery_dialog(self, parent_dialog=None):
        username = simpledialog.askstring("Recover profile", "Username", parent=parent_dialog or self.root)
        if not username:
            return
        code = simpledialog.askstring("Recover profile", "Recovery code", parent=parent_dialog or self.root)
        if not code:
            return
        password = simpledialog.askstring("Recover profile", "New password", show="•", parent=parent_dialog or self.root)
        if not password:
            return

        def recovered(response):
            if parent_dialog:
                try:
                    parent_dialog.grab_release()
                    parent_dialog.destroy()
                except tk.TclError:
                    pass
            self._render_account()
            replacement = response.get("recovery_code")
            messagebox.showinfo(
                "Profile recovered",
                "Password changed. Save your replacement recovery code:\n\n%s" % replacement,
                parent=self.root,
            )

        self._run_async(
            "Recovering profile…",
            lambda: self.api.recover(username, code, password),
            recovered,
        )

    def open_settings(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Launcher Settings")
        dialog.resizable(False, False)
        dialog.configure(bg=PANEL)
        dialog.transient(self.root)
        dialog.grab_set()
        tk.Label(dialog, text="FIELD KIT", bg=PANEL, fg=GOLD_LIGHT, font=("Impact", 18)).grid(row=0, column=0, columnspan=2, padx=24, pady=(20, 14))
        tk.Label(dialog, text="Legacy display name", bg=PANEL, fg=CREAM).grid(row=1, column=0, sticky="w", padx=24, pady=6)
        name_entry = tk.Entry(dialog, width=24, bg="#f5ebbc", fg=INK, relief="flat")
        name_entry.insert(0, self.legacy_name)
        name_entry.grid(row=1, column=1, padx=(0, 24), pady=6)
        tk.Label(dialog, text="Language", bg=PANEL, fg=CREAM).grid(row=2, column=0, sticky="w", padx=24, pady=6)
        language_value = tk.StringVar()
        languages = available_languages()
        language_value.set(self.language if self.language in languages else languages[0])
        combo = ttk.Combobox(dialog, textvariable=language_value, values=languages, state="readonly", width=21)
        combo.grid(row=2, column=1, padx=(0, 24), pady=6)
        debug_value = tk.IntVar(value=1 if self.debug_enabled else 0)
        tk.Checkbutton(dialog, text="Enable debug console", variable=debug_value, bg=PANEL, fg=CREAM, selectcolor=OLIVE_DARK, activebackground=PANEL, activeforeground=CREAM).grid(row=3, column=0, columnspan=2, pady=8)

        def save():
            candidate = name_entry.get().strip()
            if not candidate:
                messagebox.showerror("Settings", "Display name cannot be empty.", parent=dialog)
                return
            self.legacy_name = candidate
            self.language = language_value.get()
            self.debug_enabled = bool(debug_value.get())
            save_emulator_config(self.legacy_name[:15], self.language)
            dialog.grab_release()
            dialog.destroy()
            self.set_status("Field kit saved.")

        tk.Button(dialog, text="SAVE SETTINGS", command=save, bg=RED, fg="white", relief="flat", width=20, font=("Arial", 10, "bold")).grid(row=4, column=0, columnspan=2, pady=(10, 20))
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + (self.WIDTH - dialog.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.HEIGHT - dialog.winfo_height()) // 2
        dialog.geometry("+%d+%d" % (x, y))

    def open_official_steam(self):
        webbrowser.open(STEAM_APP_URL)
        self.set_status("Handing off to the official Steam client (AppID 224540).")

    def close(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass


def create_eula_window():
    root = tk.Tk()
    root.title("AoS Revival — Community Notice")
    root.resizable(False, False)
    root.configure(bg=PANEL)
    tk.Label(root, text="COMMUNITY REVIVAL NOTICE", bg=PANEL, fg=GOLD_LIGHT, font=("Impact", 18)).pack(padx=24, pady=(20, 8))
    notice = (
        "AoS Revival is an independent community preservation project and is not "
        "an official Jagex product. Do not sell this build. If you own the original "
        "Steam release, the launcher includes a direct official-Steam option.\n\n"
        "Online play sends only the account and match data described on aosplay.net; "
        "passwords are hashed by the service and launcher credentials are protected "
        "by your Windows account."
    )
    tk.Label(root, text=notice, bg=PANEL, fg=CREAM, wraplength=470, justify="left", font=("Arial", 10)).pack(padx=24, pady=10)
    buttons = tk.Frame(root, bg=PANEL)
    buttons.pack(pady=(8, 20))

    def decline():
        root.destroy()
        raise SystemExit(0)

    def accept():
        marker = eula_marker_path()
        try:
            directory = os.path.dirname(marker)
            if not os.path.isdir(directory):
                os.makedirs(directory)
            with open(marker, "wb") as stream:
                stream.write(b"accepted\n")
                stream.flush()
                try:
                    os.fsync(stream.fileno())
                except OSError:
                    pass
        except (IOError, OSError) as error:
            messagebox.showerror(
                "Could not save acceptance",
                "The launcher could not write its per-user settings.\n\n%s"
                % display_text(error),
                parent=root,
            )
            return
        root.destroy()

    tk.Button(buttons, text="DECLINE", command=decline, bg=OLIVE_DARK, fg=CREAM, relief="flat", width=12).pack(side="left", padx=5)
    tk.Button(buttons, text="I AGREE", command=accept, bg=RED, fg="white", relief="flat", width=16, font=("Arial", 10, "bold")).pack(side="left", padx=5)
    root.update_idletasks()
    x = max((root.winfo_screenwidth() - root.winfo_width()) // 2, 0)
    y = max((root.winfo_screenheight() - root.winfo_height()) // 2, 0)
    root.geometry("+%d+%d" % (x, y))
    root.mainloop()


def launch_launcher():
    root = tk.Tk()
    Launcher(root)
    root.mainloop()


def game_start():
    # This must precede every recovered-client import.  LoadingMenu and other
    # stock modules print Unicode packet fields during normal gameplay.
    install_game_output_streams()
    os.chdir(APP_DIR)
    missing = missing_game_files()
    if missing:
        path = append_launcher_log(
            "Game extraction is incomplete: %s"
            % ", ".join(display_text(item) for item in missing)
        )
        show_native_error(
            "Incomplete Ace of Spades installation",
            u"Required game files are missing:\n\n%s\n\nDiagnostic log:\n%s"
            % (
                u"\n".join(display_text(item) for item in missing),
                display_text(path or launcher_log_path()),
            ),
        )
        raise SystemExit(1)
    try:
        import run  # noqa: F401 — importing boots the recovered game client
    except SystemExit:
        raise
    except Exception as error:
        path = append_launcher_log(
            "Game bootstrap failed: %s" % display_text(error),
            sys.exc_info(),
        )
        show_native_error(
            "Ace of Spades could not start",
            u"The recovered game client encountered a startup error.\n\n"
            u"Diagnostic log:\n%s" % display_text(path or launcher_log_path()),
        )
        raise SystemExit(1)


def main():
    """Run either the resilient launcher shell or its isolated game child."""
    check_launcher_path()
    append_launcher_log(
        "Starting %s runtime."
        % ("frozen" if getattr(sys, "frozen", False) else "source")
    )
    is_game_child = "+s" in sys.argv
    if not is_game_child and not acquire_launcher_mutex():
        show_native_error(
            "AoS Revival is already running",
            "The launcher or an isolated game session is already active.",
        )
        raise SystemExit(0)
    legacy_marker = os.path.join(APP_DIR, "eula_true")
    if not os.path.isfile(eula_marker_path()) and not os.path.isfile(legacy_marker):
        create_eula_window()
    if is_game_child:
        game_start()
    else:
        launch_launcher()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as error:
        path = append_launcher_log(
            "Fatal launcher startup error: %s" % display_text(error),
            sys.exc_info(),
        )
        show_native_error(
            "AoS Revival launcher error",
            u"The launcher could not finish starting.\n\nDiagnostic log:\n%s"
            % display_text(path or launcher_log_path()),
        )
        raise SystemExit(1)
