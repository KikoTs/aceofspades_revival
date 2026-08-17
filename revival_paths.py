# -*- coding: utf-8 -*-
"""Unicode-safe per-user paths for the legacy Python 2 Windows client."""
from __future__ import unicode_literals

import ctypes
from ctypes import wintypes
import os
import signal
import subprocess
import sys


try:
    TEXT_TYPE = unicode
except NameError:  # pragma: no cover - Python 3 source tooling
    TEXT_TYPE = str


CSIDL_LOCAL_APPDATA = 0x001C
SHGFP_TYPE_CURRENT = 0


def unicode_path(value):
    """Return a filesystem value as text without using Python 2's ANSI APIs."""

    if value is None or isinstance(value, TEXT_TYPE):
        return value
    encoding = sys.getfilesystemencoding() or (
        "mbcs" if os.name == "nt" else "utf-8"
    )
    return value.decode(encoding)


def _windows_environment_path(name):
    """Read one environment path through GetEnvironmentVariableW."""

    if os.name != "nt" or not hasattr(ctypes, "windll"):
        return None
    try:
        get_variable = ctypes.windll.kernel32.GetEnvironmentVariableW
        get_variable.argtypes = [
            ctypes.c_wchar_p,
            ctypes.c_wchar_p,
            ctypes.c_uint,
        ]
        get_variable.restype = ctypes.c_uint
        name = unicode_path(name)
        size = get_variable(name, None, 0)
        if not size:
            return None
        while size:
            buffer = ctypes.create_unicode_buffer(size)
            copied = get_variable(name, buffer, size)
            if not copied:
                return None
            if copied < size:
                return buffer.value
            size = copied + 1
    except (AttributeError, OSError, ValueError):
        return None
    return None


def _windows_local_appdata():
    """Resolve Local AppData with the Unicode Windows shell API."""

    if os.name != "nt" or not hasattr(ctypes, "windll"):
        return None
    try:
        buffer = ctypes.create_unicode_buffer(32768)
        get_folder = ctypes.windll.shell32.SHGetFolderPathW
        get_folder.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_wchar_p,
        ]
        get_folder.restype = ctypes.c_long
        result = get_folder(
            None,
            CSIDL_LOCAL_APPDATA,
            None,
            SHGFP_TYPE_CURRENT,
            buffer,
        )
        if result == 0 and buffer.value:
            return buffer.value
    except (AttributeError, OSError, ValueError):
        return None
    return None


def local_appdata_directory(fallback=None):
    """Return Local AppData as a Unicode path on Windows.

    Python 2 exposes ``os.environ`` as ANSI byte strings on Windows. Reading
    ``LOCALAPPDATA`` through the wide Win32 API prevents usernames outside the
    active code page from turning into ``?`` and producing invalid paths.
    """

    value = None
    if os.name == "nt":
        value = _windows_environment_path(u"LOCALAPPDATA")
        if not value:
            value = _windows_local_appdata()
    else:
        value = os.environ.get("LOCALAPPDATA")
    if not value:
        value = fallback if fallback is not None else os.path.expanduser("~")
    return os.path.normpath(unicode_path(value))


def current_executable_path(fallback=None):
    """Return the current executable through GetModuleFileNameW on Windows."""

    if os.name == "nt" and hasattr(ctypes, "windll"):
        try:
            buffer = ctypes.create_unicode_buffer(32768)
            get_module_filename = ctypes.windll.kernel32.GetModuleFileNameW
            get_module_filename.argtypes = [
                ctypes.c_void_p,
                ctypes.c_wchar_p,
                ctypes.c_uint,
            ]
            get_module_filename.restype = ctypes.c_uint
            length = get_module_filename(None, buffer, len(buffer))
            if length and length < len(buffer):
                return os.path.normpath(buffer.value)
        except (AttributeError, OSError, ValueError):
            pass
    value = fallback if fallback is not None else sys.executable
    return os.path.normpath(unicode_path(value))


def install_unicode_getcwd():
    """Make legacy ``os.getcwd`` callers return Unicode on Python 2 Windows."""

    unicode_getcwd = getattr(os, "getcwdu", None)
    if os.name == "nt" and unicode_getcwd is not None:
        os.getcwd = unicode_getcwd
        return True
    return False


def native_utf8_path(value):
    """Encode one Unicode filesystem path for UTF-8 native libraries."""

    value = unicode_path(value)
    return value.encode("utf-8") if isinstance(value, TEXT_TYPE) else value


class _StartupInfoW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.POINTER(ctypes.c_byte)),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]


class _ProcessInformation(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
    ]


