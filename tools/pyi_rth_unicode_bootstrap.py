"""Repair PyInstaller's bootstrap path before its Tk runtime hook executes.

PyInstaller 3.5's Python 2 bootloader resolves the executable directory
through ANSI APIs. Characters outside the active Windows code page become
question marks, which makes the bundled Tcl/Tk lookup fail before launcher.py
can install its Unicode-safe path helpers.

The bootloader already exposes an ASCII 8.3 path through ``sys.prefix`` when
one is available. Use that path only for frozen-runtime imports and Tcl/Tk;
the launcher later resolves the real executable path with GetModuleFileNameW.
"""

import os
import sys


try:
    TEXT_TYPE = unicode
except NameError:  # pragma: no cover - Python 3 source tooling
    TEXT_TYPE = str


def _debug(message):
    if os.environ.get("AOS_BOOTSTRAP_DEBUG") != "1":
        return
    try:
        sys.stderr.write("[unicode-bootstrap] %s\n" % message)
    except Exception:
        pass


def _ascii_path(value):
    if not isinstance(value, (bytes, TEXT_TYPE)):
        return None
    try:
        if isinstance(value, bytes):
            value.decode("ascii")
        else:
            value.encode("ascii")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return None
    if sys.version_info[0] < 3 and isinstance(value, TEXT_TYPE):
        value = value.encode("ascii")
    return os.path.normpath(value)


def _windows_short_runtime_path():
    if sys.platform != "win32":
        return None
    try:
        import ctypes

        module_buffer = ctypes.create_unicode_buffer(32768)
        get_module_filename = ctypes.windll.kernel32.GetModuleFileNameW
        get_module_filename.argtypes = [
            ctypes.c_void_p,
            ctypes.c_wchar_p,
            ctypes.c_uint,
        ]
        get_module_filename.restype = ctypes.c_uint
        length = get_module_filename(None, module_buffer, len(module_buffer))
        if not length or length >= len(module_buffer):
            _debug("GetModuleFileNameW failed length=%r" % length)
            return None

        runtime_directory = os.path.dirname(module_buffer.value)
        _debug("wide runtime=%r" % runtime_directory)
        get_short_path = ctypes.windll.kernel32.GetShortPathNameW
        get_short_path.argtypes = [
            ctypes.c_wchar_p,
            ctypes.c_wchar_p,
            ctypes.c_uint,
        ]
        get_short_path.restype = ctypes.c_uint
        size = get_short_path(runtime_directory, None, 0)
        if not size:
            _debug("GetShortPathNameW size lookup failed")
            return None
        short_buffer = ctypes.create_unicode_buffer(size)
        length = get_short_path(runtime_directory, short_buffer, size)
        if not length or length >= size:
            _debug("GetShortPathNameW failed length=%r size=%r" % (length, size))
            return None
        _debug("short runtime=%r" % short_buffer.value)
        return _ascii_path(short_buffer.value)
    except (AttributeError, OSError, ValueError) as error:
        _debug("Win32 recovery failed: %r" % error)
        return None


def _runtime_prefix():
    candidates = [
        _windows_short_runtime_path(),
        getattr(sys, "prefix", None),
        getattr(sys, "exec_prefix", None),
    ]
    for value in candidates:
        candidate = _ascii_path(value)
        _debug("candidate=%r normalized=%r" % (value, candidate))
        if candidate is None:
            continue
        has_tcl = os.path.isdir(os.path.join(candidate, "tcl"))
        has_tk = os.path.isdir(os.path.join(candidate, "tk"))
        _debug("candidate dirs tcl=%r tk=%r" % (has_tcl, has_tk))
        if has_tcl and has_tk:
            return candidate
    return None


def normalize_frozen_runtime_path():
    prefix = _runtime_prefix()
    if prefix is None:
        _debug("no usable runtime prefix")
        return False

    previous_meipass = getattr(sys, "_MEIPASS", None)
    _debug("normalizing %r to %r" % (previous_meipass, prefix))
    sys._MEIPASS = prefix
    sys.prefix = prefix
    sys.exec_prefix = prefix
    os.environ["TCL_LIBRARY"] = os.path.join(prefix, "tcl")
    os.environ["TK_LIBRARY"] = os.path.join(prefix, "tk")
    # Python 2's FixTk expands the short prefix back to a lossy ANSI path
    # while probing for optional Tix data unless this variable already exists.
    os.environ["TIX_LIBRARY"] = os.path.join(prefix, "tcl")
    for index, path in enumerate(list(sys.path)):
        if path == previous_meipass or (
            isinstance(path, (bytes, TEXT_TYPE))
            and "?" in path
            and not os.path.exists(path)
        ):
            sys.path[index] = prefix
    return True


normalize_frozen_runtime_path()
