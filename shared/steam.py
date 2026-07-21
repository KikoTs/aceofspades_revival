# -*- coding: utf-8 -*-
"""
Pure-Python compatibility reconstruction of shared.steam for CPython 2.7.

Source of the public ABI:
    steam.pyd / shared.steam.pyd, 32-bit CPython 2.7 Cython extension,
    build timestamp 2015-12-07.

This module preserves the original public method names and observed call flags.
It is a compatibility fallback, not a byte-for-byte recreation of Steamworks.
It does not fabricate Steam ownership, authentication tickets, or licenses.
A narrow compatibility override is retained for legacy removed content ID 42.

Python compatibility: 2.7 and 3.x.
"""

from __future__ import absolute_import

import binascii
import ctypes
import glob
import json
import struct
import os
import sys
import threading
import time
import webbrowser

try:
    integer_types = (int, long)
except NameError:
    integer_types = (int,)

try:
    text_type = unicode
except NameError:
    text_type = str


APP_ID = 224540
GAME_VERSION = 168
UGC_VERSION = 2

# Legacy content that is no longer obtainable through Steam but is required
# by the old client.  This is deliberately narrow: every other AppID is still
# checked through ISteamApps::BIsDlcInstalled.
_LEGACY_INSTALLED_DLC_IDS = frozenset((420650,))

# The original steam.pyd was built in December 2015 and imported the legacy
# SteamApps() accessor directly.  If that export is unavailable, these
# interface names are tried through SteamInternal_FindOrCreateUserInterface
# or ISteamClient::GetISteamApps.  VERSION007 is tried first because it best
# matches the SDK generation used by the original module.
_STEAMAPPS_INTERFACE_VERSIONS = (
    b"STEAMAPPS_INTERFACE_VERSION007",
    b"STEAMAPPS_INTERFACE_VERSION008",
    b"STEAMAPPS_INTERFACE_VERSION006",
    b"STEAMAPPS_INTERFACE_VERSION009",
    b"STEAMAPPS_INTERFACE_VERSION005",
    b"STEAMAPPS_INTERFACE_VERSION004",
    b"STEAMAPPS_INTERFACE_VERSION003",
    b"STEAMAPPS_INTERFACE_VERSION002",
    b"STEAMAPPS_INTERFACE_VERSION001",
)

# ISteamFriends interface versions used by legacy and newer Steam API builds.
# The original pyd imported SteamFriends() directly; VERSION015 is the most
# likely interface generation for its December 2015 SDK.
_STEAMFRIENDS_INTERFACE_VERSIONS = (
    b"SteamFriends015",
    b"SteamFriends014",
    b"SteamFriends013",
    b"SteamFriends016",
    b"SteamFriends017",
    b"SteamFriends012",
    b"SteamFriends011",
    b"SteamFriends010",
    b"SteamFriends009",
    b"SteamFriends008",
    b"SteamFriends007",
    b"SteamFriends006",
    b"SteamFriends005",
    b"SteamFriends004",
    b"SteamFriends003",
    b"SteamFriends002",
    b"SteamFriends001",
)

_DEBUG = os.environ.get("AOS_STEAM_DEBUG", "").lower() in (
    "1", "true", "yes", "on"
)

_lock = threading.RLock()
_pending_callbacks = []


def _debug(message):
    if not _DEBUG:
        return
    try:
        sys.stderr.write("[shared.steam] %s\n" % message)
    except Exception:
        pass


def _to_text(value):
    if value is None:
        return u""
    if isinstance(value, text_type):
        return value
    try:
        return text_type(value)
    except Exception:
        return u""


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def _to_app_id(value):
    """Convert a Python integer to Steamworks AppId_t (uint32)."""
    try:
        app_id = int(value)
    except (TypeError, ValueError):
        raise TypeError("app_id must be an integer")
    if app_id < 0 or app_id > 0xFFFFFFFF:
        raise OverflowError("app_id does not fit in AppId_t")
    return app_id


def _queue_callback(callback, *args):
    if not callable(callback):
        return False
    with _lock:
        _pending_callbacks.append((callback, args))
    return True


def _call_callback(callback, args):
    try:
        callback(*args)
        return True
    except Exception as exc:
        _debug("callback failed: %r" % (exc,))
        return False


def _drain_callbacks():
    while True:
        with _lock:
            if not _pending_callbacks:
                break
            callback, args = _pending_callbacks.pop(0)
        _call_callback(callback, args)


