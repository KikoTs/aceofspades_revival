import json
import os

from twisted.internet.defer import succeed
from twisted.web.client import getPage

from aoslib.scenes.frontend.serverInfo import ServerInfo
from aoslib.tools import get_server_details, ip_to_int, make_server_identifier

REGION_ALL = 'all'
REGION_US_WEST = 'us_west'
REGION_US_EAST = 'us_east'
REGION_EUROPE = 'europe'
REGION_ASIA = 'asia'

TYPE_ALL = 'all'
TYPE_OFFICIAL = 'official'
TYPE_COMMUNITY = 'community'
TYPE_FAVORITES = 'favorites'

SERVER_LIST = os.environ.get('AOS_SERVER_LIST_URL', 'https://aceofspades-web-server.vercel.app/serverlist')
FAVORITES_PATH = 'server_favorites.json'
DEFAULT_PORT = 32887
DEFAULT_REGION = REGION_EUROPE

MODE_ALIASES = {
    'ctf': 'ctf',
    'capture the flag': 'ctf',
    'classic ctf': 'ctf',
    'tdm': 'tdm',
    'team deathmatch': 'tdm',
    'deathmatch': 'tdm',
    'dem': 'dem',
    'demolition': 'dem',
    'dia': 'dia',
    'diamond mine': 'dia',
    'mh': 'mh',
    'multihill': 'mh',
    'oc': 'oc',
    'occupation': 'oc',
    'tc': 'tc',
    'cp': 'tc',
    'territory': 'tc',
    'territory control': 'tc',
    'vip': 'vip',
    'zom': 'zom',
    'zombie': 'zom',
    'ugc': 'ugc',
    'tut': 'tut',
    'tutorial': 'tut',
}


def log(message):
    print '[web]', message


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_bool(value):
    if isinstance(value, basestring):
        return value.strip().lower() in ('1', 'true', 'yes', 'on')
    return bool(value)


def _normalize_server_type(server_type):
    if not isinstance(server_type, basestring):
        return TYPE_ALL
    return server_type.strip().lower()


def _normalize_region(region):
    if not isinstance(region, basestring):
        return REGION_ALL
    value = region.strip().lower()
    if value == 'all regions':
        return REGION_ALL
    return value


def _decode_payload(data):
    if isinstance(data, unicode):
        return data
    return data.decode('utf-8', 'ignore')


