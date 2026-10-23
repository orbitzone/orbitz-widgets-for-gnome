#!/usr/bin/env python3
"""Open-Meteo current weather and validated seven-day forecasts.

Free API access is non-commercial (CC-BY 4.0 attribution required). Private
global location/unit preferences are read for each run; CLI flags override them.
"""
import argparse
from datetime import date, datetime, timedelta, timezone
import hashlib
from http.client import HTTPException
import json
import math
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from orbitz_i18n import t, locale
from widget_runtime import load, save
import weather_locations as locations

API = 'https://api.open-meteo.com/v1/forecast'
GEOCODING_API = 'https://geocoding-api.open-meteo.com/v1/search'
MAX_RESPONSE = 262144
FRESH_SECONDS = 300
MAX_STALE_SECONDS = 86400
DEFAULT_LOCATION = {'latitude': -15.7939, 'longitude': -47.8828, 'name': 'Brasília, DF'}
ATTRIBUTION = {'name': 'Open-Meteo', 'url': 'https://open-meteo.com/', 'license': 'CC-BY-4.0'}
PARAMS = {'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,is_day',
          'daily': 'temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code,wind_speed_10m_max',
          'wind_speed_unit': 'kmh', 'timezone': 'auto', 'forecast_days': 7}
# UI convention: wind icon at >=40 km/h; thunderstorms (WMO 95/96/99)
# retain priority. This threshold is a display choice, not a weather warning.
WIND_ICON_THRESHOLD_KMH = 40