class _SteamApiBackend(object):
    """Small safe bridge to the exported flat Steam API entry points."""

    def __init__(self):
        self.dll = None
        self.initialized = False
        self.path = None
        self._exec_blocks = []
        self._get_steam_id_thunk = None
        self._get_auth_ticket_thunk = None
        self._cancel_auth_ticket_thunk = None
        self._get_persona_name_thunk = None
        self._get_current_game_language_thunk = None
        self._get_isteamfriends_thunk = None
        self._is_dlc_installed_thunk = None
        self._get_isteamapps_thunk = None
        self._steam_friends_ptr = 0
        self._steam_friends_source = None
        self._steam_apps_ptr = 0
        self._steam_apps_source = None
        self._legacy_steam_friends = None
        self._flat_steam_friends = []
        self._legacy_steam_apps = None
        self._flat_steam_apps = []
        self._steam_client = None
        self._get_hsteam_user = None
        self._get_hsteam_pipe = None
        self._find_or_create_user_interface = None

    def _candidate_paths(self):
        module_dir = os.path.dirname(os.path.abspath(__file__))
        roots = [
            os.getcwd(),
            module_dir,
            os.path.dirname(module_dir),
            os.path.dirname(os.path.dirname(module_dir)),
        ]
        env_path = os.environ.get("AOS_STEAM_API_DLL")
        if env_path:
            yield env_path
        seen = set()
        for root in roots:
            candidate = os.path.abspath(os.path.join(root, "steam_api.dll"))
            key = candidate.lower()
            if key not in seen:
                seen.add(key)
                yield candidate

    def has_dll_file(self):
        """Return True when steam_api.dll physically exists in a search path."""
        for candidate in self._candidate_paths():
            try:
                if os.path.isfile(candidate):
                    return True
            except Exception:
                pass
        return False

    def _bind_optional_export(self, dll, name, restype, argtypes):
        """Bind an optional cdecl Steam API export without failing DLL load."""
        try:
            function = getattr(dll, name)
        except AttributeError:
            return None
        try:
            function.restype = restype
            function.argtypes = argtypes
        except Exception:
            return None
        return function

    def load(self):
        if self.dll is not None:
            return True
        if os.name != "nt":
            return False
        for candidate in self._candidate_paths():
            if not os.path.isfile(candidate):
                continue
            try:
                # Steamworks exports use the C calling convention on Win32.
                dll = ctypes.CDLL(candidate)
                dll.SteamAPI_Init.restype = ctypes.c_bool
                dll.SteamAPI_Init.argtypes = []
                dll.SteamAPI_RunCallbacks.restype = None
                dll.SteamAPI_RunCallbacks.argtypes = []
                dll.SteamAPI_Shutdown.restype = None
                dll.SteamAPI_Shutdown.argtypes = []

                # Legacy global accessors imported by the original 2015 pyd.
                steam_user = self._bind_optional_export(
                    dll, "SteamUser", ctypes.c_void_p, []
                )
                if steam_user is not None:
                    dll.SteamUser = steam_user

                self._legacy_steam_friends = self._bind_optional_export(
                    dll, "SteamFriends", ctypes.c_void_p, []
                )
                self._legacy_steam_apps = self._bind_optional_export(
                    dll, "SteamApps", ctypes.c_void_p, []
                )

                # Newer steam_api.dll builds can expose versioned flat
                # accessors instead of the legacy SteamApps symbol.
                self._flat_steam_friends = []
                for version in range(20, 0, -1):
                    export_name = "SteamAPI_SteamFriends_v%03d" % version
                    function = self._bind_optional_export(
                        dll, export_name, ctypes.c_void_p, []
                    )
                    if function is not None:
                        self._flat_steam_friends.append((export_name, function))

                self._flat_steam_apps = []
                for version in range(12, 0, -1):
                    export_name = "SteamAPI_SteamApps_v%03d" % version
                    function = self._bind_optional_export(
                        dll, export_name, ctypes.c_void_p, []
                    )
                    if function is not None:
                        self._flat_steam_apps.append((export_name, function))

                # Internal/context reconstruction fallbacks.
                self._steam_client = self._bind_optional_export(
                    dll, "SteamClient", ctypes.c_void_p, []
                )
                self._get_hsteam_user = self._bind_optional_export(
                    dll, "SteamAPI_GetHSteamUser", ctypes.c_int32, []
                )
                self._get_hsteam_pipe = self._bind_optional_export(
                    dll, "SteamAPI_GetHSteamPipe", ctypes.c_int32, []
                )
                self._find_or_create_user_interface = self._bind_optional_export(
                    dll,
                    "SteamInternal_FindOrCreateUserInterface",
                    ctypes.c_void_p,
                    [ctypes.c_int32, ctypes.c_char_p],
                )
                self.dll = dll
                self.path = candidate
                _debug("loaded %s" % candidate)
                return True
            except Exception as exc:
                _debug("failed to load %s: %r" % (candidate, exc))
        return False

    def initialize(self):
        if self.initialized:
            return True
        if not self.load():
            return False
        try:
            self.initialized = bool(self.dll.SteamAPI_Init())
        except Exception as exc:
            _debug("SteamAPI_Init failed: %r" % (exc,))
            self.initialized = False
        return self.initialized

    def update(self):
        if not self.initialized or self.dll is None:
            return
        try:
            self.dll.SteamAPI_RunCallbacks()
        except Exception as exc:
            _debug("SteamAPI_RunCallbacks failed: %r" % (exc,))

    def _alloc_x86_thunk(self, code, prototype):
        """Create a tiny x86 bridge from cdecl ctypes to MSVC __thiscall."""
        if os.name != "nt" or ctypes.sizeof(ctypes.c_void_p) != 4:
            return None
        kernel32 = ctypes.windll.kernel32
        kernel32.VirtualAlloc.restype = ctypes.c_void_p
        kernel32.VirtualAlloc.argtypes = [
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.c_ulong,
            ctypes.c_ulong,
        ]
        address = kernel32.VirtualAlloc(
            None,
            len(code),
            0x3000,  # MEM_COMMIT | MEM_RESERVE
            0x40,    # PAGE_EXECUTE_READWRITE
        )
        if not address:
            return None
        ctypes.memmove(address, code, len(code))
        self._exec_blocks.append(address)
        return prototype(address)

    def _ensure_ticket_thunks(self):
        if self._get_auth_ticket_thunk is not None:
            return True
        if os.name != "nt" or ctypes.sizeof(ctypes.c_void_p) != 4:
            _debug("Steam ticket bridge requires 32-bit Windows/Python")
            return False

        # ISteamUser::GetSteamID(), vtable index 2 / byte offset 0x08.
        # MSVC x86 returns CSteamID through a hidden output pointer.
        get_steam_id_code = (
            b"\x55\x8b\xec"          # push ebp; mov ebp, esp
            b"\x8b\x4d\x08"          # mov ecx, [ebp+8]   ; this
            b"\xff\x75\x0c"          # push [ebp+12]      ; out CSteamID
            b"\x8b\x01"              # mov eax, [ecx]     ; vtable
            b"\xff\x50\x08"          # call [eax+08h]
            b"\x5d\xc3"              # pop ebp; ret
        )
        get_steam_id_proto = ctypes.CFUNCTYPE(
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
        )

        # ISteamUser::GetAuthSessionTicket(), vtable index 13 / offset 0x34.
        get_ticket_code = (
            b"\x55\x8b\xec"
            b"\x8b\x4d\x08"          # ECX = this
            b"\xff\x75\x14"          # pcbTicket
            b"\xff\x75\x10"          # cbMaxTicket
            b"\xff\x75\x0c"          # pTicket
            b"\x8b\x01"
            b"\xff\x50\x34"
            b"\x5d\xc3"
        )
        get_ticket_proto = ctypes.CFUNCTYPE(
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint32),
        )

        # ISteamUser::CancelAuthTicket(), vtable index 16 / offset 0x40.
        cancel_ticket_code = (
            b"\x55\x8b\xec"
            b"\x8b\x4d\x08"          # ECX = this
            b"\xff\x75\x0c"          # hAuthTicket
            b"\x8b\x01"
            b"\xff\x50\x40"
            b"\x5d\xc3"
        )
        cancel_ticket_proto = ctypes.CFUNCTYPE(
            None,
            ctypes.c_void_p,
            ctypes.c_uint32,
        )

        self._get_steam_id_thunk = self._alloc_x86_thunk(
            get_steam_id_code, get_steam_id_proto
        )
        self._get_auth_ticket_thunk = self._alloc_x86_thunk(
            get_ticket_code, get_ticket_proto
        )
        self._cancel_auth_ticket_thunk = self._alloc_x86_thunk(
            cancel_ticket_code, cancel_ticket_proto
        )
        return bool(
            self._get_steam_id_thunk
            and self._get_auth_ticket_thunk
            and self._cancel_auth_ticket_thunk
        )

    def _steam_user(self):
        if not self.initialized or self.dll is None:
            return 0
        try:
            return int(self.dll.SteamUser() or 0)
        except Exception as exc:
            _debug("SteamUser() failed: %r" % (exc,))
            return 0

    def get_steam_id(self):
        if not self._ensure_ticket_thunks():
            return 0
        user = self._steam_user()
        if not user:
            return 0
        output = ctypes.create_string_buffer(8)
        try:
            self._get_steam_id_thunk(user, ctypes.byref(output))
            return int(struct.unpack("<Q", output.raw)[0])
        except Exception as exc:
            _debug("ISteamUser::GetSteamID failed: %r" % (exc,))
            return 0

    def create_session_ticket(self):
        """Return (hex_ticket, handle), matching the original 2015 format."""
        if not self.initialized and not self.initialize():
            return "", 0
        if not self._ensure_ticket_thunks():
            return "", 0
        user = self._steam_user()
        if not user:
            return "", 0

        # Original shared.steam.pyd reserves 1016 bytes for the Steam ticket
        # and prepends the 8-byte little-endian SteamID before hex encoding.
        ticket_buffer = ctypes.create_string_buffer(0x3F8)
        ticket_size = ctypes.c_uint32(0)
        try:
            handle = int(self._get_auth_ticket_thunk(
                user,
                ticket_buffer,
                0x3F8,
                ctypes.byref(ticket_size),
            ))
        except Exception as exc:
            _debug("GetAuthSessionTicket failed: %r" % (exc,))
            return "", 0

        if handle == 0 or ticket_size.value > 0x3F8:
            _debug("GetAuthSessionTicket returned an invalid result")
            return "", 0

        steam_id = self.get_steam_id()
        if not steam_id:
            self.cancel_session_ticket(handle)
            _debug("GetAuthSessionTicket succeeded but SteamID is unavailable")
            return "", 0

        raw_ticket = (
            struct.pack("<Q", steam_id)
            + ticket_buffer.raw[:ticket_size.value]
        )
        encoded = binascii.hexlify(raw_ticket)
        if not isinstance(encoded, str):
            encoded = encoded.decode("ascii")
        _debug(
            "created auth ticket for %d: %d Steam bytes, %d encoded chars"
            % (steam_id, ticket_size.value, len(encoded))
        )
        return encoded, handle

    def cancel_session_ticket(self, handle):
        handle = _to_int(handle, 0)
        if not handle or not self._ensure_ticket_thunks():
            return False
        user = self._steam_user()
        if not user:
            return False
        try:
            self._cancel_auth_ticket_thunk(user, handle)
            return True
        except Exception as exc:
            _debug("CancelAuthTicket failed: %r" % (exc,))
            return False

    def _ensure_get_isteamfriends_thunk(self):
        """Build a cdecl-to-MSVC-thiscall bridge for GetISteamFriends."""
        if self._get_isteamfriends_thunk is not None:
            return True
        if os.name != "nt" or ctypes.sizeof(ctypes.c_void_p) != 4:
            return False

        # ISteamClient::GetISteamFriends( HSteamUser, HSteamPipe, version )
        # vtable index 8 / byte offset 0x20 in the legacy x86 ABI.
        code = (
            b"\x55\x8b\xec"          # push ebp; mov ebp, esp
            b"\x8b\x4d\x08"          # mov ecx, [ebp+8]  ; this
            b"\xff\x75\x14"          # push [ebp+20]     ; version
            b"\xff\x75\x10"          # push [ebp+16]     ; hSteamPipe
            b"\xff\x75\x0c"          # push [ebp+12]     ; hSteamUser
            b"\x8b\x01"              # mov eax, [ecx]    ; vtable
            b"\xff\x50\x20"          # call [eax+20h]
            b"\x5d\xc3"              # pop ebp; ret
        )
        prototype = ctypes.CFUNCTYPE(
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_int32,
            ctypes.c_int32,
            ctypes.c_char_p,
        )
        self._get_isteamfriends_thunk = self._alloc_x86_thunk(code, prototype)
        return bool(self._get_isteamfriends_thunk)

    def _remember_steam_friends(self, pointer, source):
        pointer = int(pointer or 0)
        if pointer:
            self._steam_friends_ptr = pointer
            self._steam_friends_source = source
            _debug("ISteamFriends acquired via %s at 0x%08X" % (source, pointer))
        return pointer

    def _steam_friends(self):
        """Reconstruct SteamFriends() and return the real ISteamFriends*."""
        if not self.initialized or self.dll is None:
            return 0
        if self._steam_friends_ptr:
            return self._steam_friends_ptr

        # Exact accessor imported by the original 2015 shared.steam.pyd.
        if self._legacy_steam_friends is not None:
            try:
                pointer = self._legacy_steam_friends()
                if pointer:
                    return self._remember_steam_friends(
                        pointer, "SteamFriends export"
                    )
            except Exception as exc:
                _debug("legacy SteamFriends() failed: %r" % (exc,))

        # Newer versioned flat accessors.
        for export_name, function in self._flat_steam_friends:
            try:
                pointer = function()
                if pointer:
                    return self._remember_steam_friends(pointer, export_name)
            except Exception as exc:
                _debug("%s failed: %r" % (export_name, exc))

        hsteam_user = 0
        hsteam_pipe = 0
        if self._get_hsteam_user is not None:
            try:
                hsteam_user = int(self._get_hsteam_user())
            except Exception as exc:
                _debug("SteamAPI_GetHSteamUser failed: %r" % (exc,))
        if self._get_hsteam_pipe is not None:
            try:
                hsteam_pipe = int(self._get_hsteam_pipe())
            except Exception as exc:
                _debug("SteamAPI_GetHSteamPipe failed: %r" % (exc,))

        # Internal accessor used by newer Steam API contexts.
        if self._find_or_create_user_interface is not None and hsteam_user:
            for version in _STEAMFRIENDS_INTERFACE_VERSIONS:
                try:
                    pointer = self._find_or_create_user_interface(
                        hsteam_user, version
                    )
                    if pointer:
                        return self._remember_steam_friends(
                            pointer,
                            "SteamInternal_FindOrCreateUserInterface(%s)"
                            % version,
                        )
                except Exception as exc:
                    _debug(
                        "FindOrCreateUserInterface(%s) failed: %r"
                        % (version, exc)
                    )

        # Legacy reconstruction through ISteamClient.
        if (
            self._steam_client is not None
            and hsteam_user
            and hsteam_pipe
            and self._ensure_get_isteamfriends_thunk()
        ):
            try:
                client = int(self._steam_client() or 0)
            except Exception as exc:
                _debug("SteamClient() failed: %r" % (exc,))
                client = 0
            if client:
                for version in _STEAMFRIENDS_INTERFACE_VERSIONS:
                    try:
                        pointer = self._get_isteamfriends_thunk(
                            client, hsteam_user, hsteam_pipe, version
                        )
                        if pointer:
                            return self._remember_steam_friends(
                                pointer,
                                "SteamClient::GetISteamFriends(%s)" % version,
                            )
                    except Exception as exc:
                        _debug(
                            "GetISteamFriends(%s) failed: %r" % (version, exc)
                        )

        _debug("unable to acquire ISteamFriends interface")
        return 0

    def _ensure_friends_thunks(self):
        if self._get_persona_name_thunk is not None:
            return True
        if os.name != "nt" or ctypes.sizeof(ctypes.c_void_p) != 4:
            _debug("ISteamFriends bridge requires 32-bit Windows/Python")
            return False

        # Recovered directly from the original steam.pyd:
        # SteamFriends()->GetPersonaName()
        # ISteamFriends vtable index 0 / byte offset 0x00.
        get_persona_name_code = (
            b"\x55\x8b\xec"          # push ebp; mov ebp, esp
            b"\x8b\x4d\x08"          # mov ecx, [ebp+8] ; this
            b"\x8b\x01"              # mov eax, [ecx]   ; vtable
            b"\xff\x10"              # call [eax+00h]
            b"\x5d\xc3"              # pop ebp; ret
        )
        prototype = ctypes.CFUNCTYPE(
            ctypes.c_void_p,
            ctypes.c_void_p,
        )
        self._get_persona_name_thunk = self._alloc_x86_thunk(
            get_persona_name_code, prototype
        )
        return bool(self._get_persona_name_thunk)

    def get_persona_name(self):
        """Return the current Steam persona name as Unicode."""
        if not self.initialized and not self.initialize():
            return u""
        if not self._ensure_friends_thunks():
            return u""
        friends = self._steam_friends()
        if not friends:
            return u""
        try:
            pointer = int(self._get_persona_name_thunk(friends) or 0)
            if not pointer:
                return u""
            raw_name = ctypes.string_at(pointer)
            try:
                name = raw_name.decode("utf-8")
            except UnicodeDecodeError:
                name = raw_name.decode("utf-8", "replace")
            _debug("GetPersonaName() -> %r" % (name,))
            return name
        except Exception as exc:
            _debug("ISteamFriends::GetPersonaName failed: %r" % (exc,))
            return u""

    def _ensure_language_thunk(self):
        """Build a bridge for ISteamApps::GetCurrentGameLanguage()."""
        if self._get_current_game_language_thunk is not None:
            return True
        if os.name != "nt" or ctypes.sizeof(ctypes.c_void_p) != 4:
            _debug("ISteamApps language bridge requires 32-bit Windows/Python")
            return False

        # Legacy ISteamApps ABI used by the original module:
        # GetCurrentGameLanguage() is vtable index 4 / byte offset 0x10.
        code = (
            b"\x55\x8b\xec"          # push ebp; mov ebp, esp
            b"\x8b\x4d\x08"          # mov ecx, [ebp+8] ; this
            b"\x8b\x01"              # mov eax, [ecx]   ; vtable
            b"\xff\x50\x10"          # call [eax+10h]
            b"\x5d\xc3"              # pop ebp; ret
        )
        prototype = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p)
        self._get_current_game_language_thunk = self._alloc_x86_thunk(
            code, prototype
        )
        return bool(self._get_current_game_language_thunk)

    def get_current_game_language(self):
        """Return Steam's current game language, or an empty string."""
        if not self.initialized and not self.initialize():
            return u""
        if not self._ensure_language_thunk():
            return u""
        apps = self._steam_apps()
        if not apps:
            return u""
        try:
            pointer = int(self._get_current_game_language_thunk(apps) or 0)
            if not pointer:
                return u""
            raw_language = ctypes.string_at(pointer)
            try:
                language = raw_language.decode("utf-8")
            except UnicodeDecodeError:
                language = raw_language.decode("utf-8", "replace")
            language = language.strip()
            _debug("GetCurrentGameLanguage() -> %r" % (language,))
            return language
        except Exception as exc:
            _debug("ISteamApps::GetCurrentGameLanguage failed: %r" % (exc,))
            return u""

    def _ensure_get_isteamapps_thunk(self):
        """Build a cdecl-to-MSVC-thiscall bridge for GetISteamApps."""
        if self._get_isteamapps_thunk is not None:
            return True
        if os.name != "nt" or ctypes.sizeof(ctypes.c_void_p) != 4:
            return False

        # ISteamClient::GetISteamApps( HSteamUser, HSteamPipe, const char * )
        # occupies vtable index 15 / byte offset 0x3C in the legacy x86 ABI.
        code = (
            b"\x55\x8b\xec"          # push ebp; mov ebp, esp
            b"\x8b\x4d\x08"          # mov ecx, [ebp+8]  ; this
            b"\xff\x75\x14"          # push [ebp+20]     ; version
            b"\xff\x75\x10"          # push [ebp+16]     ; hSteamPipe
            b"\xff\x75\x0c"          # push [ebp+12]     ; hSteamUser
            b"\x8b\x01"              # mov eax, [ecx]    ; vtable
            b"\xff\x50\x3c"          # call [eax+3Ch]
            b"\x5d\xc3"              # pop ebp; ret
        )
        prototype = ctypes.CFUNCTYPE(
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_int32,
            ctypes.c_int32,
            ctypes.c_char_p,
        )
        self._get_isteamapps_thunk = self._alloc_x86_thunk(code, prototype)
        return bool(self._get_isteamapps_thunk)

    def _remember_steam_apps(self, pointer, source):
        pointer = int(pointer or 0)
        if pointer:
            self._steam_apps_ptr = pointer
            self._steam_apps_source = source
            _debug("ISteamApps acquired via %s at 0x%08X" % (source, pointer))
        return pointer

    def _steam_apps(self):
        """Reconstruct the global SteamApps() accessor and return ISteamApps*."""
        if not self.initialized or self.dll is None:
            return 0
        if self._steam_apps_ptr:
            return self._steam_apps_ptr

        # 1. Exact path used by the original steam.pyd.
        if self._legacy_steam_apps is not None:
            try:
                pointer = self._legacy_steam_apps()
                if pointer:
                    return self._remember_steam_apps(pointer, "SteamApps export")
            except Exception as exc:
                _debug("legacy SteamApps() failed: %r" % (exc,))

        # 2. Versioned flat accessor used by newer SDK builds.
        for export_name, function in self._flat_steam_apps:
            try:
                pointer = function()
                if pointer:
                    return self._remember_steam_apps(pointer, export_name)
            except Exception as exc:
                _debug("%s failed: %r" % (export_name, exc))

        hsteam_user = 0
        hsteam_pipe = 0
        if self._get_hsteam_user is not None:
            try:
                hsteam_user = int(self._get_hsteam_user())
            except Exception as exc:
                _debug("SteamAPI_GetHSteamUser failed: %r" % (exc,))
        if self._get_hsteam_pipe is not None:
            try:
                hsteam_pipe = int(self._get_hsteam_pipe())
            except Exception as exc:
                _debug("SteamAPI_GetHSteamPipe failed: %r" % (exc,))

        # 3. The internal helper used by modern Steam API contexts.
        if self._find_or_create_user_interface is not None and hsteam_user:
            for version in _STEAMAPPS_INTERFACE_VERSIONS:
                try:
                    pointer = self._find_or_create_user_interface(
                        hsteam_user, version
                    )
                    if pointer:
                        return self._remember_steam_apps(
                            pointer,
                            "SteamInternal_FindOrCreateUserInterface(%s)"
                            % version,
                        )
                except Exception as exc:
                    _debug(
                        "FindOrCreateUserInterface(%s) failed: %r"
                        % (version, exc)
                    )

        # 4. Explicit legacy reconstruction:
        # SteamClient()->GetISteamApps(user, pipe, interface_version).
        if (
            self._steam_client is not None
            and hsteam_user
            and hsteam_pipe
            and self._ensure_get_isteamapps_thunk()
        ):
            try:
                client = int(self._steam_client() or 0)
            except Exception as exc:
                _debug("SteamClient() failed: %r" % (exc,))
                client = 0
            if client:
                for version in _STEAMAPPS_INTERFACE_VERSIONS:
                    try:
                        pointer = self._get_isteamapps_thunk(
                            client, hsteam_user, hsteam_pipe, version
                        )
                        if pointer:
                            return self._remember_steam_apps(
                                pointer,
                                "SteamClient::GetISteamApps(%s)" % version,
                            )
                    except Exception as exc:
                        _debug(
                            "GetISteamApps(%s) failed: %r" % (version, exc)
                        )

        _debug("unable to acquire ISteamApps interface")
        return 0

    def _ensure_apps_thunks(self):
        if self._is_dlc_installed_thunk is not None:
            return True
        if os.name != "nt" or ctypes.sizeof(ctypes.c_void_p) != 4:
            _debug("ISteamApps bridge requires 32-bit Windows/Python")
            return False

        # Recovered directly from the original 2015 steam.pyd:
        # SteamApps()->BIsDlcInstalled(app_id)
        # ISteamApps vtable byte offset 0x1C, index 7.
        #
        # The tiny bridge converts a ctypes cdecl call into MSVC x86
        # __thiscall: ECX receives the ISteamApps pointer and AppId_t is
        # pushed as the single explicit uint32 argument.
        is_dlc_installed_code = (
            b"\x55\x8b\xec"          # push ebp; mov ebp, esp
            b"\x8b\x4d\x08"          # mov ecx, [ebp+8] ; this
            b"\xff\x75\x0c"          # push [ebp+12]    ; app_id
            b"\x8b\x01"              # mov eax, [ecx]   ; vtable
            b"\xff\x50\x1c"          # call [eax+1Ch]
            b"\x0f\xb6\xc0"          # movzx eax, al    ; C++ bool
            b"\x5d\xc3"              # pop ebp; ret
        )
        prototype = ctypes.CFUNCTYPE(
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.c_uint32,
        )
        self._is_dlc_installed_thunk = self._alloc_x86_thunk(
            is_dlc_installed_code,
            prototype,
        )
        return bool(self._is_dlc_installed_thunk)

    def is_dlc_installed(self, app_id):
        app_id = ctypes.c_uint32(app_id).value

        # Offline emulation mode: when steam_api.dll is physically absent,
        # there is no ISteamApps interface to query.  The standalone client
        # must therefore treat requested DLC content as installed so that
        # removed/legacy content remains available without Steam.
        if not self.has_dll_file():
            _debug("offline DLC emulation: BIsDlcInstalled(%u) -> True" % app_id)
            return True

        # ID 42 is retired/removed content.  Keep it available even when a
        # real Steam API DLL is present and Steam can no longer resolve it.
        if app_id in _LEGACY_INSTALLED_DLC_IDS:
            _debug("backend legacy DLC compatibility: %u -> True" % app_id)
            return True

        if not self.initialized and not self.initialize():
            return False
        if not self._ensure_apps_thunks():
            return False
        apps = self._steam_apps()
        if not apps:
            return False
        try:
            result = self._is_dlc_installed_thunk(apps, app_id)
            installed = bool(result)
            _debug("BIsDlcInstalled(%u) -> %s" % (app_id, installed))
            return installed
        except Exception as exc:
            _debug("ISteamApps::BIsDlcInstalled failed: %r" % (exc,))
            return False

    def shutdown(self):
        if not self.initialized or self.dll is None:
            return
        try:
            self.dll.SteamAPI_Shutdown()
        except Exception as exc:
            _debug("SteamAPI_Shutdown failed: %r" % (exc,))
        self.initialized = False
        self._steam_friends_ptr = 0
        self._steam_friends_source = None
        self._steam_apps_ptr = 0
        self._steam_apps_source = None