def _handle_value(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def _close_child_handle(value):
    if value is None:
        return
    try:
        value.Close()
    except AttributeError:
        ctypes.windll.kernel32.CloseHandle(_handle_value(value))


def _unpack_execute_child_handles(child_handles):
    """Accept both Python 2 Windows ``Popen`` private ABI layouts.

    Stock 2.7 passes the six pipe handles directly.  The frozen runtime's
    newer ``subprocess`` adds its ``to_close`` set before those handles.
    Keeping the compatibility check here makes an unexpected ABI fail loudly
    without weakening argument validation for the two supported runtimes.
    """

    if len(child_handles) == 6:
        return (None,) + tuple(child_handles)
    if len(child_handles) == 7:
        return tuple(child_handles)
    raise TypeError(
        "_execute_child expected 6 or 7 child-handle arguments, got %d"
        % len(child_handles)
    )


def _close_parent_child_handle(value, to_close=None):
    """Close one inherited child end and retire it from ``to_close``."""

    if value is None:
        return
    if to_close is not None:
        try:
            to_close.remove(value)
        except (KeyError, ValueError):
            pass
    _close_child_handle(value)


def _unicode_environment_block(environment):
    if environment is None:
        return None
    entries = []
    for key in sorted(environment, key=lambda value: unicode_path(value).upper()):
        key_text = unicode_path(key)
        value_text = unicode_path(environment[key])
        entries.append(u"%s=%s" % (key_text, value_text))
    return ctypes.create_unicode_buffer(u"\0".join(entries) + u"\0\0")


class _UnicodePopen(subprocess.Popen):
    """Python 2 ``Popen`` backed by ``CreateProcessW`` on Windows."""

    def _execute_child(
        self,
        args,
        executable,
        preexec_fn,
        close_fds,
        cwd,
        env,
        universal_newlines,
        startupinfo,
        creationflags,
        shell,
        *child_handles
    ):
        (
            to_close,
            p2cread,
            p2cwrite,
            c2pread,
            c2pwrite,
            errread,
            errwrite,
        ) = _unpack_execute_child_handles(child_handles)
        if shell:
            raise ValueError("unicode_popen does not support shell=True")

        if not isinstance(args, (bytes, TEXT_TYPE)):
            args = subprocess.list2cmdline(args)
        command_line = ctypes.create_unicode_buffer(unicode_path(args))
        executable_value = (
            unicode_path(executable) if executable is not None else None
        )
        cwd_value = unicode_path(cwd) if cwd is not None else None

        if startupinfo is None:
            startupinfo = subprocess.STARTUPINFO()
        if None not in (p2cread, c2pwrite, errwrite):
            startupinfo.dwFlags |= getattr(
                subprocess,
                "STARTF_USESTDHANDLES",
                0x00000100,
            )
            startupinfo.hStdInput = p2cread
            startupinfo.hStdOutput = c2pwrite
            startupinfo.hStdError = errwrite

        native_startup = _StartupInfoW()
        native_startup.cb = ctypes.sizeof(native_startup)
        native_startup.dwFlags = startupinfo.dwFlags
        native_startup.wShowWindow = startupinfo.wShowWindow
        native_startup.hStdInput = _handle_value(startupinfo.hStdInput)
        native_startup.hStdOutput = _handle_value(startupinfo.hStdOutput)
        native_startup.hStdError = _handle_value(startupinfo.hStdError)
        process_info = _ProcessInformation()
        environment_block = _unicode_environment_block(env)
        environment_pointer = (
            ctypes.cast(environment_block, ctypes.c_void_p)
            if environment_block is not None
            else None
        )
        if environment_block is not None:
            creationflags |= 0x00000400  # CREATE_UNICODE_ENVIRONMENT

        create_process = ctypes.windll.kernel32.CreateProcessW
        create_process.argtypes = [
            wintypes.LPCWSTR,
            wintypes.LPWSTR,
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.BOOL,
            wintypes.DWORD,
            ctypes.c_void_p,
            wintypes.LPCWSTR,
            ctypes.POINTER(_StartupInfoW),
            ctypes.POINTER(_ProcessInformation),
        ]
        create_process.restype = wintypes.BOOL
        try:
            created = create_process(
                executable_value,
                command_line,
                None,
                None,
                int(not close_fds),
                creationflags,
                environment_pointer,
                cwd_value,
                ctypes.byref(native_startup),
                ctypes.byref(process_info),
            )
            if not created:
                raise ctypes.WinError()
        finally:
            _close_parent_child_handle(p2cread, to_close)
            _close_parent_child_handle(c2pwrite, to_close)
            _close_parent_child_handle(errwrite, to_close)

        self._child_created = True
        self._handle = _handle_value(process_info.hProcess)
        self.pid = int(process_info.dwProcessId)
        ctypes.windll.kernel32.CloseHandle(process_info.hThread)

    def _close_process_handle(self):
        handle = getattr(self, "_handle", None)
        if handle is not None:
            ctypes.windll.kernel32.CloseHandle(handle)
            self._handle = None

    def _internal_poll(self, _deadstate=None):
        if self.returncode is None:
            wait_result = ctypes.windll.kernel32.WaitForSingleObject(
                self._handle,
                0,
            )
            if wait_result == 0:
                exit_code = wintypes.DWORD()
                if not ctypes.windll.kernel32.GetExitCodeProcess(
                    self._handle,
                    ctypes.byref(exit_code),
                ):
                    if _deadstate is not None:
                        self.returncode = _deadstate
                    else:
                        raise ctypes.WinError()
                else:
                    self.returncode = int(exit_code.value)
                self._close_process_handle()
        return self.returncode

    def wait(self):
        if self.returncode is None:
            wait_result = ctypes.windll.kernel32.WaitForSingleObject(
                self._handle,
                0xFFFFFFFF,
            )
            if wait_result != 0:
                raise ctypes.WinError()
            exit_code = wintypes.DWORD()
            if not ctypes.windll.kernel32.GetExitCodeProcess(
                self._handle,
                ctypes.byref(exit_code),
            ):
                raise ctypes.WinError()
            self.returncode = int(exit_code.value)
            self._close_process_handle()
        return self.returncode

    def terminate(self):
        if self.returncode is None and not ctypes.windll.kernel32.TerminateProcess(
            self._handle,
            1,
        ):
            raise ctypes.WinError()

    kill = terminate

    def send_signal(self, signal_value):
        if signal_value == signal.SIGTERM:
            self.terminate()
            return
        raise ValueError("Unsupported signal: %s" % signal_value)


def unicode_popen(args, **kwargs):
    """Launch a child without Python 2's ANSI ``CreateProcess`` limitation."""

    if os.name == "nt" and sys.version_info[0] < 3:
        return _UnicodePopen(args, **kwargs)
    return subprocess.Popen(args, **kwargs)
