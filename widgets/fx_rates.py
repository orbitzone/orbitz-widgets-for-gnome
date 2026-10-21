"""Latest available daily reference FX rates from Frankfurter's public v2 API.

This module provides data for an informational converter. Rates are not live
market prices. ``/rate/{base}/{quote}`` returns the provider's latest available
reference rate and date; on weekends or holidays that date can be older than
today. That is the latest provider quote, not an application-selected historical
lookup or a fallback to a locally cached rate.
"""

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import re
from urllib.error import HTTPError, URLError
from http.client import HTTPException
from urllib.request import Request, urlopen


API = 'https://api.frankfurter.dev/v2'
MAX_RESPONSE = 2 * 1024 * 1024
CODE = re.compile(r'^[A-Z]{3}$')


class FxError(Exception):
    """A clear, user-safe error from FX data retrieval or validation."""


def _get_json(url, opener=urlopen):
    request = Request(url, headers={'Accept': 'application/json', 'User-Agent': 'Orbitz-Widgets/1'})
    try:
        with opener(request, timeout=6) as response:
            raw = response.read(MAX_RESPONSE + 1)
    except (HTTPError, URLError, HTTPException, TimeoutError, OSError) as error:
        raise FxError('Cotação indisponível; confira a conexão e tente novamente.') from error
    if len(raw) > MAX_RESPONSE:
        raise FxError('Resposta de cotação excedeu o limite permitido.')
    try:
        return json.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FxError('A fonte retornou dados de cotação inválidos.') from error


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