_backend = _SteamApiBackend()

_state = {
    "client_initialized": False,
    "server_initialized": False,
    "monitor_initialized": False,
    "scene": None,
    "recording": False,
    "overlay_active": False,
    "overlay_changed": False,
    "persona_name": u"",
    "language": u"english",
    "steam_id": 0,
    "current_lobby": 0,
    "next_lobby_id": 1,
    "next_guest_id": 1,
    "lobbies": {},
    "friend_lobbies": {},
    "friends": [],
    "server_lists": {
        "internet": [],
        "official": [],
        "user": [],
        "lan": [],
        "favourite": [],
        "history": [],
        "friends": [],
    },
    "server": {
        "auth": False,
        "secure": False,
        "server_mode": 0,
        "beta": False,
        "classic": False,
        "game_port": 0,
        "master_port": 0,
        "game_version": u"",
        "playlist_id": 0,
        "region": 0,
        "texture_skin": u"",
        "name": u"",
        "max_players": 0,
        "map_name": u"",
        "game_mode": u"",
        "public_ip": 0,
        "steam_id": 0,
        "players": {},
    },
    "stats": {},
    "server_stats": {},
    "server_achievements": {},
    "published_ugc_handle": 0,
    "subscribed_content": [],
    "password": u"",
    "session_ticket": "",
    "session_ticket_handle": 0,
    "authenticating_steam_id": 0,
    "authenticated_users": set(),
    "player_to_kick": 0,
    "kick_reason": u"",
    "no_auth_reason": u"Steam authentication is unavailable",
    "rich_presence": {},
    "callbacks": {
        "microtxn": None,
        "dlc_installed": None,
        "lobby_chat": None,
        "lobby_user_joined": None,
        "lobby_user_left": None,
        "lobby_user_kicked": None,
        "lobby_join_request": None,
        "server_requested": None,
        "lobby_data_changed": None,
    },
}


