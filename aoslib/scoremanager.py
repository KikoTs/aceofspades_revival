# -*- coding: utf-8 -*-
"""Legacy profile UI adapter backed by the Revival statistics API."""
from __future__ import print_function

import json
import re
try:
    from urllib import urlencode
except ImportError:  # pragma: no cover - Python 3 tooling compatibility
    from urllib.parse import urlencode

from twisted.internet.threads import deferToThread

from revival_http import HttpTransportError, request as http_request
from revival_store import canonical_legacy_id, get_secret, load_state


SCORE_SERVER_URL = "https://www.aosplay.net/api"
SCORE_SERVER_CONNECTION_TIMEOUT = 8.0
SESSION_TOKEN_PATTERN = re.compile(r"^aos_sess_[A-Za-z0-9_-]{43}$")
UINT64_MAX = 18446744073709551615
MAX_SAFE_COUNTER = 9007199254740991
OFFLINE_PROFILE_ID = "18446744073709551615"

try:
    integer_types = (int, long)
    long_type = long
    text_types = (basestring,)
    text_type = unicode
except NameError:  # pragma: no cover - Python 3 tooling compatibility
    integer_types = (int,)
    long_type = int
    text_types = (str,)
    text_type = str


def _session_token():
    token = get_secret(load_state(), "access_token")
    if isinstance(token, bytes):
        try:
            token = token.decode("ascii")
        except UnicodeDecodeError:
            return None
    if not isinstance(token, text_types) or not SESSION_TOKEN_PATTERN.match(token):
        return None
    return token


def _clean_name(value):
    if isinstance(value, bytes) and text_type is not bytes:
        value = value.decode("utf-8", "replace")
    if not isinstance(value, text_types):
        return None
    value = u" ".join(value.split()).strip()
    return value[:64] if value else None


def _counter(value):
    if isinstance(value, bool) or not isinstance(value, integer_types):
        return None
    if value < 0 or value > MAX_SAFE_COUNTER:
        return None
    return value


def _stat_pair(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    count = _counter(value[0])
    score = _counter(value[1])
    return [count, score] if count is not None and score is not None else None


def _stats_map(value):
    if not isinstance(value, dict) or len(value) > 1024:
        return None
    normalized = {}
    for stat_id, pair in value.items():
        if not isinstance(stat_id, text_types):
            return None
        stat_id = stat_id.strip()
        normalized_pair = _stat_pair(pair)
        if (
            not stat_id.isdigit()
            or len(stat_id) > 6
            or normalized_pair is None
        ):
            return None
        normalized[str(stat_id)] = normalized_pair
    return normalized


def _normalize_profile_payload(value):
    if not isinstance(value, dict):
        return {}
    profile = value.get("profile")
    if not isinstance(profile, dict):
        return {}
    name = _clean_name(profile.get("name"))
    stats = _stats_map(profile.get("stats"))
    total = _stat_pair(profile.get("total", [0, 0]))
    if name is None or stats is None or total is None:
        return {}
    normalized = {"profile": {"name": name, "stats": stats, "total": total}}
    updated_at = profile.get("updated_at")
    if isinstance(updated_at, text_types) and len(updated_at) <= 64:
        normalized["profile"]["updated_at"] = updated_at
    return normalized


def _normalize_player_id(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, integer_types):
        player_id = long_type(value)
    elif isinstance(value, text_types) and value.isdigit():
        try:
            player_id = long_type(value)
        except ValueError:
            return None
    else:
        return None
    return player_id if 0 <= player_id <= UINT64_MAX else None


def _normalize_leaderboard_payload(value):
    if not isinstance(value, dict) or not isinstance(value.get("leaderboard"), list):
        return {"leaderboard": []}
    normalized = []
    for row in value["leaderboard"][:100]:
        if not isinstance(row, (list, tuple)) or len(row) != 5:
            continue
        player_id = _normalize_player_id(row[0])
        name = _clean_name(row[1])
        total = _stat_pair(row[2])
        stats = _stats_map(row[3])
        rank = _counter(row[4])
        if (
            player_id is None
            or name is None
            or total is None
            or stats is None
            or rank is None
            or rank < 1
        ):
            continue
        normalized.append([player_id, name, total, stats, rank])
    return {"leaderboard": normalized}


def _fallback_profile_payload():
    """Return a renderable zero-stat profile for the launcher's identity.

    The retail profile menu treats a missing ``profile`` member as a network
    failure and otherwise accepts an empty stats mapping.  Keeping the local
    identity visible is preferable to leaving the recovered menu on its
    permanent connecting screen when a newly-created account has not produced
    a statistics row yet.
    """
    account = load_state().get("account") or {}
    name = _clean_name(account.get("nickname") or account.get("username"))
    if name is None:
        return {}
    return {
        "profile": {
            "name": name,
            "stats": {},
            "total": [0, 0],
        }
    }


def _request_form(path, fields):
    data = urlencode(fields, True)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "User-Agent": "AoS-Revival-Client/1.0 (protocol 168)",
    }
    status, response = http_request(
        SCORE_SERVER_URL + path,
        method="POST",
        headers=headers,
        body=data,
        timeout=SCORE_SERVER_CONNECTION_TIMEOUT,
    )
    if status != 200:
        raise HttpTransportError("statistics service returned HTTP %s" % status)
    return response


