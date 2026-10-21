#!/usr/bin/python3
"""Text/JSON adapter for the existing Orbitz fiat and crypto converter."""

import argparse
import json
from decimal import Decimal, ROUND_HALF_UP, localcontext

from fx_rates import FxError, currencies, quote, crypto_currencies, crypto_quote


def render_quote(item):
    rate = Decimal(str(item['rate']))
    if 'asset' in item and item['quote'] != 'USD':
        # Display only the supplied rate's digits, without rounding small
        # crypto amounts to zero or padding them with invented precision.
        value = format(rate, 'f')
        if '.' in value:
            value = value.rstrip('0').rstrip('.')
        whole, separator, fraction = value.partition('.')
        value = format(int(whole), ',').replace(',', '.') + (',' + fraction if separator else '')
        return f"1 {item['base']} → {value} {item['quote']}"
    # Quantizing needs room for all integer digits, cents and a rounding carry.
    # Crypto rates can legitimately reach 1e30 in the accepted provider domain.
    with localcontext() as context:
        context.prec = max(context.prec, rate.adjusted() + 4)
        value = format(rate.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), ',.2f')
    value = value.translate(str.maketrans({',': '.', '.': ','}))
    return f"1 {item['base']} → {value} {item['quote']}"


def main(argv=None, *, quote_provider=quote, catalog_provider=currencies,
         crypto_quote_provider=crypto_quote, crypto_catalog_provider=crypto_currencies, output=print):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--catalog-json', action='store_true')
    parser.add_argument('--quote-json', action='store_true')
    parser.add_argument('--mode', choices=('fiat', 'crypto'), default='fiat')
    parser.add_argument('--asset', default='btc-bitcoin')
    parser.add_argument('--quote', default='USD')
    parser.add_argument('--reverse', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.catalog_json:
            output(json.dumps(crypto_catalog_provider() if args.mode == 'crypto' else catalog_provider(), ensure_ascii=False))
            return 0
        if args.mode == 'crypto':
            item = crypto_quote_provider(args.asset, args.reverse)
        else:
            if len(args.quote) != 3 or not args.quote.isalpha() or not args.quote.isascii():
                raise ValueError('Código de moeda inválido.')
            source, target = (args.quote.upper(), 'BRL') if args.reverse else ('BRL', args.quote.upper())
            item = quote_provider(source, target)
        output(json.dumps({**item, 'rate': str(item['rate'])}, ensure_ascii=False) if args.quote_json else render_quote(item))
        return 0
    except (FxError, ValueError) as error:
        output(json.dumps({'error': str(error)}, ensure_ascii=False) if args.quote_json or args.catalog_json else f'Cotação indisponível · {error}')
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