# When steam_api.dll exists, identity and language come only from Steamworks.
# When the DLL is physically absent, the client enters a local/offline mode and
# reads username/language from config_user.json. steam_emu.ini is never used.

_USER_CONFIG_DEFAULTS = {
    "username": u"Player",
    "language": u"english",
}


def _user_config_candidates():
    module_dir = os.path.dirname(os.path.abspath(__file__))
    script_dir = u""
    try:
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    except Exception:
        pass
    roots = [
        os.getcwd(),
        script_dir,
        module_dir,
        os.path.dirname(module_dir),
        os.path.dirname(os.path.dirname(module_dir)),
    ]
    seen = set()
    for root in roots:
        if not root:
            continue
        path = os.path.abspath(os.path.join(root, "config_user.json"))
        key = path.lower()
        if key in seen:
            continue
        seen.add(key)
        yield path


def _load_user_config():
    """Read the first valid config_user.json using Python 2-safe Unicode."""
    result = dict(_USER_CONFIG_DEFAULTS)
    for path in _user_config_candidates():
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "rb") as config_file:
                raw = config_file.read()
            if raw.startswith(b"\xef\xbb\xbf"):
                raw = raw[3:]
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("root JSON value must be an object")

            username = _to_text(data.get("username", u"")).strip()
            language = _to_text(data.get("language", u"")).strip().lower()
            if username:
                result["username"] = username
            if language:
                result["language"] = language
            _debug("loaded offline user config: %s" % path)
            return result
        except Exception as exc:
            _debug("failed to read %s: %r" % (path, exc))
    _debug("config_user.json not found; using offline defaults")
    return result