def _request_profile(steam_id):
    token = _session_token()
    if token:
        status, response = http_request(
            SCORE_SERVER_URL + "/profile/me",
            method="GET",
            headers={
                "Accept": "application/json",
                "Authorization": "Bearer " + token,
                "User-Agent": "AoS-Revival-Client/1.0 (protocol 168)",
            },
            timeout=SCORE_SERVER_CONNECTION_TIMEOUT,
        )
        if status == 200:
            return response
        # Older deployments and expired sessions can still serve the public,
        # read-only profile tied to the launcher's last canonical identity.
    return _request_form("/profile", {"steamid": _profile_id(steam_id)})


def _profile_id(fallback):
    account = (load_state().get("account") or {})
    if account.get("offline"):
        # Never let a shared emulator Steam ID impersonate a real profile while
        # a preserved local guest is active.
        return OFFLINE_PROFILE_ID
    return canonical_legacy_id() or str(fallback)


def _friend_profile_ids(friend_list):
    normalized = []
    seen = set()
    for value in list(friend_list or []) + [canonical_legacy_id()]:
        player_id = _normalize_player_id(value)
        if player_id is None:
            continue
        player_id = str(player_id)
        if player_id not in seen:
            normalized.append(player_id)
            seen.add(player_id)
    return normalized


class ScoreManager(object):
    def __init__(self):
        self.request_profile_callback = None
        self.request_leaderboard_callback = None

        # Menus are cached and can be opened again while an older worker is
        # still finishing.  Generations prevent that stale result from being
        # delivered to the callback installed by the new menu instance.
        self._profile_request_generation = 0
        self._leaderboard_request_generation = 0

    def request_profile(self, steam_id):
        self._profile_request_generation += 1
        generation = self._profile_request_generation
        try:
            request = deferToThread(_request_profile, steam_id)
        except Exception as error:
            # A stopped/unavailable Twisted thread pool used to leave the UI
            # on "Connecting" forever because no Deferred existed to errback.
            self.__request_profile_error_callback(error, generation)
            return None
        request.addCallbacks(
            lambda result: self.__request_profile_callback(result, generation),
            lambda error: self.__request_profile_error_callback(error, generation),
        )
        return request

    def set_request_profile_callback(self, callback):
        self.request_profile_callback = callback

    def clear_request_profile_callback(self):
        self.request_profile_callback = None
        self._profile_request_generation += 1
        # The recovered LeaderboardMenu calls this method from on_stop instead
        # of its leaderboard counterpart. Clear both to prevent a late worker
        # result from calling a menu that has already been destroyed.
        if self.request_leaderboard_callback is not None:
            self.clear_request_leaderboard_callback()

    def __request_profile_callback(self, result, generation):
        if generation != self._profile_request_generation:
            return
        try:
            profile = _normalize_profile_payload(json.loads(result))
        except (ValueError, TypeError):
            profile = {}
        if not profile:
            profile = _fallback_profile_payload()
        if self.request_profile_callback:
            self.request_profile_callback(profile)

    def __request_profile_error_callback(self, result, generation):
        if generation != self._profile_request_generation:
            return
        if self.request_profile_callback:
            self.request_profile_callback(_fallback_profile_payload())

    def request_global_leaderboard(self, stat_id_list, sort_stat_id):
        return self.__request_leaderboard(stat_id_list, sort_stat_id)

    def request_local_leaderboard(self, stat_id_list, sort_stat_id, steam_id):
        return self.__request_leaderboard(
            stat_id_list,
            sort_stat_id,
            steam_id=_profile_id(steam_id),
            noof_results=10,
        )

    def request_friend_leaderboard(self, stat_id_list, sort_stat_id, friend_list):
        return self.__request_leaderboard(
            stat_id_list,
            sort_stat_id,
            friend_list=_friend_profile_ids(friend_list),
        )

    def __request_leaderboard(
        self,
        stat_id_list,
        sort_stat_id,
        steam_id=None,
        noof_results=None,
        friend_list=None,
    ):
        fields = {
            "sortid": sort_stat_id,
            "noof_stats": len(stat_id_list),
            "statid": stat_id_list,
        }
        if steam_id:
            fields["steamid"] = steam_id
        if noof_results:
            fields["noof_results"] = noof_results
        if friend_list:
            fields["noof_friends"] = len(friend_list)
            fields["friend"] = friend_list
        self._leaderboard_request_generation += 1
        generation = self._leaderboard_request_generation
        try:
            request = deferToThread(_request_form, "/leaderboard", fields)
        except Exception as error:
            self.__request_leaderboard_error_callback(error, generation)
            return None
        request.addCallbacks(
            lambda result: self.__request_leaderboard_callback(result, generation),
            lambda error: self.__request_leaderboard_error_callback(error, generation),
        )
        return request

    def set_request_leaderboard_callback(self, callback):
        self.request_leaderboard_callback = callback

    def clear_request_leaderboard_callback(self):
        self.request_leaderboard_callback = None
        self._leaderboard_request_generation += 1

    def __request_leaderboard_callback(self, result, generation):
        if generation != self._leaderboard_request_generation:
            return
        try:
            leaderboard = _normalize_leaderboard_payload(json.loads(result))
        except (ValueError, TypeError):
            leaderboard = {"leaderboard": []}
        if self.request_leaderboard_callback:
            self.request_leaderboard_callback(leaderboard)

    def __request_leaderboard_error_callback(self, result, generation):
        if generation != self._leaderboard_request_generation:
            return
        if self.request_leaderboard_callback:
            self.request_leaderboard_callback({"leaderboard": []})
