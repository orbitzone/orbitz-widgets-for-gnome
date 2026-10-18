"""Import and output contracts of collectors executed by the metrics worker."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from xml.etree import ElementTree
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'widgets'))


def module(filename):
    spec = importlib.util.spec_from_file_location('entrypoint_' + filename.replace('-','_'), ROOT/'widgets'/filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class CollectorEntrypoints(unittest.TestCase):
    def test_import_does_not_collect_sleep_spawn_or_print(self):
        for filename in ['cpu-ram-widget.py','processos-widget.py','rede-widget.py','seguranca-widget.py','temperaturas-widget.py']:
            with self.subTest(filename=filename), io.StringIO() as output, contextlib.redirect_stdout(output), patch('time.sleep', side_effect=AssertionError('sampling on import')), patch.object(Path, 'read_text', side_effect=AssertionError('read on import')), patch.object(subprocess, 'Popen', side_effect=AssertionError('spawn on import')):
                self.assertTrue(callable(module(filename).main))
                self.assertEqual(output.getvalue(), '')

    def test_cpu_detail_subprocess_routes_preserve_arguments(self):
        # Sibling helper fixtures exercise actual CLI routing without system reads.
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            (directory/'cpu-ram-widget.py').write_text((ROOT/'widgets/cpu-ram-widget.py').read_text())
            (directory/'widget_runtime.py').write_text('def load(*args): raise AssertionError("sampling")\ndef save(*args): raise AssertionError("sampling")\n')
            (directory/'external_storage.py').write_text('def external_usage(): raise AssertionError("sampling")\n')
            for filename, prefix in [('hardware-details.py','AZCLOCK_HARDWARE:'), ('armazenamento-widget.py','AZCLOCK_STORAGE:')]:
                (directory/filename).write_text('import json,sys\nassert __name__ == "__main__"\nprint(' + repr(prefix) + ' + json.dumps({"args":sys.argv[1:]}))\n')
            for arguments, prefix in [(['--hardware','cpu'],'AZCLOCK_HARDWARE:'), (['--hardware','ram'],'AZCLOCK_HARDWARE:'), (['--details'],'AZCLOCK_STORAGE:'), (['--details','--external','--device','sda','--identity','synthetic'],'AZCLOCK_STORAGE:')]:
                with self.subTest(arguments=arguments):
                    result = subprocess.run([sys.executable,str(directory/'cpu-ram-widget.py'),*arguments], capture_output=True,text=True,timeout=5)
                    self.assertEqual(result.returncode,0,result.stderr)
                    self.assertTrue(result.stdout.startswith(prefix),result.stdout)
                    self.assertEqual(json.loads(result.stdout[len(prefix):]), {'args':arguments})

    def test_cpu_eject_routes_identity_without_sampling(self):
        collector = module('cpu-ram-widget.py')
        with io.StringIO() as output, contextlib.redirect_stdout(output), patch.object(sys,'argv',['cpu-ram-widget.py','--eject','--device','sda','--identity','synthetic']), patch.object(collector,'cpu',side_effect=AssertionError('sampling')), patch('external_storage.eject_device', return_value={'ok':True}) as eject:
            collector.main()
            eject.assert_called_once_with('sda','synthetic')
            self.assertEqual(output.getvalue(),'AZCLOCK_EJECT:{"ok": true}\n')

    def test_cpu_historical_eight_cell_bar_rounding_and_limits(self):
        collector = module('cpu-ram-widget.py')
        for percent, filled in [(-100,0),(0,0),(6.24,0),(6.25,1),(12.5,1),(50,4),(93.74,7),(93.75,8),(100,8),(150,8)]:
            with self.subTest(percent=percent):
                value = collector.bar(percent)
                self.assertEqual(value, '█'*filled + '░'*(8-filled))

    def test_cpu_compact_markup_columns_and_aggregate_external(self):
        collector = module('cpu-ram-widget.py')
        with io.StringIO() as output, contextlib.redirect_stdout(output), patch.object(sys,'argv',['cpu-ram-widget.py']), patch.object(collector,'cpu',side_effect=[(100,50),(200,50)]), patch.object(collector.time,'sleep'), patch.object(Path,'read_text',return_value='MemTotal: 1000 kB\nMemAvailable: 1000 kB\n'), patch.object(collector,'load',return_value=50), patch.object(collector,'external_usage',return_value=25):
            collector.main()
            span = ElementTree.fromstring(output.getvalue())
        self.assertEqual(span.attrib, {'font_family':'monospace','size':'7680','line_height':'1.5'})
        rows = span.text.split('\n')
        self.assertEqual(len(rows),4)
        self.assertEqual([row[2:6].strip() for row in rows], ['CPU','RAM','SSD','EXT'])
        self.assertEqual([row[19:] for row in rows], ['100%','  0%',' 50%',' 25%'])
        for row in rows:
            self.assertEqual(len(row),23)
            self.assertEqual(row[:2],'  ')
            self.assertEqual(row[6:9],'   ')
            self.assertEqual(row[17:19],'  ')
            self.assertEqual(len(row[9:17]),8)
            self.assertTrue(set(row[9:17]) <= {'█','░'})

    def test_network_rate_and_details_prefix(self):
        network = module('rede-widget.py')
        with io.StringIO() as output, contextlib.redirect_stdout(output), patch.object(sys,'argv',['rede-widget.py']), patch.object(network,'interface',return_value='synthetic0'), patch.object(network,'counters',side_effect=[(0,0),(2048,1024)]), patch.object(network.time,'sleep'), patch.object(network.time,'monotonic',side_effect=[1,3]):
            network.main()
            self.assertEqual(output.getvalue(), '↓ 1.0 KiB/s   ↑ 512.0 B/s\n')
        with io.StringIO() as output, contextlib.redirect_stdout(output), patch.object(sys,'argv',['rede-widget.py','--details']), patch('network_quality.collect',return_value={'items':[]}):
            with self.assertRaises(SystemExit) as stopped:network.main()
            self.assertEqual(stopped.exception.code, 0)
            self.assertEqual(output.getvalue(), 'AZCLOCK_QUALITY:{"items": []}\n')

    def test_security_summary_skips_dns(self):
        security = module('seguranca-widget.py')
        def sockets(state):
            return [['0','0','192.0.2.1:1234','198.51.100.2:443']] if state=='established' else [['0','128','0.0.0.0:80']]
        with io.StringIO() as output, contextlib.redirect_stdout(output), patch.object(sys,'argv',['seguranca-widget.py','--summary']), patch.object(security,'sockets',side_effect=sockets), patch.object(security,'hostnames',side_effect=AssertionError('DNS in summary')):
            with self.assertRaises(SystemExit):security.main()
            prefix, data = output.getvalue().split(':',1)
            self.assertEqual(prefix,'AZCLOCK_NETWORK')
            self.assertEqual(json.loads(data), {'text':'Conexões externas: 1\nEscutando portas: 1'})

    def test_temperatures_fallback_and_details(self):
        temperatures = module('temperaturas-widget.py')
        with io.StringIO() as output, contextlib.redirect_stdout(output), patch.object(sys,'argv',['temperaturas-widget.py']), patch.object(temperatures,'load',side_effect=lambda name, age: [] if name=='sensors-paths.json' else True):
            temperatures.main()
            self.assertEqual(output.getvalue(), '<span font_family="monospace">CPU: N/D\nGPU: N/D</span>\n')
        with io.StringIO() as output, contextlib.redirect_stdout(output), patch.object(sys,'argv',['temperaturas-widget.py','--details']), patch.object(temperatures,'details',return_value={'items':[],'omitted':0}):
            with self.assertRaises(SystemExit):temperatures.main()
            self.assertEqual(output.getvalue(), 'AZCLOCK_TEMPERATURES:{"items": [], "omitted": 0}\n')

    def test_worker_style_exec_still_runs_cpu_entrypoint(self):
        # This is the same namespace contract used by metrics-worker, with fake reads.
        source = (ROOT/'widgets/cpu-ram-widget.py').read_text()
        reads = ['cpu 10 0 0 90 0 0 0 0\n', 'cpu 20 0 0 180 0 0 0 0\n', 'MemTotal: 1000 kB\nMemAvailable: 250 kB\n']
        namespace = {'__name__':'__main__','__file__':str(ROOT/'widgets/cpu-ram-widget.py')}
        with io.StringIO() as output, contextlib.redirect_stdout(output), patch.object(Path,'read_text',side_effect=reads), patch('time.sleep'), patch('widget_runtime.load',return_value=50), patch('external_storage.external_usage',return_value=None):
            exec(compile(source, namespace['__file__'], 'exec'), namespace)
            self.assertEqual(output.getvalue(), '<span font_family="monospace" size="7680" line_height="1.5">  CPU    █░░░░░░░   10%\n  RAM    ██████░░   75%\n  SSD    ████░░░░   50%</span>\n')


if __name__ == '__main__':unittest.main()