def _offline_mode():
    """Offline mode is allowed only when steam_api.dll is absent."""
    return not _backend.has_dll_file()


def _apply_offline_user_config():
    config = _load_user_config()
    _state["persona_name"] = config["username"]
    _state["language"] = config["language"]
    return config


def _ensure_lobby(lobby_id):
    lobby_id = _to_int(lobby_id, 0)
    with _lock:
        lobby = _state["lobbies"].get(lobby_id)
        if lobby is None:
            lobby = {
                "id": lobby_id,
                "owner": 0,
                "members": [],
                "data": {},
                "member_data": {},
                "max_players": 0,
                "accessibility": 0,
                "game_server": None,
                "chat": [],
                "ping": 0,
            }
            _state["lobbies"][lobby_id] = lobby
        return lobby


def _current_lobby():
    lobby_id = _state["current_lobby"]
    if not lobby_id:
        return None
    return _ensure_lobby(lobby_id)


def _finish_server_query(finished_callback):
    _queue_callback(finished_callback)
    return True


def _server_query(kind, modes_to_find, server_callback, finished_callback, region=None):
    del modes_to_find
    del region
    servers = list(_state["server_lists"].get(kind, []))
    for server in servers:
        _queue_callback(server_callback, server)
    _finish_server_query(finished_callback)
    return True


