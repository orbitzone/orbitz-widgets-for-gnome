import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'widgets'))
spec=importlib.util.spec_from_file_location('services',Path(__file__).resolve().parents[1]/'widgets/servicos-widget.py')
services=importlib.util.module_from_spec(spec);spec.loader.exec_module(services)

class ServicesTests(unittest.TestCase):
    def test_empty_and_permission_failure(self):
        with patch.object(services,'run',return_value=subprocess.CompletedProcess([],0,'')):
            self.assertEqual(services.collect()['text'],'Serviços: OK')
        with patch.object(services,'run',side_effect=OSError()):
            self.assertEqual(services.collect()['text'],'Serviços: consulta incompleta')

    def test_caps_details_and_read_only(self):
        calls=[]
        def query(args,**kw):
            calls.append(args)
            self.assertLessEqual(kw['timeout'],2)
            if 'show' in args:
                text='Id=test0.service\nResult=exit-code\nExecMainStatus=1\nStateChangeTimestamp=Thu 2026-10-15 09:00:00\n'
            else: text='\n'.join(f'test{i}.service loaded failed failed Test {i}' for i in range(9))
            return subprocess.CompletedProcess(args,0,text)
        with patch.object(services,'run',side_effect=query): data=services.collect(True)
        self.assertEqual(len(calls),4)
        self.assertEqual(data['groups'][0]['count'],9)
        self.assertEqual(len(data['groups'][0]['items']),6)
        self.assertEqual(data['groups'][0]['items'][0]['result'],'exit-code')
        self.assertTrue(all(not any(a in args for a in ('restart','start','stop','reset-failed')) for args in calls))

    def test_malformed_list_is_not_healthy(self):
        with patch.object(services,'run',return_value=subprocess.CompletedProcess([],0,'unrecognized response')):
            self.assertEqual(services.collect()['text'],'Serviços: consulta incompleta')

    def test_missing_details_are_reported_as_partial(self):
        def query(args, **kwargs):
            text = 'Id=other.service\nResult=exit-code\n' if 'show' in args else 'test.service loaded failed failed Test'
            return subprocess.CompletedProcess(args, 0, text)
        with patch.object(services, 'run', side_effect=query):
            data = services.collect(True)
        self.assertTrue(all(group['error'] for group in data['groups']))
        self.assertIn('parcial', data['text'])

    def test_rejects_option_names_and_nonfailed_units(self):
        for line in ('--bad.service loaded failed failed Test', 'test.service loaded active running Test', 'x'*257 + '.service loaded failed failed Test'):
            with self.subTest(line=line), patch.object(services, 'run', return_value=subprocess.CompletedProcess([], 0, line)):
                data = services.collect(True)
                self.assertTrue(all(group['error'] for group in data['groups']))
