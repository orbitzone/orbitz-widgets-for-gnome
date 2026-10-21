import json
import importlib.util
import sys
import unittest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'widgets'))
import fx_rates
WIDGET_SPEC = importlib.util.spec_from_file_location('currency_widget', Path(__file__).resolve().parents[1] / 'widgets' / 'currency-widget.py')
currency_widget = importlib.util.module_from_spec(WIDGET_SPEC)
WIDGET_SPEC.loader.exec_module(currency_widget)


class Response:
    def __init__(self, data):
        self.data = json.dumps(data).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, limit):
        return self.data[:limit]


def opener_for(data):
    opener = Mock(return_value=Response(data))
    return opener


class FxRatesTests(unittest.TestCase):
    def test_currency_catalog_uses_supported_codes_and_names(self):
        opener = opener_for([{'iso_code': 'USD', 'name': 'US Dollar'},
                             {'iso_code': 'BRL', 'name': 'Brazilian Real'}])
        self.assertEqual(fx_rates.currencies(opener), {'USD': 'US Dollar', 'BRL': 'Brazilian Real'})
        request = opener.call_args.args[0]
        self.assertEqual(request.full_url, fx_rates.API + '/currencies')

    def test_quote_uses_latest_rate_endpoint_and_dates_the_reference(self):
        today = datetime.now(timezone.utc).date().isoformat()
        opener = opener_for({'date': today, 'base': 'BRL', 'quote': 'USD', 'rate': 0.2})
        item = fx_rates.quote('BRL', 'USD', opener)
        self.assertEqual(item['rate'], Decimal('0.2'))
        self.assertEqual(item['date'], today)
        self.assertEqual(item['source'], 'Frankfurter · taxas de referência diárias')
        self.assertEqual(opener.call_args.args[0].full_url, fx_rates.API + '/rate/brl/usd')

    def test_quote_accepts_latest_provider_date_older_than_today(self):
        # Daily references are not published every calendar day. A weekend or
        # holiday response can legitimately contain the provider's prior date.
        latest_available = datetime.now(timezone.utc).date() - timedelta(days=4)
        opener = opener_for({'date': latest_available.isoformat(), 'base': 'BRL',
                             'quote': 'USD', 'rate': 0.2})
        item = fx_rates.quote('BRL', 'USD', opener)
        self.assertEqual(item['date'], latest_available.isoformat())
        self.assertEqual(opener.call_args.args[0].full_url, fx_rates.API + '/rate/brl/usd')

    def test_quote_compares_provider_date_to_utc_day_not_local_day(self):
        utc_day = date(2026, 10, 20)
        opener = opener_for({'date': utc_day.isoformat(), 'base': 'BRL', 'quote': 'USD', 'rate': 0.2})
        with patch.object(fx_rates, 'datetime') as mocked_datetime:
            mocked_datetime.now.return_value.date.return_value = utc_day
            item = fx_rates.quote('BRL', 'USD', opener)
        self.assertEqual(item['date'], utc_day.isoformat())

    def test_rejects_noncanonical_date_and_network_read_failure(self):
        with self.assertRaises(fx_rates.FxError):
            fx_rates.quote('BRL', 'USD', opener_for({'date': '20261020', 'base': 'BRL', 'quote': 'USD', 'rate': 0.2}))
        opener = Mock(side_effect=OSError('offline'))
        with self.assertRaises(fx_rates.FxError):
            fx_rates.currencies(opener)

    def test_conversion_uses_decimal_without_binary_float_rounding(self):
        self.assertEqual(fx_rates.convert('10.25', Decimal('0.2')), Decimal('2.050'))

    def test_rejects_invalid_codes_rate_future_date_and_bad_catalog(self):
        with self.assertRaises(ValueError):
            fx_rates.quote('BRL&x=1', 'USD', opener_for({}))
        for payload in (
            {'date': datetime.now(timezone.utc).date().isoformat(), 'base': 'BRL', 'quote': 'USD', 'rate': 0},
            {'date': (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat(),
             'base': 'BRL', 'quote': 'USD', 'rate': 1},
        ):
            with self.subTest(payload=payload), self.assertRaises(fx_rates.FxError):
                fx_rates.quote('BRL', 'USD', opener_for(payload))
        with self.assertRaises(fx_rates.FxError):
            fx_rates.currencies(opener_for([{'iso_code': 'bad', 'name': 'Bad'}]))

    def test_rejects_negative_and_non_finite_conversion(self):
        for amount in (-1, 'NaN', 'Infinity'):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                fx_rates.convert(amount, '0.5')

    def test_widget_displays_only_the_conversion_in_forward_and_reverse_modes(self):
        output = []
        calls = []
        def provider(base, target):
            calls.append((base, target))
            rate = Decimal('0.19829') if (base, target) == ('BRL', 'USD') else Decimal('5.0435')
            return {'base': base, 'quote': target, 'rate': rate, 'date': '2026-10-20',
                    'source': 'Frankfurter · taxas de referência diárias'}
        result = currency_widget.main(['--quote', 'USD'], quote_provider=provider, output=output.append)
        self.assertEqual(result, 0)
        self.assertEqual(calls, [('BRL', 'USD')])
        self.assertEqual(output, ['1 BRL → 0,20 USD'])

        output.clear()
        result = currency_widget.main(['--quote', 'USD', '--reverse'], quote_provider=provider, output=output.append)
        self.assertEqual(result, 0)
        self.assertEqual(calls, [('BRL', 'USD'), ('USD', 'BRL')])
        self.assertEqual(output, ['1 USD → 5,04 BRL'])

    def test_widget_rounds_to_cents_including_small_rates(self):
        self.assertEqual(currency_widget.render_quote({'base': 'BRL', 'quote': 'USD',
                                                        'rate': Decimal('0.005')}),
                         '1 BRL → 0,01 USD')
        self.assertEqual(currency_widget.render_quote({'base': 'BRL', 'quote': 'BTC',
                                                        'rate': Decimal('0.0049')}),
                         '1 BRL → 0,00 BTC')

    def test_rounding_examples_and_half_up(self):
        for raw, expected in [('5.04', '5,04'), ('83060.16777893', '83.060,17'), ('5.5', '5,50'), ('0.5', '0,50'), ('1.005', '1,01'), ('999.999', '1.000,00')]:
            for extra in ({}, {'asset': 'btc-bitcoin'}):
                self.assertEqual(currency_widget.render_quote(dict(base='BTC', quote='USD', rate=Decimal(raw), **extra)),
                                 f'1 BTC → {expected} USD')

    def test_widget_keeps_readable_error_when_quote_is_unavailable(self):
        output = []
        result = currency_widget.main(['--quote', 'USD'],
                                      quote_provider=lambda *_args: (_ for _ in ()).throw(fx_rates.FxError('sem conexão')),
                                      output=output.append)
        self.assertEqual(result, 0)
        self.assertEqual(output, ['Cotação indisponível · sem conexão'])

    def test_catalog_mode_outputs_json_without_quote_call(self):
        output = []
        currency_widget.main(['--catalog-json'], catalog_provider=lambda: {'USD': 'US Dollar'}, output=output.append)
        self.assertEqual(json.loads(output[0]), {'USD': 'US Dollar'})


class CryptoRatesTests(unittest.TestCase):
    def ticker(self, **overrides):
        return {'id': 'btc-bitcoin', 'symbol': 'BTC', 'name': 'Bitcoin',
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'quotes': {'USD': {'price': '100000.125'}}, **overrides}

    def test_usd_pair_both_directions_and_provider_identity(self):
        opener = opener_for(self.ticker())
        forward = fx_rates.crypto_quote(opener=opener)
        self.assertEqual((forward['base'], forward['quote']), ('USD', 'BTC'))
        self.assertEqual(forward['rate'], Decimal(1) / Decimal('100000.125'))
        self.assertEqual(forward['source'], 'Powered by CoinPaprika')
        self.assertEqual(opener.call_args.args[0].full_url,
                         fx_rates.CRYPTO_API + '/tickers/btc-bitcoin?quotes=USD')
        reverse = fx_rates.crypto_quote(reverse=True, opener=opener)
        self.assertEqual((reverse['base'], reverse['quote'], reverse['rate']),
                         ('BTC', 'USD', Decimal('100000.125')))
        self.assertEqual(forward['updated_at'], reverse['updated_at'])

    def test_catalog_exposes_unique_ids_and_omits_unpriced_or_old_assets(self):
        opener = opener_for([self.ticker(), self.ticker(id='another-bitcoin'),
                             self.ticker(id='old-coin', last_updated=(datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()),
                             self.ticker(id='missing-coin', quotes={}), None])
        catalog = fx_rates.crypto_currencies(opener)
        self.assertEqual({item['id'] for item in catalog['assets']}, {'btc-bitcoin', 'another-bitcoin'})
        self.assertEqual(catalog['source'], fx_rates.CRYPTO_SOURCE)
        self.assertEqual(opener.call_args.args[0].full_url, fx_rates.CRYPTO_API + '/tickers?quotes=USD')

    def test_rejects_stale_future_naive_dates_mismatches_bad_prices(self):
        now = datetime.now(timezone.utc)
        bad = [self.ticker(last_updated=(now - timedelta(hours=2)).isoformat()),
               self.ticker(last_updated=(now + timedelta(hours=1)).isoformat()),
               self.ticker(last_updated='2026-10-21T00:00:00'),
               self.ticker(last_updated=None), self.ticker(id='eth-ethereum'), [], None,
               self.ticker(symbol='bad\nlabel')]
        bad += [self.ticker(quotes={'USD': {'price': price}}) for price in
                ('NaN', 'Infinity', 0, -1, None, '1e999999', '1e-99999')]
        for item in bad:
            with self.subTest(item=item), self.assertRaises(fx_rates.FxError):
                fx_rates.crypto_quote(opener=opener_for(item))

    def test_invalid_asset_never_calls_network(self):
        opener = Mock()
        for asset in ('../../secret', 'BTC;echo', 'btc?quote=EUR', '', None):
            with self.subTest(asset=asset), self.assertRaises(ValueError):
                fx_rates.crypto_quote(asset, opener=opener)
        opener.assert_not_called()

    def test_network_throttle_invalid_json_and_size_errors_without_retry(self):
        for failure in (OSError('offline'), HTTPError('url', 429, 'limit', {}, None)):
            opener = Mock(side_effect=failure)
            with self.assertRaises(fx_rates.FxError):
                fx_rates.crypto_quote(opener=opener)
            self.assertEqual(opener.call_count, 1)
        for raw in (b'bad json', b'x' * (fx_rates.MAX_RESPONSE + 1)):
            response = Response({})
            response.data = raw
            with self.assertRaises(fx_rates.FxError):
                fx_rates.crypto_quote(opener=Mock(return_value=response))
        with self.assertRaises(fx_rates.FxError):
            fx_rates.crypto_currencies(opener_for([]))

    def test_impossible_json_exponent_returns_sanitized_cli_error(self):
        response = Response({})
        response.data = b'{"rate":1e999999999999999999999}'
        opener = Mock(return_value=response)
        with self.assertRaisesRegex(fx_rates.FxError, '^A fonte retornou dados de cotação inválidos\\.$'):
            fx_rates.quote('BRL', 'USD', opener)
        output = []
        result = currency_widget.main(
            ['--quote', 'USD', '--quote-json'],
            quote_provider=lambda base, target: fx_rates.quote(base, target, opener),
            output=output.append)
        self.assertEqual(result, 0)
        self.assertEqual(len(output), 1)
        self.assertEqual(json.loads(output[0]), {'error': 'A fonte retornou dados de cotação inválidos.'})

    def test_oversized_json_integer_returns_sanitized_cli_error(self):
        response = Response({})
        response.data = b'{"rate":' + b'9' * 5000 + b'}'
        opener = Mock(return_value=response)
        output = []
        # Pin the interpreter limit so this exercises the parser ValueError
        # even when the test runner was started with a different setting.
        previous_limit = sys.get_int_max_str_digits()
        try:
            sys.set_int_max_str_digits(4300)
            result = currency_widget.main(
                ['--quote', 'USD', '--quote-json'],
                quote_provider=lambda base, target: fx_rates.quote(base, target, opener),
                output=output.append)
        finally:
            sys.set_int_max_str_digits(previous_limit)
        self.assertEqual(result, 0)
        self.assertEqual(len(output), 1)
        self.assertEqual(json.loads(output[0]), {'error': 'A fonte retornou dados de cotação inválidos.'})
        self.assertNotIn('4300', output[0])
        self.assertNotIn('5000', output[0])
        self.assertNotIn('9999', output[0])

    def test_deep_json_within_byte_limit_returns_safe_cli_error(self):
        response = Response({})
        response.data = b'[' * 1100 + b'0' + b']' * 1100
        self.assertLess(len(response.data), fx_rates.MAX_RESPONSE)
        opener = Mock(return_value=response)
        with self.assertRaisesRegex(fx_rates.FxError, 'dados de cotação inválidos'):
            fx_rates.crypto_quote(opener=opener)
        output = []
        result = currency_widget.main(
            ['--mode', 'crypto', '--quote-json'],
            crypto_quote_provider=lambda asset, reverse: fx_rates.crypto_quote(asset, reverse, opener),
            output=output.append)
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output[0]), {'error': 'A fonte retornou dados de cotação inválidos.'})

    def test_text_cli_formats_both_extreme_prices_in_both_directions(self):
        from decimal import getcontext
        precision = getcontext().prec
        large = '1.000.000.000.000.000.000.000.000.000.000,00'
        for price in ('1e30', '1e-30'):
            for reverse in (False, True):
                with self.subTest(price=price, reverse=reverse):
                    opener = opener_for(self.ticker(quotes={'USD': {'price': price}}))
                    output = []
                    argv = ['--mode', 'crypto'] + (['--reverse'] if reverse else [])
                    result = currency_widget.main(
                        argv, crypto_quote_provider=lambda asset, rev: fx_rates.crypto_quote(asset, rev, opener),
                        output=output.append)
                    high_rate = (price == '1e30') == reverse
                    if reverse:
                        value = large if high_rate else '0,00'
                    else:
                        value = large.removesuffix(',00') if high_rate else '0,' + '0' * 29 + '1'
                    base, target = ('BTC', 'USD') if reverse else ('USD', 'BTC')
                    self.assertEqual(result, 0)
                    self.assertEqual(output, [f'1 {base} → {value} {target}'])
                    self.assertEqual(getcontext().prec, precision)

    def test_crypto_cli_catalog_json_errors_precision_and_direction(self):
        calls, output = [], []
        def provider(asset, reverse):
            calls.append((asset, reverse))
            return fx_rates.crypto_quote(asset, reverse, opener_for(self.ticker()))
        currency_widget.main(['--mode', 'crypto'], crypto_quote_provider=provider, output=output.append)
        self.assertEqual(calls, [('btc-bitcoin', False)])
        self.assertEqual(output[-1], '1 USD → 0,000009999987500015624980468774414 BTC')
        currency_widget.main(['--mode', 'crypto', '--reverse', '--quote-json'],
                             crypto_quote_provider=provider, output=output.append)
        item = json.loads(output[-1])
        self.assertEqual(item['rate'], '100000.125')
        self.assertEqual(item['base'], 'BTC')
        self.assertIn('updated_at', item)
        currency_widget.main(['--mode', 'crypto', '--catalog-json'],
                             crypto_catalog_provider=lambda: {'assets': []}, output=output.append)
        self.assertEqual(json.loads(output[-1]), {'assets': []})
        currency_widget.main(['--mode', 'crypto', '--quote-json'],
                             crypto_quote_provider=Mock(side_effect=fx_rates.FxError('offline')), output=output.append)
        self.assertEqual(json.loads(output[-1]), {'error': 'offline'})
        self.assertEqual('1 USD → 0,' + '0' * 24 + '1 TINY', currency_widget.render_quote({'asset': 'tiny', 'base': 'USD', 'quote': 'TINY', 'rate': Decimal('1e-25')}))

    def test_crypto_destination_preserves_supplied_digits_without_context_change(self):
        from decimal import getcontext
        precision = getcontext().prec
        for rate, expected in [('0.000016273845678', '0,000016273845678'),
                               ('1E-30', '0,' + '0' * 29 + '1'),
                               ('0.00001000', '0,00001'), ('1000.00', '1.000')]:
            output = []
            currency_widget.main(['--mode', 'crypto'],
                                 crypto_quote_provider=lambda *_: dict(asset='btc-bitcoin', base='USD', quote='BTC', rate=Decimal(rate)),
                                 output=output.append)
            self.assertEqual(output, [f'1 USD → {expected} BTC'])
            self.assertEqual(getcontext().prec, precision)
        output = []
        currency_widget.main(['--mode', 'crypto', '--reverse'],
                             crypto_quote_provider=lambda *_: dict(asset='btc-bitcoin', base='BTC', quote='USD', rate=Decimal('83060.16777893')),
                             output=output.append)
        self.assertEqual(output, ['1 BTC → 83.060,17 USD'])
        self.assertEqual(getcontext().prec, precision)


if __name__ == '__main__':
    unittest.main()
