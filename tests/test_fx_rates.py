import json
import importlib.util
import sys
import unittest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch

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
        self.assertEqual(output, ['1 BRL → 0.19 USD'])

        output.clear()
        result = currency_widget.main(['--quote', 'USD', '--reverse'], quote_provider=provider, output=output.append)
        self.assertEqual(result, 0)
        self.assertEqual(calls, [('BRL', 'USD'), ('USD', 'BRL')])
        self.assertEqual(output, ['1 USD → 5.04 BRL'])

    def test_widget_truncates_to_two_places_including_small_rates(self):
        self.assertEqual(currency_widget.render_quote({'base': 'BRL', 'quote': 'USD',
                                                        'rate': Decimal('0.005')}),
                         '1 BRL → 0.00 USD')
        self.assertEqual(currency_widget.render_quote({'base': 'BRL', 'quote': 'BTC',
                                                        'rate': Decimal('0.0049')}),
                         '1 BRL → 0.00 BTC')

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


if __name__ == '__main__':
    unittest.main()
