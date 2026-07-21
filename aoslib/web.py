# -*- coding: utf-8 -*-
"""Revival master-server browser adapter for the recovered retail menus."""
from __future__ import print_function

import json
import logging
import re

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

from twisted.internet.defer import Deferred
from twisted.internet.threads import deferToThread

import aoslib.a2s
from revival_http import HttpTransportError, request as http_request


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

REGION_ALL = "all"
REGION_US_WEST = "us_west"
REGION_US_EAST = "us_east"
REGION_EUROPE = "europe"
REGION_ASIA = "asia"
REGION_AUSTRALIA = "australia"

TYPE_ALL = "all"
TYPE_OFFICIAL = "official"
TYPE_COMMUNITY = "community"
TYPE_FAVORITES = "favorites"
TYPE_HISTORY = "history"
TYPE_LOCAL = "local"

SERVER_LIST = "https://www.aosplay.net/api/serverlist"

try:
    TEXT_TYPE = unicode
    INTEGER_TYPES = (int, long)
except NameError:
    TEXT_TYPE = str
    INTEGER_TYPES = (int,)

_CONTROL_CHARACTERS = re.compile(u"[\x00-\x1f\x7f]")
_HOST_PATTERN = re.compile(u"^[A-Za-z0-9.-]+$")
_REGION_PATTERN = re.compile(u"^[A-Za-z0-9_-]+$")


def _clean_text(value, fallback, maximum_length):
    if value is None:
        return fallback
    if isinstance(value, TEXT_TYPE):
        text = value
    elif isinstance(value, bytes):
        text = value.decode("utf-8", "replace")
    else:
        try:
            text = TEXT_TYPE(value)
        except (TypeError, ValueError):
            return fallback
    text = _CONTROL_CHARACTERS.sub(u" ", text)
    text = u" ".join(text.split())
    if not text:
        return fallback
    return text[:maximum_length]


def _integer(value, fallback, minimum, maximum):
    if isinstance(value, bool):
        return fallback
    if isinstance(value, float) and not value.is_integer():
        return fallback
    try:
        number = int(value)
    except (TypeError, ValueError, OverflowError):
        return fallback
    if number < minimum or number > maximum:
        return fallback
    return number


def _strict_integer(value, minimum, maximum, field):
    number = _integer(value, None, minimum, maximum)
    if number is None:
        raise ValueError("server %s is invalid" % field)
    return number


def _boolean(value, fallback=False):
    if isinstance(value, bool):
        return value
    normalized = _clean_text(value, u"", 12).lower()
    if normalized in (u"1", u"true", u"yes", u"on"):
        return True
    if normalized in (u"0", u"false", u"no", u"off"):
        return False
    return fallback


def _first(value, *names):
    for name in names:
        if name in value and value[name] is not None:
            return value[name]
    return None


def _host(value):
    candidate = _clean_text(value, u"", 253)
    labels = candidate.split(u".")
    if (
        not candidate
        or not _HOST_PATTERN.match(candidate)
        or candidate.startswith(u".")
        or candidate.endswith(u".")
        or u".." in candidate
        or any(label.startswith(u"-") or label.endswith(u"-") for label in labels)
    ):
        raise ValueError("server host is invalid")
    # The recovered Cython networking layer expects a narrow ASCII hostname.
    if TEXT_TYPE is not str:
        return candidate.encode("ascii")
    return candidate


def _ipv4_number(host):
    normalized = host.decode("ascii") if isinstance(host, bytes) else host
    parts = normalized.split(u".")
    if len(parts) != 4:
        return host
    values = []
    for part in parts:
        if not part.isdigit():
            return host
        number = int(part)
        if number < 0 or number > 255:
            return host
        values.append(number)
    result = 0
    for number in values:
        result = result * 256 + number
    return result


def _tags(value, version, playlist_id, region):
    raw_tags = value if isinstance(value, (list, tuple)) else []
    result = []
    for raw_tag in raw_tags[:24]:
        tag = _clean_text(raw_tag, u"", 64)
        if tag and tag not in result:
            result.append(tag)
    required = [
        version if version.startswith(u"v") else u"v%s" % version,
        u"playlist=%s" % playlist_id,
        u"region=%s" % region,
    ]
    for tag in required:
        if tag not in result:
            result.append(tag)
    return result[:24]


def _normalized_selector(value, fallback):
    normalized = _clean_text(value, fallback, 32).lower()
    return normalized if _REGION_PATTERN.match(normalized) else fallback


def _server_list_url(region, server_type):
    query = urlencode({"region": region, "type": server_type})
    return "%s?%s" % (SERVER_LIST, query)