def _extract_servers(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ('servers', 'data', 'results'):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []


def _normalize_mode_tla(value):
    if value is None:
        return 'tdm'
    mode = str(value).strip().lower()
    return MODE_ALIASES.get(mode, mode if len(mode) <= 4 else 'tdm')


def _normalize_identifier(entry):
    identifier = entry.get('identifier')
    if identifier:
        return str(identifier)
    ip = entry.get('ip')
    if not ip:
        return None
    port = _to_int(entry.get('port'), DEFAULT_PORT)
    return make_server_identifier(ip, port)


def _build_tags(entry, region, playlist_id, texture_skin):
    tags = []
    version = str(entry.get('version', '0'))
    tags.append('v%s' % version)
    tags.append('playlist=%s' % playlist_id)
    tags.append('region=%s' % region)

    if _to_bool(entry.get('classic')):
        tags.append('classic')
    if _to_bool(entry.get('beta')):
        tags.append('beta')
    if _to_bool(entry.get('monitor')):
        tags.append('monitor')
    if texture_skin:
        tags.append('skin=%s' % texture_skin)

    raw_tags = entry.get('tags', [])
    if isinstance(raw_tags, basestring):
        raw_tags = [item.strip() for item in raw_tags.split(',') if item.strip()]
    for tag in raw_tags:
        if tag not in tags:
            tags.append(tag)
    return tags


def _entry_matches(entry, region, server_type):
    entry_region = _normalize_region(entry.get('region', DEFAULT_REGION))
    if region != REGION_ALL and entry_region != region:
        return False
    is_official = _to_bool(entry.get('official'))
    if server_type == TYPE_OFFICIAL and not is_official:
        return False
    if server_type == TYPE_COMMUNITY and is_official:
        return False
    return True


def _build_server_info(entry):
    identifier = _normalize_identifier(entry)
    if not identifier:
        return None

    try:
        ip_text, port = get_server_details(identifier)
    except Exception as exc:
        log('Skipping invalid server identifier %r (%s)' % (identifier, exc))
        return None

    query_port = _to_int(entry.get('queryPort', entry.get('query_port', port)), port)
    players = _to_int(entry.get('players', entry.get('count', 0)), 0)
    max_players = _to_int(entry.get('max_players', entry.get('max', 32)), 32)
    ping = _to_int(entry.get('ping', 0), 0)
    region = _normalize_region(entry.get('region', DEFAULT_REGION))
    playlist_id = _to_int(entry.get('playlist_id', 0), 0)
    texture_skin = entry.get('texture_skin') or entry.get('skin')
    mode_tla = _normalize_mode_tla(entry.get('mode_tla') or entry.get('mode') or entry.get('game_mode'))
    name = entry.get('name') or identifier
    map_name = entry.get('map') or entry.get('map_name') or 'Unknown'
    tags = _build_tags(entry, region, playlist_id, texture_skin)

    ip_number = ip_to_int(ip_text)
    server = ServerInfo(name, ip_number, port, query_port, ping * 1000, map_name, mode_tla, players, max_players, tags, _to_int(entry.get('time_last_played', 0), 0))
    server.identifier = make_server_identifier(ip_number, port)
    server.ip = server.identifier.split(':')[0]
    server.ipn = ip_number
    server.port = port
    server.queryPort = query_port
    server.players = players
    server.max_players = max_players
    server.ping = ping
    server.region = region
    server.official = _to_bool(entry.get('official'))
    server.texture_skin = texture_skin
    server.playlist_id = str(playlist_id)
    server.beta = _to_bool(entry.get('beta', server.beta))
    server.monitor = _to_bool(entry.get('monitor', server.monitor))
    return server


class ServerEntry(object):

    def __init__(self, value):
        server = _build_server_info(value)
        if server is None:
            raise ValueError('Invalid server entry: %r' % (value,))
        self.__dict__.update(server.__dict__)


def _load_favorite_entries(region):
    if not os.path.exists(FAVORITES_PATH):
        return []

    try:
        favorites = json.load(open(FAVORITES_PATH, 'rb'))
    except Exception as exc:
        log('Failed to read favourites file: %s' % exc)
        return []

    if not isinstance(favorites, list):
        return []

    entries = []
    for identifier in favorites:
        if not isinstance(identifier, basestring):
            continue
        entry = {
            'identifier': identifier,
            'name': identifier,
            'region': region if region != REGION_ALL else DEFAULT_REGION,
            'official': False,
            'players': 0,
            'max_players': 32,
            'map': 'Unknown',
            'mode_tla': 'ctf',
            'ping': 0,
        }
        server = _build_server_info(entry)
        if server is not None:
            entries.append(server)
    return entries


def _handle_page_success(data, region, server_type):
    try:
        payload = json.loads(_decode_payload(data))
    except (TypeError, ValueError) as exc:
        log('Failed to parse server list: %s' % exc)
        return []

    entries = []
    for entry in _extract_servers(payload):
        if not isinstance(entry, dict):
            continue
        if not _entry_matches(entry, region, server_type):
            continue
        server = _build_server_info(entry)
        if server is not None:
            entries.append(server)
    return entries


def _handle_page_error(failure, url):
    message = getattr(failure, 'getErrorMessage', None)
    if callable(message):
        message = message()
    if not message:
        message = str(failure)
    log('Failed to fetch server list from %s: %s' % (url, message))
    return []


def get_servers(region=REGION_ALL, server_type=TYPE_ALL, server_list_url=None):
    normalized_region = _normalize_region(region)
    normalized_type = _normalize_server_type(server_type)

    if normalized_type == TYPE_FAVORITES:
        return succeed(_load_favorite_entries(normalized_region))

    url = server_list_url or SERVER_LIST
    deferred = getPage(url)
    deferred.addCallback(_handle_page_success, normalized_region, normalized_type)
    deferred.addErrback(_handle_page_error, url)
    return deferred
