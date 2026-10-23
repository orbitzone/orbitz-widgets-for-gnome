"""Pinned CSC geographic catalog and private weather preferences.

Data source: Countries States Cities Database, v5.0.0-export.1, ODbL 1.0.
SHA-256 values below were checked on the official GitHub release asset list.
The compressed JSON is data only, never code/SQL; gzip is bounded and nothing
is extracted by archive paths. All five release NOTICE files accompany the
local derived index. No source dataset is bundled with this repository.
"""
import contextlib
import fcntl
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import secrets
import sqlite3
import stat
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from http.client import HTTPException
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from orbitz_i18n import t

SNAPSHOT = 'v5.0.0-export.1'
SOURCE = 'https://github.com/dr5hn/countries-states-cities-database'
BASE = SOURCE + '/releases/download/' + SNAPSHOT + '/'
ASSET = 'json-countries+states+cities.json.gz'
DIGEST = '72cbb838c2004ccedc97fb18b10b2d8916fd9275bf227e9a4d26e814adc16eb8'
NOTICES = {
    'NOTICE-4-72-Clausula-Licencia-Abierta.txt': '6d94032c8a4acd9da801682a96118192d0a2a309f785dfb5498085c8558a9f4d',
    'NOTICE-pc_rebuild_7-distribution-notices.txt': '26253aea0cb5d917d9cd44f70fe41551fe0db28e54d18ace6982e9428e99bb8b',
    'NOTICE-Posti-postal-code-terms.txt': 'ac57a024e144a0a1a2cd4b49be645d186b61e008087ab8264bc52edbcbcd0708',
    'NOTICE-SOURCES.txt': 'b894f4bd60cf65e22377a78a26ea2264ed47eb4768a41b483955163adea3b08f',
    'NOTICE-Unicode-3.0.txt': '220ba0e1c43b99530d2d5bdb892a99dca0989414f51ab695ecd90163eaa1ec3b',
}
MAX_COMPRESSED = 6 * 1024 * 1024
MAX_EXPANDED = 96 * 1024 * 1024
MAX_DATABASE = 96 * 1024 * 1024
EXPECTED_COUNTS = (250, 5327, 152378)
ATTRIBUTION = dict(name='Countries States Cities Database', url=SOURCE, license='ODbL-1.0', snapshot=SNAPSHOT,
                   license_url='https://opendatacommons.org/licenses/odbl/1-0/',
                   credits='Data by Countries States Cities Database · GeoNames · © OpenStreetMap contributors · Wikidata. See the accompanying NOTICE-*.txt files for all credits and source terms.')
DEFAULT = dict(version=1, revision=0, unit='celsius', location=dict(id='builtin-brasilia', country_id='BR', region_id='',
               name='Brasília, DF', latitude=-15.7939, longitude=-47.8828, timezone='America/Sao_Paulo', country_name='Brazil', region_name=''))
LOCATION_KEYS = {'id','country_id','region_id','name','latitude','longitude','timezone'}
LOCATION_LABELS = {'country_name','region_name'}
ERROR_MESSAGES = {
    'catalog_unavailable': 'widgets.clima_widget.catalog_unavailable',
    'catalog_invalid': 'widgets.clima_widget.catalog_invalid',
    'catalog_checksum': 'widgets.clima_widget.catalog_checksum',
    'catalog_busy': 'widgets.clima_widget.catalog_busy',
    'catalog_limit': 'widgets.clima_widget.catalog_limit',
    'preferences_invalid': 'widgets.clima_widget.preferences_invalid',
    'preferences_conflict': 'widgets.clima_widget.preferences_conflict',
    'invalid_location': 'widgets.clima_widget.invalid_location',
    'invalid_search': 'widgets.clima_widget.invalid_search',
    'invalid_unit': 'widgets.clima_widget.invalid_unit',
}


class LocationError(ValueError):
    def __init__(self, key, code='invalid'):
        super().__init__(t(ERROR_MESSAGES[key]))
        self.code = code


