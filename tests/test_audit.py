"""Safety and resource regression checks; no admin actions or network required."""
import ast
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'widgets'))
import widget_runtime as runtime


def definitions(name):
    path = ROOT / 'widgets' / name
    tree = ast.parse(path.read_text(), str(path))
    # Isolate reusable definitions without executing a widget's sampling loop.
    nodes = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef)):
            nodes.append(node)
        elif isinstance(node, ast.Assign) and all(isinstance(t, ast.Name) and t.id.isupper() for t in node.targets):
            nodes.append(node)
    namespace = {'__file__': str(path), '__name__': 'audit_widget'}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


class RuntimeTests(unittest.TestCase):
    def test_output_limit(self):
        with self.assertRaises(ValueError):
            runtime.run([sys.executable, '-c', "print('x'*10000)"], limit=100)

    def test_timeout_includes_child_pipes(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            runtime.run([sys.executable, '-c', "import subprocess,time; subprocess.Popen(['sleep','10']); time.sleep(10)"], timeout=.1)

    def test_watchdog_survives_parent_exit(self):
        import time
        with tempfile.TemporaryDirectory() as folder:
            sentinel=Path(folder)/'unexpected'
            ready=Path(folder)/'ready'
            child="import time;open("+repr(str(ready))+",'w').close();time.sleep(.6);open("+repr(str(sentinel))+",'w').close()"
            parent="import sys;sys.path.insert(0,"+repr(str(ROOT/'widgets'))+");from widget_runtime import run;run([sys.executable,'-c',"+repr(child)+"],timeout=.2)"
            with subprocess.Popen([sys.executable,'-c',parent],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL) as proc:
                deadline=time.monotonic()+2
                while not ready.exists() and time.monotonic()<deadline:time.sleep(.01)
                self.assertTrue(ready.exists())
                proc.kill();proc.wait()
            time.sleep(.7)
            self.assertFalse(sentinel.exists())

    def test_cache_rejects_symlink_and_nonfinite_time(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, XDG_CACHE_HOME=folder):
            target = Path(folder) / 'target'
            target.write_text(json.dumps({'saved': math.inf, 'data': 'bad'}))
            path = runtime.cache_path('bad.json')
            path.parent.mkdir()
            path.symlink_to(target)
            self.assertIsNone(runtime.load('bad.json'))
            path.unlink()
            path.write_text(target.read_text())
            self.assertIsNone(runtime.load('bad.json'))

    def test_cache_roundtrip_and_invalid_name(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, XDG_CACHE_HOME=folder):
            runtime.save('test.json', {'ok': True})
            self.assertEqual(runtime.load('test.json'), {'ok': True})
            with self.assertRaises(ValueError):
                runtime.cache_path('../escape')
            runtime.save('nan.json', math.nan)
            self.assertFalse(runtime.cache_path('nan.json').exists())

    def test_eof_does_not_execute_and_enter_does(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'executed'
            command = f'touch {target}'
            with patch.object(runtime.subprocess, 'Popen') as launch:
                runtime.launch_terminal('Test', command)
                argv = launch.call_args.args[0]
            self.assertEqual(argv[:4], ['gnome-terminal', '--', 'bash', '-c'])
            subprocess.run(['bash', '-c', argv[4]], input='', text=True, capture_output=True, check=True)
            self.assertFalse(target.exists())
            subprocess.run(['bash', '-c', argv[4]], input='\n\n', text=True, capture_output=True, check=True)
            self.assertTrue(target.exists())


class WidgetTests(unittest.TestCase):
    def test_firewall_cache_structure(self):
        fw = definitions('firewall-widget.py')
        state = fw['empty']()
        self.assertTrue(fw['valid_state'](state))
        for change in [{'sources': {'invalid': {}}}, {'partial': 'yes'}, {'updated': math.nan}, {'totals': {'x': {}}}]:
            self.assertFalse(fw['valid_state']({**state, **change}))

    def test_firewall_persistence_noise_and_expiry(self):
        fw = definitions('firewall-widget.py')
        now = 1760000000
        def event(i, dst='192.168.1.4'):
            return json.dumps({'__CURSOR': str(i), '__REALTIME_TIMESTAMP': str(int((now-i%6*300)*1e6)), 'MESSAGE': f'[UFW BLOCK] SRC=8.8.4.4 DST={dst} PROTO=TCP DPT={20+i%12}'})
        state = fw['empty']()
        fw['ingest'](state, [event(i) for i in range(2501)], now)
        self.assertTrue(fw['valid_state'](state))
        data = fw['payload'](state, now)
        self.assertEqual(data['count'], 2501)
        self.assertEqual(len(data['groups']), 1)
        self.assertEqual(fw['payload'](state, now+90000)['count'], 0)
        noise = fw['empty']()
        fw['ingest'](noise, [event(i, '239.255.255.250') for i in range(100)], now)
        self.assertFalse(fw['payload'](noise, now)['groups'])

    def test_firewall_memory_batch_limit(self):
        fw = definitions('firewall-widget.py')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'log'
            path.write_bytes((b'x'*6000+b'\n')*1000)
            real_popen = subprocess.Popen
            with patch.object(subprocess, 'Popen', side_effect=lambda args, **kw: real_popen(['cat', str(path)], **kw)):
                lines, partial = fw['journal_batch']('')
            self.assertTrue(partial)
            self.assertLessEqual(sum(len(x) for x in lines), 4194304)

    def test_process_startup_path_is_shell_quoted(self):
        module = definitions('processos-widget.py')
        folder = "/tmp/config with 'quotes;$(false)"
        with patch.dict(module['os'].environ, {'XDG_CONFIG_HOME': folder}), patch.dict(module, query=lambda args: ''), patch.object(module['shutil'], 'which', side_effect=lambda name: '/usr/bin/xdg-open' if name == 'xdg-open' else None):
            actions = module['available_actions']()
        import shlex
        self.assertEqual(shlex.split(actions[0]['command']), ['xdg-open', folder + '/autostart'])

    def test_process_query_bounds(self):
        module = definitions('processos-widget.py')
        with patch.dict(module, bounded_run=lambda *a, **k: (_ for _ in ()).throw(ValueError('limit'))):
            self.assertEqual(module['query'](['anything']), '')

    def test_update_unknown_action_and_shared_confirmation(self):
        module = definitions('atualizacoes-widget.py')
        with patch.dict(module, actions=lambda: []):
            with self.assertRaises(ValueError): module['launch']('unknown')
        action = {'id': 'test', 'name': 'Test', 'command': 'true'}
        with patch.dict(module, actions=lambda: [action], launch_terminal=lambda *args: self.assertEqual(args, ('Test','true'))):
            module['launch']('test')

    def test_docker_inspection_caps(self):
        module = definitions('docker-widget.py')
        ids = [f'{i:064x}' for i in range(140)]
        inspected = []
        def run(argv, **kw):
            if argv[1] == 'ps': output = '\n'.join(ids)
            elif argv[1] == 'context': output = 'unix:///var/run/docker.sock'
            else:
                selected = argv[6:]; inspected.extend(selected)
                output = '\n'.join(json.dumps({'name':'/'+x, 'running':True,'ports':{},'mode':'bridge'}) for x in selected)
            return subprocess.CompletedProcess(argv, 0, output, '')
        with patch.dict(module, run=run, read_json=lambda p: {}): data = module['collect'](True)
        self.assertEqual(len(inspected), 100)
        self.assertEqual(len(data['items']), 100)
        self.assertEqual(data['skipped_containers'], 40)
        self.assertIn('140', data['text'])

    def test_docker_url_rejects_unsafe_values(self):
        module = definitions('docker-widget.py')
        for url in ['javascript:alert(1)', 'http://user:pass@localhost:80', 'http://localhost:80\n', 'http://localhost:0']:
            self.assertFalse(module['valid_url'](url))
        self.assertTrue(module['valid_url']('https://localhost:9443'))

    def test_weather_malformed_values(self):
        module = definitions('clima-widget.py')
        for obj in [None, {}, {'current': {'temperature_2m': math.nan}, 'daily': {}}]:
            self.assertFalse(module['valid_weather'](obj))

    def test_storage_rejects_recursive_or_wrong_mounts(self):
        module = definitions('external_storage.py')
        self.assertFalse(module['valid_devices']([{'mountpoints': ['/mnt/test', 42]}]))
        self.assertFalse(module['valid_devices']([], 17))
        self.assertTrue(module['valid_devices']([{'name':'sda', 'mountpoints':['/mnt/test']}]))

    def test_sensor_missing_readings_are_not_exported(self):
        module = definitions('temperaturas-widget.py')
        data = {'applesmc-isa': {'TG0D': {'temp1_input': 60}, 'bad': {'temp2_input': -127}, 'missing': {'temp3_input': None}}}
        def run(*args, **kwargs):return subprocess.CompletedProcess(args,0,json.dumps(data),'')
        with patch.dict(module, run=run), patch.object(Path,'glob',return_value=[]), patch('shutil.which',return_value=None):
            result=module['details']()
        self.assertEqual(len(result['items']),1)
        self.assertEqual(result['items'][0]['value'],60)

    def test_network_handles_truncated_routes_and_rates(self):
        module = definitions('rede-widget.py')
        with patch.object(Path,'read_text',side_effect=['header\ninvalid\n','']):
            self.assertIsNone(module['interface']())
        self.assertEqual(module['rate'](-1),'0.0 B/s')
        self.assertEqual(module['rate'](1024),'1.0 KiB/s')

    def test_sensor_known_and_unknown_descriptions(self):
        module = definitions('temperaturas-widget.py')
        self.assertIn('GPU', module['describe']('applesmc-isa', 'TG0D'))
        self.assertIn('não identificados', module['describe']('applesmc-isa', 'UNKNOWN'))


if __name__ == '__main__':
    unittest.main()
