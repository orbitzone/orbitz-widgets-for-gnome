"""Latest fiat references and keyless CoinPaprika crypto USD prices.

This module provides data for an informational converter. Rates are not live
market prices. ``/rate/{base}/{quote}`` returns the provider's latest available
reference rate and date; on weekends or holidays that date can be older than
today. That is the latest provider quote, not an application-selected historical
lookup or a fallback to a locally cached rate.

Crypto uses CoinPaprika Free (personal use, attribution required), bounded
responses and fresh provider timestamps. No price or catalog is saved locally.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import json
import re
from urllib.error import HTTPError, URLError
from http.client import HTTPException
from urllib.request import Request, urlopen


API = 'https://api.frankfurter.dev/v2'
MAX_RESPONSE = 2 * 1024 * 1024
CODE = re.compile(r'^[A-Z]{3}$')
CRYPTO_API = 'https://api.coinpaprika.com/v1'
CRYPTO_SOURCE = 'Powered by CoinPaprika'
ASSET_ID = re.compile(r'^[a-z0-9][a-z0-9-]{0,159}$')
CRYPTO_MAX_AGE = timedelta(hours=1)


class FxError(Exception):
    """A clear, user-safe error from FX data retrieval or validation."""


def _get_json(url, opener=urlopen, *, max_response=MAX_RESPONSE):
    request = Request(url, headers={'Accept': 'application/json', 'User-Agent': 'Orbitz-Widgets/1'})
    try:
        with opener(request, timeout=6) as response:
            raw = response.read(max_response + 1)
    except (HTTPError, URLError, HTTPException, TimeoutError, OSError) as error:
        raise FxError('Cotação indisponível; confira a conexão e tente novamente.') from error
    if len(raw) > max_response:
        raise FxError('Resposta de cotação excedeu o limite permitido.')
    try:
        return json.loads(raw.decode('utf-8'), parse_float=Decimal)
    except (UnicodeDecodeError, ValueError, RecursionError, InvalidOperation) as error:
        raise FxError('A fonte retornou dados de cotação inválidos.') from error


def _crypto_item(data, now):
    """Validate a live ticker; never substitute a saved or historical quote."""
    try:
        asset, symbol, name = data['id'], data['symbol'], data['name']
        if (not isinstance(asset, str) or not ASSET_ID.fullmatch(asset) or
                not isinstance(symbol, str) or not re.fullmatch(r'[A-Za-z0-9.\-]{1,32}', symbol) or
                not isinstance(name, str) or not name.strip() or len(name) > 160 or
                any(ord(char) < 32 for char in name)):
            raise ValueError('identity')
        price = Decimal(str(data['quotes']['USD']['price']))
        updated = datetime.fromisoformat(data['last_updated'].replace('Z', '+00:00'))
        if (not price.is_finite() or not Decimal('1e-30') <= price <= Decimal('1e30') or updated.tzinfo is None or
                now - updated > CRYPTO_MAX_AGE or updated - now > timedelta(minutes=5)):
            raise ValueError('price or timestamp')
    except (KeyError, TypeError, AttributeError, ValueError, InvalidOperation) as error:
        raise FxError('Cotação cripto ausente, inválida ou desatualizada na fonte.') from error
    return {'id': asset, 'symbol': symbol.upper(), 'name': name.strip(),
            'price': price, 'updated_at': updated.astimezone(timezone.utc).isoformat()}


def crypto_currencies(opener=urlopen):
    """Keyless plan's priced assets, rather than unpriced /coins entries.

    CoinPaprika Free is for personal use; attribution is required. No catalog
    or price is persisted, and assets without a fresh USD price are omitted.
    """
    data = _get_json(f'{CRYPTO_API}/tickers?quotes=USD', opener, max_response=8 * 1024 * 1024)
    if not isinstance(data, list) or len(data) > 20000:
        raise FxError('Catálogo cripto inválido.')
    now = datetime.now(timezone.utc)
    result = {}
    for entry in data:
        try:
            item = _crypto_item(entry, now)
        except FxError:
            continue
        result[item['id']] = {key: item[key] for key in ('id', 'symbol', 'name')}
    if not result:
        raise FxError('Catálogo cripto indisponível; nenhum ativo com cotação recente.')
    return {'source': CRYPTO_SOURCE, 'assets': sorted(result.values(), key=lambda item: (item['name'].casefold(), item['id']))}


def crypto_quote(asset='btc-bitcoin', reverse=False, opener=urlopen):
    """Return USD -> asset, or its inverse, from the same validated USD tick."""
    if not isinstance(asset, str) or not ASSET_ID.fullmatch(asset):
        raise ValueError('Identificador cripto inválido.')
    item = _crypto_item(_get_json(f'{CRYPTO_API}/tickers/{asset}?quotes=USD', opener), datetime.now(timezone.utc))
    if item['id'] != asset:
        raise FxError('A fonte retornou outro ativo cripto.')
    return {'base': item['symbol'] if reverse else 'USD',
            'quote': 'USD' if reverse else item['symbol'],
            'rate': item['price'] if reverse else Decimal(1) / item['price'],
            'asset': asset, 'date': item['updated_at'], 'updated_at': item['updated_at'],
            'source': CRYPTO_SOURCE}


def currencies(opener=urlopen):
    """Return the provider's current ISO code -> display name catalog."""
    data = _get_json(f'{API}/currencies', opener)
    if not isinstance(data, list) or len(data) > 1000:
        raise FxError('Catálogo de moedas inválido.')
    result = {}
    for item in data:
        if not isinstance(item, dict):
            raise FxError('Catálogo de moedas inválido.')
        code, name = item.get('iso_code'), item.get('name')
        if not isinstance(code, str) or not CODE.fullmatch(code):
            raise FxError('Código de moeda inválido no catálogo.')
        if not isinstance(name, str) or not name.strip() or len(name) > 160:
            raise FxError('Nome de moeda inválido no catálogo.')
        result[code] = name.strip()
    if not result:
        raise FxError('Catálogo de moedas vazio.')
    return result