def directory(path, create=False):
    """No-follow directory traversal; mutations stay anchored to this fd."""
    path = Path(path).absolute()
    if '..' in path.parts:
        raise LocationError('preferences_invalid')
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            try:
                following = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            except FileNotFoundError:
                if not create:
                    raise
                try: os.mkdir(part, 0o700, dir_fd=fd)
                except FileExistsError: pass
                following = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd = following
        return fd
    except BaseException:
        os.close(fd); raise


def read_at(fd, name, limit):
    handle = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    with os.fdopen(handle, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise LocationError('preferences_invalid')
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise LocationError('catalog_limit')
    return raw


def write_at(fd, name, raw):
    temporary = '.weather-' + secrets.token_hex(16)
    handle = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
    try:
        with os.fdopen(handle, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, name, src_dir_fd=fd, dst_dir_fd=fd); os.fsync(fd)
    finally:
        try: os.unlink(temporary, dir_fd=fd)
        except FileNotFoundError: pass


@contextlib.contextmanager
def locked(fd, name):
    lock = os.open(name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=fd)
    try:
        if not stat.S_ISREG(os.fstat(lock).st_mode): raise LocationError('preferences_invalid')
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: raise LocationError('catalog_busy', 'busy') from None
        yield
    finally: os.close(lock)


class SafeRedirect(HTTPRedirectHandler):
    def __init__(self): self.count = 0
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        part = urlsplit(newurl); self.count += 1
        if self.count > 3 or part.scheme != 'https' or part.hostname not in ('github.com', 'release-assets.githubusercontent.com', 'objects.githubusercontent.com') or part.username or part.password or part.port not in (None, 443):
            raise LocationError('catalog_unavailable', 'unavailable')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(name, digest, maximum, opener=None, *, deadline=None):
    request = Request(BASE + name, headers={'User-Agent': 'Orbitz-Widgets/1', 'Accept': 'application/octet-stream'})
    opener = opener or build_opener(SafeRedirect()).open
    deadline = min(time.monotonic() + 60, deadline if deadline is not None else float('inf'))
    try:
        with opener(request, timeout=8) as response:
            reader = getattr(response, 'read1', response.read)
            chunks = []; total = 0
            while True:
                if time.monotonic() > deadline: raise LocationError('catalog_unavailable', 'unavailable')
                chunk = reader(min(65536, maximum + 1 - total))
                if not chunk: break
                chunks.append(chunk); total += len(chunk)
                if total > maximum: raise LocationError('catalog_limit')
        raw = b''.join(chunks)
    except (HTTPError, URLError, HTTPException, TimeoutError, OSError):
        raise LocationError('catalog_unavailable', 'unavailable') from None
    if hashlib.sha256(raw).hexdigest() != digest:
        raise LocationError('catalog_checksum', 'checksum')
    return raw


def text(value):
    if not isinstance(value, str) or not 0 < len(value) <= 160 or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise LocationError('catalog_invalid')
    return value


def identity(value):
    if type(value) is int and 0 < value < 2**53: return str(value)
    if isinstance(value, str) and re.fullmatch('[1-9][0-9]{0,14}', value): return value
    raise LocationError('catalog_invalid')


def coords(latitude, longitude):
    try:
        if isinstance(latitude, bool) or isinstance(longitude, bool): raise ValueError()
        lat, lon = float(latitude), float(longitude)
        if not math.isfinite(lat) or not -90 <= lat <= 90 or not math.isfinite(lon) or not -180 <= lon <= 180: raise ValueError()
        return lat, lon
    except (ValueError, TypeError, OverflowError): raise LocationError('catalog_invalid') from None


def timezone(value):
    if value == 'auto': return value
    try: ZoneInfo(text(value))
    except (ValueError, ZoneInfoNotFoundError): raise LocationError('catalog_invalid') from None
    return value


def _build(raw, connection, deadline=None):
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as compressed:
            expanded = compressed.read(MAX_EXPANDED + 1)
        if len(expanded) > MAX_EXPANDED: raise LocationError('catalog_limit')
        countries = json.loads(expanded)
        if not isinstance(countries, list) or len(countries) > 300: raise LocationError('catalog_invalid')
        connection.executescript('CREATE TABLE countries(id TEXT PRIMARY KEY,name TEXT NOT NULL); CREATE TABLE regions(id TEXT PRIMARY KEY,name TEXT NOT NULL,country_id TEXT NOT NULL); CREATE TABLE cities(id TEXT PRIMARY KEY,name TEXT NOT NULL,country_id TEXT NOT NULL,region_id TEXT NOT NULL,latitude REAL NOT NULL,longitude REAL NOT NULL,timezone TEXT NOT NULL); CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);')
        count = [0, 0, 0]
        for country in countries:
            code = country['iso2']; name = text(country['name'])
            if not isinstance(code, str) or not re.fullmatch('[A-Z]{2}', code): raise LocationError('catalog_invalid')
            connection.execute('INSERT INTO countries VALUES(?,?)', (code, name)); count[0] += 1
            if not isinstance(country['states'], list) or len(country['states']) > 1000: raise LocationError('catalog_invalid')
            for region in country['states']:
                region_id = identity(region['id']); region_name = text(region['name'])
                connection.execute('INSERT INTO regions VALUES(?,?,?)', (region_id, region_name, code)); count[1] += 1
                if not isinstance(region['cities'], list) or len(region['cities']) > 50000: raise LocationError('catalog_invalid')
                for city in region['cities']:
                    if deadline is not None and count[2] % 1024 == 0 and time.monotonic() > deadline:
                        raise LocationError('catalog_unavailable', 'unavailable')
                    lat, lon = coords(city['latitude'], city['longitude'])
                    city_timezone = timezone(city.get('timezone') or 'auto')
                    connection.execute('INSERT INTO cities VALUES(?,?,?,?,?,?,?)', (identity(city['id']), text(city['name']), code, region_id, lat, lon, city_timezone)); count[2] += 1
                    if count[2] > 200000: raise LocationError('catalog_limit')
        if tuple(count) != EXPECTED_COUNTS: raise LocationError('catalog_invalid')
        connection.executescript('CREATE INDEX region_country ON regions(country_id,name,id); CREATE INDEX city_parent ON cities(country_id,region_id,name,id);')
        connection.execute('INSERT INTO metadata VALUES(?,?)', ('snapshot', SNAPSHOT))
        connection.execute('INSERT INTO metadata VALUES(?,?)', ('source_sha256', DIGEST))
        connection.commit()
    except (KeyError, TypeError, ValueError, RecursionError, OSError, EOFError, sqlite3.Error) as error:
        if isinstance(error, LocationError): raise
        raise LocationError('catalog_invalid') from None


def cache_directory():
    return Path(os.environ.get('XDG_CACHE_HOME') or Path.home()/'.cache')/'orbitz-widgets'/'locations'/SNAPSHOT


@contextlib.contextmanager
def catalog(opener=None):
    try: fd = directory(cache_directory(), True)
    except OSError: raise LocationError('catalog_unavailable', 'unavailable') from None
    connection = None
    try:
        with locked(fd, 'catalog.lock'):
            valid = False
            try:
                stamp = json.loads(read_at(fd, 'catalog.json', 32768))
                raw = read_at(fd, 'catalog.sqlite3', MAX_DATABASE)
                valid = stamp == {'snapshot': SNAPSHOT, 'source_sha256': DIGEST, 'database_sha256': hashlib.sha256(raw).hexdigest()}
                for name, digest in NOTICES.items():
                    valid = valid and hashlib.sha256(read_at(fd, name, 131072)).hexdigest() == digest
            except (FileNotFoundError, ValueError, RecursionError): pass
            if not valid:
                deadline = time.monotonic() + 90
                # Notices are verified and installed before the index is published.
                for name, digest in NOTICES.items():
                    notice = download(name, digest, 131072, opener, deadline=deadline)
                    write_at(fd, name, notice)
                raw = download(ASSET, DIGEST, MAX_COMPRESSED, opener, deadline=deadline)
                temporary = '.index-' + secrets.token_hex(16)
                handle = os.open(temporary, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd); os.close(handle)
                try:
                    connection = sqlite3.connect(f'/proc/self/fd/{fd}/{temporary}')
                    connection.execute('PRAGMA journal_mode=OFF')
                    _build(raw, connection, deadline); connection.close(); connection = None
                    value = read_at(fd, temporary, MAX_DATABASE)
                    synced = os.open(temporary, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
                    try: os.fsync(synced)
                    finally: os.close(synced)
                    manifest = {'snapshot': SNAPSHOT, 'source_sha256': DIGEST, 'database_sha256': hashlib.sha256(value).hexdigest()}
                    os.replace(temporary, 'catalog.sqlite3', src_dir_fd=fd, dst_dir_fd=fd); os.fsync(fd)
                    write_at(fd, 'catalog.json', json.dumps(manifest).encode())
                finally:
                    if connection is not None: connection.close(); connection = None
                    try: os.unlink(temporary, dir_fd=fd)
                    except FileNotFoundError: pass
            connection = sqlite3.connect(f'file:/proc/self/fd/{fd}/catalog.sqlite3?mode=ro', uri=True)
            connection.execute('PRAGMA query_only=ON'); connection.row_factory = sqlite3.Row
            connection.create_function('orbitz_fold', 1, lambda value: ''.join(c for c in unicodedata.normalize('NFKD', value.casefold()) if not unicodedata.combining(c)), deterministic=True)
            if connection.execute("SELECT value FROM metadata WHERE key='snapshot'").fetchone()[0] != SNAPSHOT: raise LocationError('catalog_invalid')
            yield connection
    except (OSError, sqlite3.Error, KeyError, TypeError, IndexError):
        raise LocationError('catalog_unavailable', 'unavailable') from None
    finally:
        if connection is not None: connection.close()
        os.close(fd)


def countries_regions_cities(kind, country=None, region=None, query='', cursor='0', *, opener=None):
    if kind not in ('countries', 'regions', 'cities') or not isinstance(cursor, str) or not re.fullmatch('[0-9]{1,6}', cursor): raise LocationError('catalog_invalid')
    if country is not None and (not isinstance(country, str) or not re.fullmatch('[A-Z]{2}', country)): raise LocationError('catalog_invalid')
    if kind == 'cities': region = identity(region)
    if query and (not isinstance(query, str) or len(query) > 100 or any(ord(c) < 32 for c in query)): raise LocationError('invalid_search')
    where = []; values = []
    if kind != 'countries': where.append('country_id=?'); values.append(country)
    if kind == 'cities': where.append('region_id=?'); values.append(region)
    if query: where.append('instr(orbitz_fold(name),orbitz_fold(?))>0'); values.append(query)
    clause = (' WHERE '+' AND '.join(where)) if where else ''
    limit = 300 if kind == 'countries' else 100; offset = int(cursor)
    with catalog(opener) as connection:
        total = connection.execute('SELECT count(*) FROM '+kind+clause, values).fetchone()[0]
        rows = connection.execute('SELECT * FROM '+kind+clause+' ORDER BY name COLLATE NOCASE,id LIMIT ? OFFSET ?', [*values,limit,offset]).fetchall()
    following = str(offset+len(rows)) if offset+len(rows) < total else None
    return dict(version=1, ok=True, kind=kind, items=[dict(row) for row in rows], total=total, next_cursor=following,
                complete=offset == 0 and following is None, snapshot=SNAPSHOT, attribution=dict(ATTRIBUTION))


def resolve_city(city_id, country, region, opener=None):
    city_id, region = identity(city_id), identity(region)
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{2}', country): raise LocationError('invalid_location')
    with catalog(opener) as connection:
        row = connection.execute('SELECT cities.*,countries.name AS country_name,regions.name AS region_name FROM cities JOIN countries ON countries.id=cities.country_id JOIN regions ON regions.id=cities.region_id WHERE cities.id=? AND cities.country_id=? AND cities.region_id=?', (city_id,country,region)).fetchone()
    if row is None: raise LocationError('invalid_location')
    return dict(row)


def preferences_directory():
    return Path(os.environ.get('XDG_CONFIG_HOME') or Path.home()/'.config')/'orbitz-widgets'


def geocoded_location(item):
    """Validate a search selection as data, without downloading the CSC index."""
    try:
        if not isinstance(item, dict) or type(item['id']) is not int: raise ValueError()
        ident = identity(item['id'])
        country = item['country_code']
        if not isinstance(country, str) or not re.fullmatch('[A-Z]{2}', country): raise ValueError()
        if any(type(item[key]) not in (int, float) for key in ('latitude', 'longitude')): raise ValueError()
        lat, lon = coords(item['latitude'], item['longitude'])
        tz = timezone(item['timezone'])
        if tz == 'auto': raise ValueError()
        admin = item.get('admin1', '')
        if admin != '': text(admin)
        return dict(id='geonames:' + ident, country_id=country, region_id='',
                    name=text(item['name']), latitude=lat, longitude=lon, timezone=tz,
                    country_name=text(item['country']), region_name=admin)
    except (KeyError, TypeError, ValueError, LocationError):
        raise LocationError('invalid_location') from None


def _preferences(fd):
    try: value = json.loads(read_at(fd, 'weather.json', 16384))
    except FileNotFoundError: return json.loads(json.dumps(DEFAULT))
    except (ValueError, RecursionError): raise LocationError('preferences_invalid') from None
    try:
        if set(value) != {'version','revision','unit','location'} or type(value['version']) is not int or value['version'] != 1 or type(value['revision']) is not int or not 0 <= value['revision'] < 2**31 or value['unit'] not in ('celsius','fahrenheit'): raise ValueError()
        selected=value['location']
        if not LOCATION_KEYS <= set(selected) <= LOCATION_KEYS | LOCATION_LABELS: raise ValueError()
        if isinstance(selected['id'], str) and selected['id'].startswith('geonames:'):
            identity(selected['id'][9:])
            if selected['region_id'] != '': raise ValueError()
        elif selected['id'] != 'builtin-brasilia': identity(selected['id']); identity(selected['region_id'])
        elif any(selected[key] != DEFAULT['location'][key] for key in LOCATION_KEYS): raise ValueError()
        if not isinstance(selected['country_id'],str) or not re.fullmatch('[A-Z]{2}',selected['country_id']): raise ValueError()
        text(selected['name']);coords(selected['latitude'],selected['longitude']);timezone(selected['timezone'])
        for key in LOCATION_LABELS:
            if key in selected and selected[key] != '': text(selected[key])
    except (KeyError, TypeError, ValueError): raise LocationError('preferences_invalid') from None
    return value


def preferences():
    try: fd=directory(preferences_directory())
    except FileNotFoundError: return dict(ok=True, **json.loads(json.dumps(DEFAULT)))
    except OSError: raise LocationError('preferences_invalid') from None
    try: return dict(ok=True, **_preferences(fd))
    except OSError: raise LocationError('preferences_invalid') from None
    finally: os.close(fd)


def set_preferences(*, unit=None, city_id=None, geocoded=None, country=None, region=None, expected=None, opener=None):
    if unit is None and city_id is None and geocoded is None: raise LocationError('preferences_invalid')
    if city_id is not None and geocoded is not None: raise LocationError('preferences_invalid')
    if unit is not None and unit not in ('celsius','fahrenheit'): raise LocationError('invalid_unit')
    if expected is not None and (type(expected) is not int or expected < 0): raise LocationError('preferences_invalid')
    selected=geocoded_location(geocoded) if geocoded is not None else resolve_city(city_id,country,region,opener) if city_id is not None else None
    try: fd=directory(preferences_directory(),True)
    except OSError: raise LocationError('preferences_invalid') from None
    try:
        with locked(fd,'weather.lock'):
            value=_preferences(fd)
            if expected is not None and value['revision'] != expected: raise LocationError('preferences_conflict','conflict')
            if value['revision'] == 2**31-1: raise LocationError('preferences_invalid')
            if selected is not None: value['location']=selected
            if unit is not None: value['unit']=unit
            value['revision'] += 1
            write_at(fd,'weather.json',json.dumps(value,ensure_ascii=False,allow_nan=False).encode())
            return dict(ok=True, **value)
    except OSError: raise LocationError('preferences_invalid') from None
    finally: os.close(fd)