class WeatherError(ValueError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def get_json(url, opener=None):
    request = Request(url, headers={'Accept': 'application/json', 'User-Agent': 'Orbitz-Widgets/1'})
    opener = opener or build_opener(NoRedirect()).open
    def finite_float(value):
        result = float(value)
        if not math.isfinite(result): raise ValueError()
        return result
    def reject_constant(value): raise ValueError()
    try:
        with opener(request, timeout=8) as response:
            reader = getattr(response, 'read1', response.read)
            deadline = time.monotonic() + 12
            chunks = []; total = 0
            while True:
                if time.monotonic() > deadline: raise TimeoutError()
                chunk = reader(min(65536, MAX_RESPONSE + 1 - total))
                if not chunk: break
                chunks.append(chunk); total += len(chunk)
                if total > MAX_RESPONSE: raise WeatherError(t('widgets.clima_widget.response_too_large'))
        result = json.loads(b''.join(chunks).decode('utf-8'), parse_float=finite_float, parse_constant=reject_constant)
    except (UnicodeError, ValueError, RecursionError) as error:
        if isinstance(error, WeatherError):
            raise
        raise WeatherError(t('widgets.clima_widget.invalid_response')) from None
    except (HTTPError, URLError, HTTPException, TimeoutError, OSError):
        raise WeatherError(t('widgets.clima_widget.network_unavailable')) from None
    if not isinstance(result, dict) or result.get('error'):
        raise WeatherError(t('widgets.clima_widget.invalid_response'))
    return result


def number(value, minimum, maximum):
    return type(value) in (int, float) and minimum <= value <= maximum and math.isfinite(value)


def display_name(value):
    if not isinstance(value, str) or not 0 < len(value.strip()) <= 160 or any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise WeatherError(t('widgets.clima_widget.invalid_location'))
    return value.strip()


def location(latitude, longitude, name):
    if not number(latitude, -90, 90) or not number(longitude, -180, 180):
        raise WeatherError(t('widgets.clima_widget.invalid_location'))
    return {'latitude': float(latitude), 'longitude': float(longitude), 'name': display_name(name)}


def zone(value):
    if not isinstance(value, str) or not 0 < len(value) <= 100:
        raise WeatherError(t('widgets.clima_widget.invalid_response'))
    try:
        return ZoneInfo(value)
    except (ValueError, ZoneInfoNotFoundError):
        raise WeatherError(t('widgets.clima_widget.invalid_response')) from None


def condition(code, day):
    if code == 0: return ('☀️' if day else '🌙'), t('widgets.clima_widget.clear_sky')
    if code in (1, 2): return '🌤️', t('widgets.clima_widget.partly_cloudy')
    if code == 3: return '☁️', t('widgets.clima_widget.cloudy')
    if code in (45, 48): return '🌫️', t('widgets.clima_widget.fog')
    if code in (51, 53, 55, 56, 57): return '🌦️', t('widgets.clima_widget.drizzle')
    if code in (61, 63, 65, 66, 67, 80, 81, 82): return '🌧️', t('widgets.clima_widget.rain')
    if code in (95, 96, 99): return '⛈️', t('widgets.clima_widget.thunderstorms')
    if code in (71, 73, 75, 77, 85, 86): return '❄️', t('widgets.clima_widget.snow')
    return '🌡️', t('widgets.clima_widget.weather')


def parse_forecast(data, selected, unit, *, now=None, allow_stale=False):
    now = time.time() if now is None else now
    try:
        if unit not in ('celsius', 'fahrenheit'):
            raise ValueError()
        current, daily = data['current'], data['daily']
        units, daily_units = data['current_units'], data['daily_units']
        symbol = '°C' if unit == 'celsius' else '°F'
        if any(units[key] != symbol for key in ('temperature_2m', 'apparent_temperature')) or any(daily_units[key] != symbol for key in ('temperature_2m_min', 'temperature_2m_max')):
            raise ValueError()
        if units['relative_humidity_2m'] != '%' or daily_units['precipitation_probability_max'] != '%':
            raise ValueError()
        if daily_units['wind_speed_10m_max'] != 'km/h':
            raise ValueError()
        latitude, longitude = data['latitude'], data['longitude']
        if not number(latitude, -90, 90) or not number(longitude, -180, 180):
            raise ValueError()
        if abs(latitude-selected['latitude']) > 2 or abs((longitude-selected['longitude']+180) % 360-180) > 2:
            raise ValueError()
        timezone_name = data['timezone']; local_zone = zone(timezone_name)
        stamp = datetime.fromisoformat(current['time'])
        if stamp.tzinfo is not None or 'T' not in current['time']:
            raise ValueError()
        age = now-stamp.replace(tzinfo=local_zone).timestamp()
        if age < -3600 or age > (MAX_STALE_SECONDS if allow_stale else 10800):
            raise ValueError()
        minimum, maximum = (-150, 150) if unit == 'celsius' else (-238, 302)
        if any(not number(current[key], minimum, maximum) for key in ('temperature_2m', 'apparent_temperature')):
            raise ValueError()
        if not number(current['relative_humidity_2m'], 0, 100) or type(current['is_day']) is not int or current['is_day'] not in (0, 1):
            raise ValueError()
        if type(current['weather_code']) is not int or not 0 <= current['weather_code'] <= 99:
            raise ValueError()
        keys = ('time', 'temperature_2m_min', 'temperature_2m_max', 'precipitation_probability_max', 'weather_code', 'wind_speed_10m_max')
        if any(not isinstance(daily[key], list) or len(daily[key]) != 7 for key in keys):
            raise ValueError()
        first = date.fromisoformat(daily['time'][0])
        today = datetime.fromtimestamp(now, local_zone).date()
        if (today-first).days not in ((0, 1) if allow_stale else (0,)):
            raise ValueError()
        days = []
        for index in range(7):
            day = daily['time'][index]; low = daily['temperature_2m_min'][index]; high = daily['temperature_2m_max'][index]
            rain = daily['precipitation_probability_max'][index]; code = daily['weather_code'][index]
            wind = daily['wind_speed_10m_max'][index]
            if not number(wind, 0, 500):
                raise ValueError()
            if day != (first+timedelta(days=index)).isoformat() or not number(low, minimum, maximum) or not number(high, minimum, maximum) or low > high or not number(rain, 0, 100) or type(code) is not int or not 0 <= code <= 99:
                raise ValueError()
            days.append(dict(date=day, temp_min=low, temp_max=high, precipitation_probability=rain, weather_code=code, wind_speed_max=wind))
        return dict(location={**selected, 'timezone': timezone_name}, unit=unit,
                    current=dict(time=current['time'], temperature=current['temperature_2m'], apparent_temperature=current['apparent_temperature'],
                                 humidity=current['relative_humidity_2m'], weather_code=current['weather_code'], is_day=current['is_day']), days=days)
    except (KeyError, TypeError, ValueError, OverflowError):
        raise WeatherError(t('widgets.clima_widget.invalid_response')) from None


def valid_weather(data):
    try:
        parse_forecast(data, DEFAULT_LOCATION, 'celsius')
        return True
    except WeatherError:
        return False


def cache_name(selected, unit):
    identity = [selected['latitude'], selected['longitude'], unit]
    digest = hashlib.sha256(json.dumps(identity, separators=(',', ':')).encode()).hexdigest()
    return 'weather-v2-' + digest + '.json'


def forecast(selected=None, unit='celsius', *, refresh=False, opener=None, now=None, allow_stale=False):
    selected = location(**(selected or DEFAULT_LOCATION))
    if unit not in ('celsius', 'fahrenheit'):
        raise WeatherError(t('widgets.clima_widget.invalid_unit'))
    now = time.time() if now is None else now
    identity = [selected['latitude'], selected['longitude'], unit]
    name = cache_name(selected, unit)
    cached = None
    try:
        item = load(name, MAX_STALE_SECONDS)
        if isinstance(item, dict) and item.get('identity') == identity and number(item.get('fetched'), 0, now) and now-item['fetched'] <= MAX_STALE_SECONDS:
            parsed = parse_forecast(item['data'], selected, unit, now=now, allow_stale=True)
            cached = (item, parsed)
    except (WeatherError, ValueError, TypeError, RecursionError):
        pass
    if cached and not refresh and now-cached[0]['fetched'] < FRESH_SECONDS:
        try:
            result = parse_forecast(cached[0]['data'], selected, unit, now=now)
            fetched = cached[0]['fetched']
            return _payload(result, fetched, False)
        except WeatherError:
            pass
    try:
        params = {**PARAMS, 'latitude': selected['latitude'], 'longitude': selected['longitude'], 'temperature_unit': unit}
        raw = get_json(API + '?' + urlencode(params), opener)
        parsed = parse_forecast(raw, selected, unit, now=now)
        save(name, {'identity': identity, 'fetched': now, 'data': raw})
        return _payload(parsed, now, False)
    except WeatherError:
        if allow_stale and cached:
            return _payload(cached[1], cached[0]['fetched'], True)
        raise


def _payload(parsed, fetched, stale):
    return dict(version=1, ok=True, **parsed, fetched_at=datetime.fromtimestamp(fetched, timezone.utc).isoformat(), stale=stale, attribution=dict(ATTRIBUTION))


def geocode(query, country_code=None, *, opener=None):
    query = display_name(query)
    if not 2 <= len(query) <= 100:
        raise WeatherError(t('widgets.clima_widget.invalid_search'))
    params = {'name': query, 'count': 10, 'language': 'en' if locale() == 'en-US' else 'pt', 'format': 'json'}
    if country_code is not None:
        if not isinstance(country_code, str) or not re.fullmatch('[A-Za-z]{2}', country_code):
            raise WeatherError(t('widgets.clima_widget.invalid_location'))
        params['countryCode'] = country_code.upper()
    raw = get_json(GEOCODING_API + '?' + urlencode(params), opener)
    results = raw.get('results', [])
    if not isinstance(results, list) or len(results) > 10:
        raise WeatherError(t('widgets.clima_widget.invalid_response'))
    items = []
    try:
        for item in results:
            if type(item['id']) is not int or not 0 < item['id'] < 2**53 or not re.fullmatch('[A-Z]{2}', item['country_code']):
                raise ValueError()
            if country_code and item['country_code'] != country_code.upper():
                raise ValueError()
            value = location(item['latitude'], item['longitude'], item['name'])
            zone(item['timezone'])
            items.append(dict(id=item['id'], **value, timezone=item['timezone'], country_code=item['country_code'],
                              country=display_name(item['country']), admin1=display_name(item['admin1']) if item.get('admin1') else ''))
    except (KeyError, TypeError, ValueError):
        raise WeatherError(t('widgets.clima_widget.invalid_response')) from None
    return dict(version=1, ok=True, results=items, complete=False,
                attribution={**ATTRIBUTION, 'location_source': 'GeoNames', 'location_url': 'https://www.geonames.org/'})


def render_summary(item):
    current = item['current']; day = item['days'][0]
    symbol = 'C' if item['unit'] == 'celsius' else 'F'
    icon, label = condition(current['weather_code'], current['is_day'])
    rows = [f"{icon} {item['location']['name']} · {current['temperature']:.0f}°{symbol}",
            t('widgets.clima_widget.feels_like', condition=label, temperature=current['apparent_temperature'], unit=symbol),
            f"↓ {day['temp_min']:.0f}°  ↑ {day['temp_max']:.0f}° · {t('widgets.clima_widget.humidity')} {current['humidity']}%",
            t('widgets.clima_widget.rain_today_value0', value0=day['precipitation_probability'])]
    if item['stale']:
        rows.append(t('widgets.clima_widget.offline_last_saved_forecast'))
    return '\n'.join(rows)


def main(argv=None, *, opener=None, output=print):
    parser = argparse.ArgumentParser(add_help=False)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--forecast-json', action='store_true')
    mode.add_argument('--geocode')
    mode.add_argument('--preferences-json', action='store_true')
    mode.add_argument('--set-unit')
    mode.add_argument('--set-location')
    mode.add_argument('--set-geocoded-location')
    mode.add_argument('--geo-countries', action='store_true')
    mode.add_argument('--geo-regions')
    mode.add_argument('--geo-cities', nargs=2)
    parser.add_argument('--country-code')
    parser.add_argument('--latitude', type=float)
    parser.add_argument('--longitude', type=float)
    parser.add_argument('--name')
    parser.add_argument('--unit')
    parser.add_argument('--region-id')
    parser.add_argument('--expected-revision', type=int)
    parser.add_argument('--query', default='')
    parser.add_argument('--cursor', default='0')
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args(argv)
    prefix = 'AZCLOCK_GEOCODING:' if args.geocode is not None else 'AZCLOCK_WEATHER:'
    preferences_mode = args.preferences_json or args.set_unit is not None or args.set_location is not None or args.set_geocoded_location is not None
    catalog_mode = args.geo_countries or args.geo_regions is not None or args.geo_cities is not None
    if preferences_mode: prefix = 'AZCLOCK_WEATHER_PREFS:'
    if catalog_mode: prefix = 'AZCLOCK_GEOCATALOG:'
    structured = args.forecast_json or args.geocode is not None or preferences_mode or catalog_mode
    unavailable_name = args.name or DEFAULT_LOCATION['name']
    try:
        if preferences_mode:
            if args.preferences_json: result = locations.preferences()
            else:
                geocoded = None
                if args.set_geocoded_location is not None:
                    try:
                        if len(args.set_geocoded_location.encode('utf-8')) > 16384: raise ValueError()
                        geocoded = json.loads(args.set_geocoded_location)
                        if not isinstance(geocoded, dict): raise ValueError()
                    except (ValueError, RecursionError, UnicodeError):
                        raise locations.LocationError('invalid_location') from None
                result = locations.set_preferences(unit=args.set_unit, city_id=args.set_location,
                                                   geocoded=geocoded,
                                                   country=args.country_code, region=args.region_id,
                                                   expected=args.expected_revision, opener=opener)
        elif catalog_mode:
            kind = 'countries' if args.geo_countries else 'regions' if args.geo_regions is not None else 'cities'
            country, region = (args.geo_cities if args.geo_cities else (args.geo_regions, None))
            result = locations.countries_regions_cities(kind, country, region, args.query, args.cursor, opener=opener)
        elif args.geocode is not None:
            result = geocode(args.geocode, args.country_code, opener=opener)
        else:
            preferences = locations.preferences() if args.latitude is None or args.unit is None else None
            if (args.latitude is None) != (args.longitude is None):
                raise WeatherError(t('widgets.clima_widget.invalid_location'))
            if args.latitude is None:
                selected = {key: preferences['location'][key] for key in ('latitude', 'longitude', 'name')}
                if args.name is not None: selected['name'] = args.name
            else:
                selected = location(args.latitude, args.longitude, args.name if args.name is not None else f'{args.latitude:.4f}, {args.longitude:.4f}')
            unit = args.unit if args.unit is not None else preferences['unit']
            unavailable_name = selected['name']
            result = forecast(selected, unit, refresh=args.refresh, opener=opener, allow_stale=not args.forecast_json)
        output(prefix + json.dumps(result, ensure_ascii=False, allow_nan=False) if structured else render_summary(result))
    except (WeatherError, locations.LocationError) as error:
        if structured:
            output(prefix + json.dumps(dict(version=1, ok=False, error=str(error), error_code=getattr(error, 'code', 'invalid')), ensure_ascii=False))
        else:
            output(t('widgets.clima_widget.summary_unavailable', name=unavailable_name))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
