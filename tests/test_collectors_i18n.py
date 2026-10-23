"""Presentation locale boundaries; no network or installed settings are used."""
import importlib.util
import ast
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'widgets'))
import orbitz_i18n as i18n
import fx_rates
import widget_runtime


def module(name):
    spec = importlib.util.spec_from_file_location('localized_' + name.replace('-', '_'), ROOT / 'widgets' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class CollectorLocaleTests(unittest.TestCase):
    def test_every_widget_message_id_exists_in_both_canonical_catalogs(self):
        keys = set()
        for path in (ROOT / 'widgets').glob('*.py'):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.startswith('widgets.'):
                    keys.add(node.value)
        for language in ('pt-BR', 'en-US'):
            catalog = json.loads((ROOT / 'i18n' / (language + '.json')).read_text())
            self.assertFalse(keys - catalog.keys(), (language, keys - catalog.keys()))

    def test_normalization_and_default_ignore_system_language(self):
        for value in (None, '', 'fr-FR', 'en', 'pt_BR', '../en-US'):
            self.assertEqual(i18n.normalize_locale(value), 'pt-BR')
        for value in ('en-US', 'en_US', 'EN-us'):
            self.assertEqual(i18n.normalize_locale(value), 'en-US')
        with patch.dict(os.environ, {'LANG': 'en_US.UTF-8'}, clear=True):
            self.assertEqual(i18n.locale(), 'pt-BR')

    def test_catalog_switch_fallback_interpolation_and_external_name(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            (path / 'pt-BR.json').write_text(json.dumps({'example': 'Serviço {name}', 'pt_only': 'Somente português'}))
            (path / 'en-US.json').write_text(json.dumps({'example': 'Service {name}'}))
            with patch.dict(os.environ, {'ORBITZ_I18N_DIR': folder, 'ORBITZ_LOCALE': 'pt-BR'}):
                self.assertEqual(i18n.t('example', name='pt_only'), 'Serviço pt_only')
                os.environ['ORBITZ_LOCALE'] = 'en-US'
                self.assertEqual(i18n.t('example', name='pt_only'), 'Service pt_only')
                self.assertEqual(i18n.t('pt_only'), 'Somente português')
                (path / 'en-US.json').write_text('{broken')
                self.assertEqual(i18n.t('example', name='A'), 'Serviço A')
                self.assertEqual(i18n.tr('unknown', fallback='Texto seguro'), 'Texto seguro')

    def test_service_payload_preserves_scope_names_descriptions_and_shape(self):
        services = module('servicos-widget')
        def query(args, **kwargs):
            text = 'custom.service loaded failed failed Serviços: OK\n'
            if 'show' in args:
                text = 'Id=custom.service\nResult=exit-code\nExecMainStatus=1\nStateChangeTimestamp=source-date\n'
            return subprocess.CompletedProcess(args, 0, text)
        with patch.object(services, 'run', side_effect=query):
            with patch.dict(os.environ, {'ORBITZ_LOCALE': 'pt-BR'}):
                portuguese = services.collect(True)
            with patch.dict(os.environ, {'ORBITZ_LOCALE': 'en-US'}):
                english = services.collect(True)
        self.assertEqual(set(portuguese), set(english))
        self.assertEqual(english['text'], 'Services: 2 failed')
        self.assertEqual([g['scope'] for g in english['groups']], ['system', 'user'])
        self.assertEqual(english['groups'][0]['items'], portuguese['groups'][0]['items'])
        self.assertEqual(english['groups'][0]['items'][0]['description'], 'Serviços: OK')

    def test_fx_error_json_changes_only_display_text(self):
        currency = module('currency-widget')
        with patch.dict(os.environ, {'ORBITZ_LOCALE': 'en-US'}):
            output = []
            result = currency.main(['--quote-json'], output=output.append,
                                   quote_provider=lambda *_: fx_rates.quote('invalid', 'USD'))
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output[0]), {'error': 'Base currency must be a three-letter ISO code.'})

    def test_updates_locale_preserves_state_markers_custom_names_and_commands(self):
        updates = module('atualizacoes-widget')
        custom = {'name': 'Buscar atualizações', 'command': 'printf custom'}
        with patch.dict(os.environ, {'ORBITZ_LOCALE': 'en-US'}), patch.object(updates, 'read_json', return_value=[custom]), patch.object(updates.shutil, 'which', return_value=None):
            actions = updates.actions()
            unavailable = updates.query('APT')
        self.assertEqual(actions[-1], {'id': 'custom-0', **custom})
        self.assertEqual(actions[0]['id'], 'buscar')
        self.assertEqual(actions[0]['name'], 'Check for updates')
        self.assertEqual(actions[0]['command'], 'sudo apt update && snap refresh --list && flatpak update --appstream')
        self.assertEqual(unavailable, {'source':'APT', 'items':[], 'state':'Não instalado'})

    def test_english_terminal_confirmation_preserves_literal_command_and_eof(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'confirmed'
            command = 'touch ' + shlex.quote(str(target))
            with patch.dict(os.environ, {'ORBITZ_LOCALE': 'en-US'}), patch.object(widget_runtime, 'launch_terminal_command') as launch:
                widget_runtime.launch_terminal('Custom name $value', command)
            script = launch.call_args.args[0][2]
            self.assertIn('Enter to execute', script)
            subprocess.run(['bash', '-c', script], input='', text=True, capture_output=True, check=True)
            self.assertFalse(target.exists())
            subprocess.run(['bash', '-c', script], input='\n\n', text=True, capture_output=True, check=True)
            self.assertTrue(target.exists())

    def test_weather_city_and_protocol_constants_remain_unchanged(self):
        weather = module('clima-widget')
        with patch.dict(os.environ, {'ORBITZ_LOCALE': 'en-US'}):
            self.assertEqual(weather.condition(0, True), ('☀️', 'Clear sky'))
        # WX-01 resolves arbitrary locations with the provider, while the
        # original Brasília coordinates/timezone remain the preference default.
        self.assertEqual(weather.PARAMS['timezone'], 'auto')
        self.assertEqual(weather.PARAMS['forecast_days'], 7)
        self.assertEqual(weather.DEFAULT_LOCATION['latitude'], -15.7939)
        self.assertEqual(weather.DEFAULT_LOCATION['name'], 'Brasília, DF')
        self.assertEqual(weather.locations.DEFAULT['location']['timezone'], 'America/Sao_Paulo')

    def test_sensor_and_pressure_labels_follow_locale_without_changing_resource_ids(self):
        sensors = module('temperaturas-widget')
        import pressure_metrics
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for resource in ('cpu', 'memory', 'io'):
                (root / resource).write_text('some avg10=0.00 avg60=0.00 avg300=0.00 total=100\n')
            with patch.dict(os.environ, {'ORBITZ_LOCALE': 'pt-BR'}):
                before = pressure_metrics.snapshot(root)
                description = sensors.describe('applesmc', 'TA0V')
            with patch.dict(os.environ, {'ORBITZ_LOCALE': 'en-US'}):
                after = pressure_metrics.snapshot(root)
                self.assertEqual(sensors.describe('applesmc', 'TA0V'), 'Estimated ambient temperature near the equipment.')
        self.assertEqual(description, 'Estimativa da temperatura ambiente próxima ao equipamento.')
        self.assertEqual([item['resource'] for item in before['items']], [item['resource'] for item in after['items']])
        self.assertEqual([item['name'] for item in after['items']], ['CPU', 'Memory', 'Disk / I/O'])
        self.assertEqual(after['text'], 'No significant pressure')