def _master_server_list(region, server_type):
    status, data = http_request(
        _server_list_url(region, server_type),
        headers={"Accept": "application/json"},
        timeout=8,
    )
    if status != 200:
        raise HttpTransportError("master server returned HTTP %s" % status)
    return data


def _fetch_master_servers(region, server_type):
    raw = _master_server_list(region, server_type)
    return normalize_server_entries(
        filter_servers(get_list(raw), region, server_type)
    )


def _fetch_stored_or_local_servers(server_type):
    return normalize_server_entries(
        filter_servers(get_list(server_type), REGION_ALL, server_type)
    )


def get_servers(region=REGION_ALL, server_type=TYPE_ALL):
    """Return one Deferred containing bounded retail-compatible entries."""
    normalized_region = _normalized_selector(region, REGION_ALL)
    normalized_type = _normalized_selector(server_type, TYPE_ALL)
    valid_types = (
        TYPE_ALL,
        TYPE_OFFICIAL,
        TYPE_COMMUNITY,
        TYPE_FAVORITES,
        TYPE_HISTORY,
        TYPE_LOCAL,
    )
    if normalized_type not in valid_types:
        normalized_type = TYPE_ALL

    if normalized_type in (TYPE_FAVORITES, TYPE_HISTORY, TYPE_LOCAL):
        return deferToThread(_fetch_stored_or_local_servers, normalized_type)

    # WinHTTP and JSON parsing stay off the pyglet/Twisted reactor thread.
    return deferToThread(
        _fetch_master_servers,
        normalized_region,
        normalized_type,
    )


def process_servers(server_list, deferred, region=REGION_ALL, server_type=TYPE_ALL):
    filtered = filter_servers(server_list, region, server_type)
    deferred.callback(normalize_server_entries(filtered))


def filter_servers(servers, region=REGION_ALL, server_type=TYPE_ALL):
    normalized_region = _normalized_selector(region, REGION_ALL)
    normalized_type = _normalized_selector(server_type, TYPE_ALL)
    filtered = []
    for server in servers if isinstance(servers, list) else []:
        if not isinstance(server, dict):
            continue
        server_region = _normalized_selector(server.get("region"), u"")
        if normalized_region != REGION_ALL and server_region != normalized_region:
            continue
        official = _boolean(server.get("official"), False)
        if normalized_type == TYPE_OFFICIAL and not official:
            continue
        if normalized_type == TYPE_COMMUNITY and official:
            continue
        filtered.append(server)
    return filtered


def normalize_server_entries(servers):
    result = []
    for value in servers if isinstance(servers, list) else []:
        try:
            result.append(ServerEntry(value))
        except (AttributeError, TypeError, ValueError, OverflowError):
            logger.warning("Ignored a malformed Revival server-list entry")
    return result


