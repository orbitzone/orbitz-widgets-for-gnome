#!/usr/bin/python3
"""Text renderer used by the Orbitz fiat-currency converter element."""

import argparse
import json
from decimal import Decimal, ROUND_DOWN

from fx_rates import FxError, currencies, quote


def render_quote(item):
    value = format(Decimal(str(item['rate'])).quantize(Decimal('0.01'), rounding=ROUND_DOWN), '.2f')
    return f"1 {item['base']} → {value} {item['quote']}"


def main(argv=None, *, quote_provider=quote, catalog_provider=currencies, output=print):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--catalog-json', action='store_true')
    parser.add_argument('--quote', default='USD')
    parser.add_argument('--reverse', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.catalog_json:
            output(json.dumps(catalog_provider(), ensure_ascii=False))
            return 0
        if len(args.quote) != 3 or not args.quote.isalpha() or not args.quote.isascii():
            raise ValueError('Código de moeda inválido.')
        source, target = (args.quote.upper(), 'BRL') if args.reverse else ('BRL', args.quote.upper())
        item = quote_provider(source, target)
        output(render_quote(item))
        return 0
    except (FxError, ValueError) as error:
        output(f'Cotação indisponível · {error}')
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
