import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'widgets'))
from pressure_metrics import parse_pressure, snapshot

class PressureTests(unittest.TestCase):
    def test_duplicate_samples_are_rejected(self):
        with self.assertRaises(ValueError):
            parse_pressure('some avg10=0 avg60=0 avg300=0\nsome avg10=1 avg60=1 avg300=1')

    def test_rejects_invalid_and_nonfinite(self):
        for value in ('nan', 'inf', '-1', '101'):
            with self.assertRaises(ValueError):
                parse_pressure(f'some avg10={value} avg60=0 avg300=0')
        with self.assertRaises((ValueError, KeyError)):
            parse_pressure('some total=23')

    def test_thresholds_multiple_resources_and_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(snapshot(root)['text'], 'Gargalos: indisponível')
            for name, value in [('cpu', 0), ('memory', 5), ('io', 20)]:
                (root/name).write_text(f'some avg10={value} avg60=1.25 avg300=0.5 total=100\nfull avg10=0 avg60=0 avg300=0 total=0\n')
            data = snapshot(root)
            self.assertEqual([i['level'] for i in data['items']], ['normal', 'attention', 'high'])
            self.assertEqual(data['text'], 'Gargalo: Memória + Disco / E/S')
            self.assertIsNone(data['items'][0]['full'])
            for name in ('memory', 'io'):
                (root/name).write_text('some avg10=0 avg60=0 avg300=0 total=0')
            self.assertEqual(snapshot(root)['text'], 'Sem pressão relevante')
            (root/'io').unlink()
            self.assertEqual(snapshot(root)['text'], 'Gargalos: leitura parcial')

if __name__ == '__main__': unittest.main()