class ServerEntry(object):
    """Strict boundary object consumed by the recovered Choose Match menu."""

    def __init__(self, value):
        if not isinstance(value, dict):
            raise ValueError("server entry must be an object")

        raw_identifier = _clean_text(value.get("identifier"), u"", 320)
        identifier_host = None
        identifier_port = None
        separator = raw_identifier.rfind(u":")
        if separator > 0:
            identifier_host = raw_identifier[:separator]
            identifier_port = raw_identifier[separator + 1:]

        host_source = _first(value, "ip")
        host = _host(host_source if host_source is not None else identifier_host)
        port_source = _first(value, "port")
        port = _strict_integer(
            port_source if port_source is not None else identifier_port,
            1,
            65535,
            "game port",
        )
        raw_query_port = _first(value, "queryPort", "query_port")
        query_port = (
            port
            if raw_query_port is None
            else _strict_integer(raw_query_port, 1, 65535, "query port")
        )

        max_players = _strict_integer(
            _first(value, "max_players", "maxPlayers", "max"),
            1,
            255,
            "capacity",
        )
        raw_players = _first(value, "players", "count")
        players = (
            0
            if raw_players is None
            else _strict_integer(raw_players, 0, 255, "population")
        )
        if players > max_players:
            raise ValueError("server population is invalid")
        raw_bots = _first(value, "bots", "bot_count", "botCount")
        raw_humans = _first(value, "human_players", "humanPlayers")
        if raw_bots is None and raw_humans is None:
            bots = 0
            human_players = players
        elif raw_bots is None:
            human_players = _strict_integer(
                raw_humans, 0, players, "human population"
            )
            bots = players - human_players
        elif raw_humans is None:
            bots = _strict_integer(raw_bots, 0, players, "bot population")
            human_players = players - bots
        else:
            bots = _strict_integer(raw_bots, 0, players, "bot population")
            human_players = _strict_integer(
                raw_humans, 0, players, "human population"
            )
            if bots + human_players != players:
                raise ValueError("server population split is invalid")

        name = _clean_text(value.get("name"), u"AoS Revival Server", 80)
        map_name = _clean_text(value.get("map"), u"classicgen", 80)
        game_mode = _clean_text(
            _first(value, "game_mode", "gameMode"),
            u"CTF",
            32,
        )
        mode_tla = _clean_text(
            _first(value, "mode_tla", "modeTla"),
            game_mode.lower(),
            16,
        ).lower()
        version = _clean_text(
            _first(value, "version", "game_version"),
            u"1.0",
            24,
        )
        region = _normalized_selector(value.get("region"), REGION_EUROPE)
        playlist_id = _integer(
            _first(value, "playlist_id", "playlistId"),
            0,
            0,
            65535,
        )
        ping = _integer(value.get("ping"), 50, 0, 60000)
        time_last_played = _integer(
            _first(value, "time_last_played", "timeLastPlayed"),
            0,
            0,
            0x7FFFFFFFFFFFFFFF,
        )
        texture_skin = _clean_text(
            _first(value, "texture_skin", "textureSkin"),
            None,
            32,
        )

        self.identifier = "%s:%s" % (host, port)
        self.name = name
        self.ip = host
        supplied_ipn = _first(value, "ipn")
        if isinstance(supplied_ipn, INTEGER_TYPES):
            self.ipn = _integer(supplied_ipn, _ipv4_number(host), 0, 0xFFFFFFFF)
        else:
            self.ipn = _ipv4_number(host)
        self.port = port
        self.queryPort = query_port
        self.players = players
        self.max_players = max_players
        self.count = players
        self.max = max_players
        self.bots = bots
        self.bot_count = bots
        self.human_players = human_players
        self.map = map_name
        self.game_mode = game_mode
        self.mode_tla = mode_tla
        self.version = version
        self.region = region
        self.official = _boolean(value.get("official"), False)
        self.playlist_id = playlist_id
        self.tags = _tags(value.get("tags"), version, playlist_id, region)
        self.ping = ping
        self.time_last_played = time_last_played
        self.texture_skin = texture_skin
        self.classic = _boolean(value.get("classic"), False)
        self.monitor = _boolean(value.get("monitor"), False)
        self.beta = _boolean(value.get("beta"), False)


def _stored_server_identifiers(kind):
    filename = (
        "server_history.json" if kind == TYPE_HISTORY else "server_favorites.json"
    )
    try:
        with open(filename, "rb") as stream:
            identifiers = json.loads(stream.read().decode("utf-8"))
    except (IOError, OSError, ValueError, UnicodeError):
        return []
    return identifiers if isinstance(identifiers, list) else []


def get_list(source):
    """Normalize master JSON, stored lists, or a LAN A2S scan."""
    if isinstance(source, bytes):
        source = source.decode("utf-8")
    if isinstance(source, TEXT_TYPE) and source.lower() not in (
        TYPE_FAVORITES,
        TYPE_HISTORY,
        TYPE_LOCAL,
    ):
        parsed = json.loads(source)
        return parsed if isinstance(parsed, list) else []

    normalized = _clean_text(source, u"", 20).lower()
    if normalized in (TYPE_FAVORITES, TYPE_HISTORY):
        raw = []
        for identifier in _stored_server_identifiers(normalized):
            identifier = _clean_text(identifier, u"", 320)
            try:
                host, port = identifier.rsplit(u":", 1)
                result = aoslib.a2s.get_server_info(ip=host, port=int(port))
                if result:
                    raw.append(result)
            except (AttributeError, ValueError, TypeError, OverflowError):
                continue
    elif normalized == TYPE_LOCAL:
        raw = aoslib.a2s.scan_local_network() or []
    else:
        return []

    result = []
    for entry in raw if isinstance(raw, list) else []:
        if not isinstance(entry, dict):
            continue
        host = entry.get("ip", "127.0.0.1")
        port = _integer(entry.get("port"), 32887, 1, 65535)
        result.append({
            "identifier": "%s:%s" % (host, port),
            "name": entry.get("name", "LAN Server"),
            "ip": host,
            "port": port,
            "queryPort": _integer(entry.get("queryPort"), port, 1, 65535),
            "players": _integer(entry.get("players"), 0, 0, 255),
            "max_players": _integer(entry.get("max_players"), 32, 1, 255),
            "bots": _integer(entry.get("bots"), 0, 0, 255),
            "map": entry.get("map", "classicgen"),
            "game_mode": entry.get("mode", "CTF"),
            "region": "local",
            "official": False,
            "ping": _integer(entry.get("ping"), 0, 0, 60000),
        })
    return result