# ---------------------------------------------------------------------------
# Version and client lifecycle
# ---------------------------------------------------------------------------

def game_version():
    return GAME_VERSION


def ugc_version():
    return UGC_VERSION


def SteamInitializeClient():
    # Steam mode has priority whenever steam_api.dll exists.  The JSON fallback
    # is activated only when the DLL is physically absent.
    steam_ready = _backend.initialize()
    _state["steam_id"] = 0
    _state["persona_name"] = u""
    _state["language"] = u"english"
    if steam_ready:
        _state["steam_id"] = _backend.get_steam_id() or 0
        _state["persona_name"] = _backend.get_persona_name() or u""
        _state["language"] = (
            _backend.get_current_game_language() or u"english"
        )
    elif _offline_mode():
        _apply_offline_user_config()
        _debug("steam_api.dll absent; local config mode enabled")
    else:
        _debug("steam_api.dll exists but SteamAPI_Init failed; JSON fallback disabled")
    with _lock:
        _state["client_initialized"] = True
    return True


def SteamShutdownClient():
    SteamCancelSessionTicket()
    _backend.shutdown()
    with _lock:
        _state["client_initialized"] = False
    return None


def SteamIsLoggedOn():
    if _offline_mode():
        return bool(_state["client_initialized"])
    return bool(_backend.initialized)


def SteamStartScene():
    return None


def SteamStopScene():
    return None


def ShowSteamCommunity():
    steam_id = GetUserSteamID()
    if steam_id:
        webbrowser.open("https://steamcommunity.com/profiles/%s" % steam_id)
        return True
    return False


def SteamShowAchievements():
    steam_id = GetUserSteamID()
    if steam_id:
        url = "https://steamcommunity.com/profiles/%s/stats/AceofSpades?tab=achievements" % steam_id
        webbrowser.open(url)
        return True
    return False


def SteamShowWebPage(url):
    url = _to_text(url)
    if not url:
        return False
    return bool(webbrowser.open(url))


def SteamUpdate(scene):
    _state["scene"] = scene
    _backend.update()
    _drain_callbacks()
    return None


def SteamStartRecording():
    _state["recording"] = True
    return None


def SteamStopRecording():
    _state["recording"] = False
    return None


def SteamActivateGameOverlayToStore(app_id):
    app_id = _to_int(app_id, APP_ID)
    _state["overlay_changed"] = True
    webbrowser.open("https://store.steampowered.com/app/%d" % app_id)
    return None


def SteamIsDLCInstalled(app_id):
    """Check DLC availability through the backend implementation."""
    return _backend.is_dlc_installed(_to_app_id(app_id))


def SteamIsDemoRunning():
    return False


def SteamGetPersonaName():
    # With a Steam DLL, query ISteamFriends every time.  Only a physically
    # missing DLL enables the config_user.json fallback.
    if _offline_mode():
        config = _apply_offline_user_config()
        return config["username"]

    persona_name = _backend.get_persona_name()
    if not persona_name:
        _state["persona_name"] = u""
        return u""
    _state["persona_name"] = persona_name
    return persona_name


def SteamGetFriendPersonaName(steam_id):
    steam_id = _to_int(steam_id, 0)
    for friend in _state["friends"]:
        if isinstance(friend, dict) and _to_int(friend.get("steam_id"), 0) == steam_id:
            return _to_text(friend.get("name"))
    return u"[unknown]"


def SteamGetFriendList():
    return list(_state["friends"])


def GetUserSteamID():
    if _backend.initialized:
        steam_id = _backend.get_steam_id()
        if steam_id:
            _state["steam_id"] = steam_id
    return int(_state["steam_id"])


def SteamReceiveVoiceData(packet):
    # The original receives a packet-like object. No OpenAL/voice decoding is
    # attempted in the compatibility implementation.
    del packet
    return None


# ---------------------------------------------------------------------------
# Server browser and favourites
# ---------------------------------------------------------------------------

def SteamClearServerRequest():
    return None


def SteamGetInternetServerList(modes_to_find, server_callback, finished_callback, region):
    return _server_query("internet", modes_to_find, server_callback, finished_callback, region)


def SteamGetInternetOfficialServerList(modes_to_find, server_callback, finished_callback, region):
    return _server_query("official", modes_to_find, server_callback, finished_callback, region)


def SteamGetInternetUserServerList(modes_to_find, server_callback, finished_callback, region):
    return _server_query("user", modes_to_find, server_callback, finished_callback, region)


def SteamGetLANServerList(server_callback, finished_callback):
    return _server_query("lan", None, server_callback, finished_callback)


def SteamGetFavouriteServerList(server_callback, finished_callback):
    return _server_query("favourite", None, server_callback, finished_callback)


def SteamGetHistoryServerList(server_callback, finished_callback):
    return _server_query("history", None, server_callback, finished_callback)


def SteamGetFriendsServerList(server_callback, finished_callback):
    return _server_query("friends", None, server_callback, finished_callback)


def SteamAddFavouriteServer(ip, gamePort, queryPort, historyItem):
    entry = {
        "ip": ip,
        "gamePort": _to_int(gamePort),
        "queryPort": _to_int(queryPort),
        "historyItem": bool(historyItem),
    }
    target = "history" if historyItem else "favourite"
    with _lock:
        if entry not in _state["server_lists"][target]:
            _state["server_lists"][target].append(entry)
    return True


def SteamRemoveFavouriteServer(ip, gamePort, queryPort, historyItem):
    target = "history" if historyItem else "favourite"
    removed = False
    with _lock:
        kept = []
        for entry in _state["server_lists"][target]:
            match = (
                entry.get("ip") == ip
                and _to_int(entry.get("gamePort")) == _to_int(gamePort)
                and _to_int(entry.get("queryPort")) == _to_int(queryPort)
            )
            if match:
                removed = True
            else:
                kept.append(entry)
        _state["server_lists"][target] = kept
    return removed


def SteamIncrementIntStat(statName, incrementAmount):
    name = _to_text(statName)
    amount = _to_int(incrementAmount, 0)
    _state["stats"][name] = _state["stats"].get(name, 0) + amount
    return True


def SteamSetMicroTxnAuthResponseCallback(callback):
    _state["callbacks"]["microtxn"] = callback
    return None


def SteamSetDLCInstalledCallback(callback):
    _state["callbacks"]["dlc_installed"] = callback
    return None


# ---------------------------------------------------------------------------
# Workshop / UGC
# ---------------------------------------------------------------------------

def SteamShowWorkshop():
    webbrowser.open("https://steamcommunity.com/workshop/browse?appid=%d" % APP_ID)
    return None


def SteamGetSubscribedContentList():
    if _state["subscribed_content"]:
        return list(_state["subscribed_content"])
    results = []
    patterns = [
        os.path.join(os.getcwd(), "Subscribed_*.ugc"),
        os.path.join(os.getcwd(), "ugc", "Subscribed_*.ugc"),
    ]
    for pattern in patterns:
        for filename in glob.glob(pattern):
            if filename not in results:
                results.append(filename)
    return results


