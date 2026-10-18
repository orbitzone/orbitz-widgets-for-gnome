#!/usr/bin/env python3
import json
import time
import math
import stat
import os
import tempfile
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

CACHE = Path(__file__).resolve().parent.parent / 'work' / 'clima-brasilia.json'
PARAMS = {
    'latitude': -15.7939, 'longitude': -47.8828,
    'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,is_day',
    'daily': 'temperature_2m_max,temperature_2m_min,precipitation_probability_max',
    'timezone': 'America/Sao_Paulo', 'forecast_days': 1,
}

def condition(code, day):
    if code == 0: return ('☀️' if day else '🌙'), 'Céu limpo'
    if code in (1, 2): return '🌤️', 'Parcialmente nublado'
    if code == 3: return '☁️', 'Nublado'
    if code in (45, 48): return '🌫️', 'Nevoeiro'
    if code in (51, 53, 55, 56, 57): return '🌦️', 'Garoa'
    if code in (61, 63, 65, 66, 67, 80, 81, 82): return '🌧️', 'Chuva'
    if code in (95, 96, 99): return '⛈️', 'Trovoadas'
    if code in (71, 73, 75, 77, 85, 86): return '❄️', 'Neve'
    return '🌡️', 'Clima'

def valid_weather(data):
    if not isinstance(data, dict):
        return False
    c, d = data.get('current'), data.get('daily')
    if not isinstance(c, dict) or not isinstance(d, dict):
        return False
    def number(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    current = ('temperature_2m', 'relative_humidity_2m', 'apparent_temperature', 'weather_code', 'is_day')
    daily = ('temperature_2m_min', 'temperature_2m_max', 'precipitation_probability_max')
    return (all(number(c.get(k)) for k in current) and
            all(isinstance(d.get(k), list) and d[k] and number(d[k][0]) for k in daily))

def load_cache():
    try:
        fd = os.open(CACHE, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                return None
            raw = stream.read(262145)
        if len(raw) > 262144:
            return None
        cache = json.loads(raw)
        saved = cache.get('saved') if isinstance(cache, dict) else None
        if (isinstance(saved, (int, float)) and not isinstance(saved, bool) and
                math.isfinite(saved) and saved <= time.time() + 60 and valid_weather(cache.get('data'))):
            return cache
    except (OSError, ValueError, TypeError):
        pass
    return None

def save_cache(data):
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='clima-', dir=CACHE.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump({'saved': time.time(), 'data': data}, stream)
        os.replace(name, CACHE)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def main():
    cached = load_cache()
    stale = False
    if cached and time.time() - cached['saved'] < 300:
        data = cached['data']
    else:
        try:
            url = 'https://api.open-meteo.com/v1/forecast?' + urlencode(PARAMS)
            with urlopen(url, timeout=8) as response:
                raw = response.read(262145)
                if len(raw) > 262144:
                    raise ValueError('Resposta muito grande')
                data = json.loads(raw)
            if not valid_weather(data):
                raise ValueError('Resposta inválida')
            try:
                save_cache(data)
            except OSError:
                pass
        except Exception:
            if not cached:
                print('Brasília, DF · Clima indisponível')
                return
            data = cached['data']
            stale = True
    c, d = data['current'], data['daily']
    icon, label = condition(c['weather_code'], c['is_day'])
    print(f"{icon} Brasília, DF · {c['temperature_2m']:.0f}°C")
    print(f"{label} · Sensação {c['apparent_temperature']:.0f}°C")
    print(f"↓ {d['temperature_2m_min'][0]:.0f}°  ↑ {d['temperature_2m_max'][0]:.0f}° · Umidade {c['relative_humidity_2m']}%")
    print(f"Chuva hoje: {d['precipitation_probability_max'][0]}%")
    if stale:
        print('Sem conexão · última previsão salva')

if __name__ == '__main__':
    main()