def quote(base, quote, opener=urlopen):
    """Fetch and validate the latest provider reference quote for an ISO pair.

    Frankfurter publishes daily reference rates, so the returned rate date may
    precede today on weekends or holidays. No age threshold is imposed.
    """
    if not isinstance(base, str) or not CODE.fullmatch(base):
        raise ValueError('Moeda base deve ser um código ISO de três letras.')
    if not isinstance(quote, str) or not CODE.fullmatch(quote):
        raise ValueError('Moeda de destino deve ser um código ISO de três letras.')
    data = _get_json(f'{API}/rate/{base.lower()}/{quote.lower()}', opener)
    try:
        rate = Decimal(str(data['rate']))
        quoted_on = date.fromisoformat(data['date'])
    except (TypeError, KeyError, ValueError, InvalidOperation) as error:
        raise FxError('A fonte retornou uma cotação incompleta.') from error
    if (not rate.is_finite() or rate <= 0 or not isinstance(data.get('base'), str) or
            not isinstance(data.get('quote'), str) or data['base'].upper() != base or
            data['quote'].upper() != quote):
        raise FxError('A fonte retornou uma cotação inconsistente.')
    if not isinstance(data.get('date'), str) or quoted_on.isoformat() != data['date']:
        raise FxError('A fonte retornou uma data de cotação inválida.')
    if quoted_on > datetime.now(timezone.utc).date():
        raise FxError('A fonte retornou uma data de cotação futura.')
    return {'base': base, 'quote': quote, 'rate': rate, 'date': quoted_on.isoformat(),
            'source': 'Frankfurter · taxas de referência diárias'}


def convert(amount, rate):
    """Multiply a positive user amount by a validated Decimal rate."""
    try:
        amount = Decimal(str(amount))
        rate = Decimal(str(rate))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ValueError('Valor ou cotação inválidos.') from error
    if not amount.is_finite() or amount < 0 or not rate.is_finite() or rate <= 0:
        raise ValueError('Valor ou cotação inválidos.')
    result = amount * rate
    if not result.is_finite():
        raise ValueError('Resultado de conversão inválido.')
    return result