def SteamGetSubscribedContentTagList(published_file_id):
    del published_file_id
    return []


def SteamExtractSubscribedContent(published_file_id):
    del published_file_id
    return False


def SteamGetSubscribedContentTitle(published_file_id):
    del published_file_id
    return u""


# ---------------------------------------------------------------------------
# Dedicated server and authentication
# ---------------------------------------------------------------------------

def SteamInitializeServer(auth, secure, serverMode, beta, classic,
                          gamePort, masterPort, gameVersion, playlistId,
                          region, texture_skin):
    server = _state["server"]
    server.update({
        "auth": bool(auth),
        "secure": bool(secure),
        "server_mode": serverMode,
        "beta": bool(beta),
        "classic": bool(classic),
        "game_port": _to_int(gamePort),
        "master_port": _to_int(masterPort),
        "game_version": _to_text(gameVersion),
        "playlist_id": playlistId,
        "region": region,
        "texture_skin": _to_text(texture_skin),
    })
    _state["server_initialized"] = True
    return True


def SteamShutdownServer():
    _state["server_initialized"] = False
    return None


def SteamGetServerSteamId():
    return int(_state["server"]["steam_id"])


def SteamGetServerPublicIP():
    return int(_state["server"]["public_ip"])


def SteamInitializeMonitorServer(beta, gamePort, masterPort, gameVersion, region):
    _state["monitor_initialized"] = True
    _state["server"].update({
        "beta": bool(beta),
        "game_port": _to_int(gamePort),
        "master_port": _to_int(masterPort),
        "game_version": _to_text(gameVersion),
        "region": region,
    })
    return True


def SteamShutdownMonitorServer():
    _state["monitor_initialized"] = False
    return None


def SteamServerUserHasBeenAuthenticated(steam_id):
    return _to_int(steam_id, 0) in _state["authenticated_users"]


def SteamSetServerData(name, max_players, ip_callback):
    _state["server"]["name"] = _to_text(name)
    _state["server"]["max_players"] = _to_int(max_players)
    if callable(ip_callback):
        _queue_callback(ip_callback, _state["server"]["public_ip"])
    return True


def SteamUpdateMapName():
    return None


def SteamChangeMaxPlayersCount(count):
    _state["server"]["max_players"] = _to_int(count)
    return None


def SteamUpdateServer():
    _backend.update()
    _drain_callbacks()
    return None


def SteamGetPlayerToKick():
    return int(_state["player_to_kick"])


def SteamGetKickReason():
    return _state["kick_reason"]


def SteamGetNoAuthReason():
    return _state["no_auth_reason"]


def SteamHasUserLicenseForApp(steamId, DLCAppID):
    del steamId
    del DLCAppID
    # No license is fabricated by the fallback module.
    return False


def SteamSetMapName(name):
    _state["server"]["map_name"] = _to_text(name)
    return None


def SteamSetGameMode(mode):
    _state["server"]["game_mode"] = _to_text(mode)
    return None


def SteamSendSessionTicket(client):
    # Reconstructed from the original Cython implementation:
    #   packet = shared.packet.SteamSessionTicket()
    #   packet.ticket = SteamGetSessionTicket()
    #   packet.ticket_size = len(packet.ticket)
    #   client.send_packet(packet)
    #   return packet.ticket
    from shared import packet as packet_module

    auth_packet = packet_module.SteamSessionTicket()
    auth_packet.ticket = SteamGetSessionTicket()
    auth_packet.ticket_size = len(auth_packet.ticket)
    client.send_packet(auth_packet)
    return auth_packet.ticket


def SteamGetSessionTicket():
    # The original implementation cancels the previous handle before creating
    # a fresh ticket.
    SteamCancelSessionTicket()
    ticket, handle = _backend.create_session_ticket()
    _state["session_ticket"] = ticket
    _state["session_ticket_handle"] = handle
    return ticket


def SteamSendPassword(client, name, ip, port):
    del client
    del name
    del ip
    del port
    return False


def SteamCheckPassword(password):
    expected = _state["password"]
    if not expected:
        return True
    return _to_text(password) == expected


def SteamGetAuthenticatingSteamId():
    return int(_state["authenticating_steam_id"])


def SteamCancelSessionTicket():
    handle = _state.get("session_ticket_handle", 0)
    if handle:
        _backend.cancel_session_ticket(handle)
    _state["session_ticket"] = ""
    _state["session_ticket_handle"] = 0
    return None


def SteamStartAuthentication(ticket_size, ticket):
    del ticket_size
    del ticket
    _state["no_auth_reason"] = u"Steam authentication is unavailable"
    return False


def SteamEndAuthSession(steam_id):
    steam_id = _to_int(steam_id, 0)
    _state["authenticated_users"].discard(steam_id)
    return None


def SteamServerIncrementIntStat(steamId, statName, incrementAmount):
    steam_id = _to_int(steamId, 0)
    name = _to_text(statName)
    amount = _to_int(incrementAmount, 0)
    user_stats = _state["server_stats"].setdefault(steam_id, {})
    user_stats[name] = user_stats.get(name, 0) + amount
    return True


def SteamServerSetAchievement(steamId, achievementName):
    steam_id = _to_int(steamId, 0)
    achievements = _state["server_achievements"].setdefault(steam_id, set())
    achievements.add(_to_text(achievementName))
    return True


def SteamServerCreateUnauthenticatedPlayer():
    with _lock:
        guest_id = _state["next_guest_id"]
        _state["next_guest_id"] += 1
    return guest_id


def SteamServerUpdatePlayer(steamId, name, score):
    steam_id = _to_int(steamId, 0)
    _state["server"]["players"][steam_id] = {
        "name": _to_text(name),
        "score": _to_int(score),
    }
    return None


def SteamGetCurrentGameLanguage():
    if _offline_mode():
        config = _apply_offline_user_config()
        return config["language"]

    language = _backend.get_current_game_language()
    if language:
        _state["language"] = language
        return language
    return _state.get("language", u"english") or u"english"


# ---------------------------------------------------------------------------
# Lobby and matchmaking
# ---------------------------------------------------------------------------

def ResetLobbyState():
    with _lock:
        _state["current_lobby"] = 0
        _state["lobbies"] = {}
        _state["friend_lobbies"] = {}
    return None


def SteamCreateLobby(created_callback, create_error_callback):
    del create_error_callback
    with _lock:
        lobby_id = _state["next_lobby_id"]
        _state["next_lobby_id"] += 1
        lobby = _ensure_lobby(lobby_id)
        lobby["owner"] = GetUserSteamID()
        if lobby["owner"] and lobby["owner"] not in lobby["members"]:
            lobby["members"].append(lobby["owner"])
        _state["current_lobby"] = lobby_id
    _queue_callback(created_callback, lobby_id)
    return lobby_id


def SteamJoinLobby(joined_callback, join_error_callback, lobby_id):
    del join_error_callback
    lobby_id = _to_int(lobby_id, 0)
    if lobby_id <= 0:
        return False
    lobby = _ensure_lobby(lobby_id)
    steam_id = GetUserSteamID()
    with _lock:
        _state["current_lobby"] = lobby_id
        if steam_id and steam_id not in lobby["members"]:
            lobby["members"].append(steam_id)
    _queue_callback(joined_callback, lobby_id)
    return True


