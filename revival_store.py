# -*- coding: utf-8 -*-
"""Private launcher state protected with the current Windows user account."""
from __future__ import print_function

import base64
import binascii
import ctypes
from ctypes import wintypes
import json
import os
import sys


APP_NAME = "AoS Revival"
STATE_VERSION = 1


def state_directory():
    root = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(root, APP_NAME)


def state_path():
    return os.path.join(state_directory(), "launcher_state.json")


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _as_bytes(value):
    if isinstance(value, bytes):
        return value
    return value.encode("utf-8")


def _dpapi_available():
    return sys.platform == "win32" and hasattr(ctypes, "windll")


def _blob_from_bytes(value):
    value = _as_bytes(value)
    buffer_value = ctypes.create_string_buffer(value, len(value))
    blob = _DataBlob(len(value), ctypes.cast(buffer_value, ctypes.POINTER(ctypes.c_char)))
    return blob, buffer_value


def _protect(value):
    value = _as_bytes(value)
    if not _dpapi_available():
        return "portable:" + base64.b64encode(value).decode("ascii")

    input_blob, input_buffer = _blob_from_bytes(value)
    output_blob = _DataBlob()
    description = u"AoS Revival launcher credential"
    result = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(input_blob),
        description,
        None,
        None,
        None,
        0,
        ctypes.byref(output_blob),
    )
    del input_buffer
    if not result:
        raise ctypes.WinError()
    try:
        protected = ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(output_blob.pbData)
    return "dpapi:" + base64.b64encode(protected).decode("ascii")


def _unprotect(value):
    if not value:
        return None
    try:
        if value.startswith("portable:"):
            return base64.b64decode(value.split(":", 1)[1])
        if not value.startswith("dpapi:") or not _dpapi_available():
            return None
        protected = base64.b64decode(value.split(":", 1)[1])
    except (AttributeError, TypeError, ValueError, binascii.Error):
        return None
    input_blob, input_buffer = _blob_from_bytes(protected)
    output_blob = _DataBlob()
    result = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(input_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(output_blob),
    )
    del input_buffer
    if not result:
        return None
    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(output_blob.pbData)


def load_state():
    try:
        with open(state_path(), "rb") as stream:
            raw = stream.read().decode("utf-8")
        state = json.loads(raw)
        if not isinstance(state, dict) or state.get("version") != STATE_VERSION:
            return {"version": STATE_VERSION}
        return state
    except (IOError, OSError, ValueError, TypeError):
        return {"version": STATE_VERSION}


def save_state(state):
    directory = state_directory()
    if not os.path.isdir(directory):
        try:
            os.makedirs(directory)
        except OSError:
            if not os.path.isdir(directory):
                raise
    state = dict(state)
    state["version"] = STATE_VERSION
    target = state_path()
    temporary = target + ".tmp"
    payload = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True)
    if not isinstance(payload, bytes):
        payload = payload.encode("utf-8")
    try:
        with open(temporary, "wb") as stream:
            stream.write(payload)
            stream.flush()
            try:
                os.fsync(stream.fileno())
            except OSError:
                pass
        if os.name == "nt":
            try:
                text_type = unicode
            except NameError:
                text_type = str
            encoding = sys.getfilesystemencoding() or "mbcs"
            source = (
                temporary
                if isinstance(temporary, text_type)
                else temporary.decode(encoding, "replace")
            )
            destination = (
                target
                if isinstance(target, text_type)
                else target.decode(encoding, "replace")
            )
            moved = ctypes.windll.kernel32.MoveFileExW(
                source,
                destination,
                0x1 | 0x8,  # MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH
            )
            if not moved:
                raise ctypes.WinError()
        else:
            if os.path.exists(target):
                os.remove(target)
            os.rename(temporary, target)
    except Exception:
        try:
            if os.path.exists(temporary):
                os.remove(temporary)
        except OSError:
            pass
        raise


def get_secret(state, name):
    secrets = state.get("secrets")
    if not isinstance(secrets, dict):
        return None
    protected = secrets.get(name)
    return _unprotect(protected)


def set_secret(state, name, value):
    secrets = dict(state.get("secrets") or {})
    if value is None:
        secrets.pop(name, None)
    else:
        secrets[name] = _protect(value)
    state["secrets"] = secrets


def clear_session(state):
    set_secret(state, "access_token", None)
    state.pop("account", None)
    state.pop("session_expires_at", None)


def canonical_legacy_id():
    state = load_state()
    account = state.get("account") or {}
    if account.get("offline"):
        return None
    value = account.get("legacy_id")
    return str(value) if value is not None else None
