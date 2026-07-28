# -*- coding: utf-8 -*-
"""Shared, Python 2-compatible display configuration validation."""
from __future__ import unicode_literals

import ctypes
import json
import os
import sys


try:
    TEXT_TYPE = unicode
except NameError:  # pragma: no cover - Python 3 tooling
    TEXT_TYPE = str


DISPLAY_SETTING_NAMES = (
    "fullscreen",
    "resolution",
    "width",
    "height",
    "window_width",
    "window_height",
    "window_location_x",
    "window_location_y",
)
MAX_DISPLAY_DIMENSION = 16384
MAX_RESOLUTION_INDEX = 4096


def _integer(value):
    if isinstance(value, bool):
        raise ValueError("boolean is not a display dimension")
    converted = int(value)
    if isinstance(value, float) and converted != value:
        raise ValueError("fractional display dimension")
    return converted


def _record_change(result, changes, name, value):
    old_value = result.get(name)
    if (
        name not in result
        or old_value != value
        or type(old_value) is not type(value)
    ):
        changes.append((name, old_value, value))
        result[name] = value


def _sanitize_pair(
    result,
    changes,
    width_name,
    height_name,
    default_width,
    default_height,
    minimum_width,
    minimum_height,
):
    if width_name not in result and height_name not in result:
        return
    try:
        width = _integer(result.get(width_name, default_width))
        height = _integer(result.get(height_name, default_height))
        if (
            width < minimum_width
            or height < minimum_height
            or width > MAX_DISPLAY_DIMENSION
            or height > MAX_DISPLAY_DIMENSION
        ):
            raise ValueError("display dimensions are outside safe bounds")
    except (TypeError, ValueError, OverflowError):
        width = default_width
        height = default_height
    _record_change(result, changes, width_name, width)
    _record_change(result, changes, height_name, height)


def sanitize_display_config(data):
    """Return a copy with only malformed display fields repaired.

    Valid custom resolutions are intentionally preserved. The client can use a
    window size which is not one of the monitor's exclusive fullscreen modes.
    """

    if not isinstance(data, dict):
        raise TypeError("display configuration must be a mapping")
    result = dict(data)
    changes = []

    if "fullscreen" in result:
        value = result["fullscreen"]
        if isinstance(value, TEXT_TYPE):
            normalized = value.strip().lower()
            if normalized in ("true", "1", "yes", "on"):
                value = True
            elif normalized in ("false", "0", "no", "off"):
                value = False
            else:
                value = False
        else:
            value = bool(value)
        _record_change(result, changes, "fullscreen", value)

    if "resolution" in result:
        try:
            resolution = _integer(result["resolution"])
            if resolution < 0 or resolution > MAX_RESOLUTION_INDEX:
                raise ValueError("resolution index is outside safe bounds")
        except (TypeError, ValueError, OverflowError):
            resolution = 0
        _record_change(result, changes, "resolution", resolution)

    _sanitize_pair(
        result,
        changes,
        "width",
        "height",
        800,
        600,
        640,
        480,
    )
    _sanitize_pair(
        result,
        changes,
        "window_width",
        "window_height",
        800,
        600,
        320,
        240,
    )

    for name in ("window_location_x", "window_location_y"):
        if name not in result:
            continue
        try:
            value = _integer(result[name])
        except (TypeError, ValueError, OverflowError):
            value = 0
        _record_change(result, changes, name, value)

    return result, changes


def _filesystem_text(value):
    if isinstance(value, TEXT_TYPE):
        return value
    encoding = sys.getfilesystemencoding() or (
        "mbcs" if os.name == "nt" else "utf-8"
    )
    return value.decode(encoding, "replace")


def write_json_file(path, data):
    """Atomically replace a JSON file without leaving a partial config."""

    payload = json.dumps(data, ensure_ascii=False, indent=4, sort_keys=True)
    if not isinstance(payload, bytes):
        payload = payload.encode("utf-8")
    temporary = path + ".tmp"
    try:
        with open(temporary, "wb") as stream:
            stream.write(payload)
            stream.flush()
            try:
                os.fsync(stream.fileno())
            except (AttributeError, OSError):
                pass
        if os.name == "nt":
            moved = ctypes.windll.kernel32.MoveFileExW(
                _filesystem_text(temporary),
                _filesystem_text(path),
                0x1 | 0x8,  # REPLACE_EXISTING | WRITE_THROUGH
            )
            if not moved:
                raise ctypes.WinError()
        else:
            if os.path.exists(path):
                os.remove(path)
            os.rename(temporary, path)
    except Exception:
        try:
            if os.path.exists(temporary):
                os.remove(temporary)
        except (IOError, OSError):
            pass
        raise


def repair_display_config_file(path):
    """Repair malformed display values in-place and return the changed fields."""

    with open(path, "rb") as stream:
        payload = stream.read()
    if not isinstance(payload, TEXT_TYPE):
        payload = payload.decode("utf-8-sig")
    data = json.loads(payload)
    repaired, changes = sanitize_display_config(data)
    if changes:
        write_json_file(path, repaired)
    return changes