def SteamLeaveLobby():
    lobby = _current_lobby()
    steam_id = GetUserSteamID()
    if lobby is not None and steam_id in lobby["members"]:
        lobby["members"].remove(steam_id)
        callback = _state["callbacks"]["lobby_user_left"]
        _queue_callback(callback, steam_id)
    _state["current_lobby"] = 0
    return None


def SteamSetLobbyMaxPlayers(lobby_id, max_players):
    _ensure_lobby(lobby_id)["max_players"] = _to_int(max_players)
    return True


def SteamEnumerateFriendLobbies(found_callback):
    for friend_id, lobby_id in list(_state["friend_lobbies"].items()):
        _queue_callback(found_callback, friend_id, lobby_id)
    return None


def SteamEnumeratePublicLobbies(found_callback):
    for lobby_id in sorted(_state["lobbies"]):
        _queue_callback(found_callback, lobby_id)
    return None


def SteamGetLobbyMembers(lobby_id):
    return list(_ensure_lobby(lobby_id)["members"])


def SteamGetLobbyOwner():
    lobby = _current_lobby()
    return int(lobby["owner"]) if lobby is not None else 0


def SteamGetFriendLobbyOwner(friend_id):
    lobby_id = _state["friend_lobbies"].get(_to_int(friend_id, 0), 0)
    if not lobby_id:
        return 0
    return int(_ensure_lobby(lobby_id)["owner"])


def SteamShowInviteFriendOverlay():
    return None


def SteamRegisterLobbyChatCallback(callback):
    _state["callbacks"]["lobby_chat"] = callback
    return None


def SteamRegisterLobbyUpdateCallback(user_joined_callback,
                                     user_left_callback,
                                     user_kicked_callback):
    _state["callbacks"]["lobby_user_joined"] = user_joined_callback
    _state["callbacks"]["lobby_user_left"] = user_left_callback
    _state["callbacks"]["lobby_user_kicked"] = user_kicked_callback
    return None


def SteamRegisterLobbyJoinRequestCallback(request_handler_callback):
    _state["callbacks"]["lobby_join_request"] = request_handler_callback
    return None


def SteamRegisterServerRequestedCallback(server_callback):
    _state["callbacks"]["server_requested"] = server_callback
    return None


def SteamSendChatMessage(text):
    lobby = _current_lobby()
    if lobby is None:
        return False
    message = {
        "steam_id": GetUserSteamID(),
        "text": _to_text(text),
        "time": time.time(),
    }
    lobby["chat"].append(message)
    callback = _state["callbacks"]["lobby_chat"]
    if callable(callback):
        _queue_callback(callback, message["steam_id"], message["text"])
    return True


def SteamRegisterLobbyDataChangedCallback(data_changed_callback):
    _state["callbacks"]["lobby_data_changed"] = data_changed_callback
    return None


def SteamSetLobbyData(key, text):
    lobby = _current_lobby()
    if lobby is None:
        return False
    lobby["data"][_to_text(key)] = _to_text(text)
    return True


def SteamGetLobbyData(lobby_id, key):
    lobby = _ensure_lobby(lobby_id)
    return lobby["data"].get(_to_text(key), u"")


def SteamGetLobbyPing(lobby_id):
    return int(_ensure_lobby(lobby_id)["ping"])


def SteamClearAllPingRequests():
    return None


def SteamGetAllLobbyData(lobby_id):
    return dict(_ensure_lobby(lobby_id)["data"])


def SteamGetLobbyMemberName(friend_id):
    friend_id = _to_int(friend_id, 0)
    if friend_id == GetUserSteamID():
        return SteamGetPersonaName()
    return SteamGetFriendPersonaName(friend_id)


def SteamSetLobbyMemberData(key, text):
    lobby = _current_lobby()
    if lobby is None:
        return False
    steam_id = GetUserSteamID()
    data = lobby["member_data"].setdefault(steam_id, {})
    data[_to_text(key)] = _to_text(text)
    return True


def SteamGetLobbyMemberData(lobby_id, friend_id, key):
    lobby = _ensure_lobby(lobby_id)
    friend_data = lobby["member_data"].get(_to_int(friend_id, 0), {})
    return friend_data.get(_to_text(key), u"")


def SteamGetCurrentLobby():
    return int(_state["current_lobby"])


def SteamDumpLobbyData(lobby_id):
    lobby = _ensure_lobby(lobby_id)
    return {
        "id": lobby["id"],
        "owner": lobby["owner"],
        "members": list(lobby["members"]),
        "data": dict(lobby["data"]),
        "member_data": dict(lobby["member_data"]),
        "max_players": lobby["max_players"],
        "accessibility": lobby["accessibility"],
        "game_server": lobby["game_server"],
    }


def SteamAmITheLobbyOwner():
    lobby = _current_lobby()
    if lobby is None:
        return False
    return bool(GetUserSteamID() and lobby["owner"] == GetUserSteamID())


def SteamSetLobbyGameServer(ip, port):
    lobby = _current_lobby()
    if lobby is None:
        return False
    lobby["game_server"] = (ip, _to_int(port))
    return True


def SteamRefreshLobbyData(lobby_id):
    _ensure_lobby(lobby_id)
    return True


def SteamGetLobbyGameServer():
    lobby = _current_lobby()
    return lobby["game_server"] if lobby is not None else None


def SteamClearLobbyGameServer():
    lobby = _current_lobby()
    if lobby is not None:
        lobby["game_server"] = None
    return None


def SteamSetLobbyAccessibility(accessibility):
    lobby = _current_lobby()
    if lobby is None:
        return False
    lobby["accessibility"] = accessibility
    return True


def SteamSetRichPresenceLobby(lobby_id):
    _state["rich_presence"]["lobby"] = _to_int(lobby_id, 0)
    return None


def SteamSetRichPresenceServer(ip, port):
    _state["rich_presence"]["server"] = (ip, _to_int(port))
    return True


def SteamClearRichPresence():
    _state["rich_presence"] = {}
    return None


def SteamPublishUGC(filename, ugc_path, title, description, tags,
                    aos_ugc_handle, finished_callback):
    del filename
    del ugc_path
    del title
    del description
    del tags
    handle = _to_int(aos_ugc_handle, 0)
    if handle <= 0:
        handle = int(time.time() * 1000)
    _state["published_ugc_handle"] = handle
    _queue_callback(finished_callback, handle)
    return handle


def GetPublishedUGCHandle():
    return int(_state["published_ugc_handle"])


def SteamRequestLobbyJoin(lobbyID, block=False):
    lobby_id = _to_int(lobbyID, 0)
    callback = _state["callbacks"]["lobby_join_request"]
    if callable(callback):
        if block:
            return _call_callback(callback, (lobby_id,))
        return _queue_callback(callback, lobby_id)
    return False


def SteamIsGameOverlayActive():
    return bool(_state["overlay_active"])


def SteamHasGameOverlayActivationChanged():
    changed = bool(_state["overlay_changed"])
    _state["overlay_changed"] = False
    return changed


__all__ = [name for name in globals().keys() if name.startswith("Steam")]
__all__.extend(["game_version", "ugc_version", "GetUserSteamID",
                "ShowSteamCommunity", "GetPublishedUGCHandle",
                "ResetLobbyState"])
