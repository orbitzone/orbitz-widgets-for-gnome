import importlib.util
import sys
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'widgets'))
spec=importlib.util.spec_from_file_location('storage',Path(__file__).resolve().parents[1]/'widgets/armazenamento-widget.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)
class StorageTests(unittest.TestCase):
    def test_smart_unavailable_and_alert(self):
        with patch.object(storage.shutil,'which',return_value=None):
            self.assertEqual(storage.health('/dev/test')['state'],'unavailable')
        with patch.object(storage.shutil,'which',return_value='/usr/sbin/smartctl'),patch.object(storage,'run',return_value=subprocess.CompletedProcess([],8,'{"smart_status":{"passed":false}}')):
            self.assertEqual(storage.health('/dev/test')['state'],'alert')
        with patch.object(storage.shutil,'which',return_value='/usr/sbin/smartctl'),patch.object(storage,'run',return_value=subprocess.CompletedProcess([],2,'{}')):
            self.assertEqual(storage.health('/dev/test')['state'],'unavailable')
    def test_failure_not_healthy(self):
        with patch.object(storage,'run',side_effect=OSError()):
            self.assertEqual(storage.collect()['text'],'Armazenamento: sem leitura')
    def test_deduplicates_bind_mounts(self):
        from types import SimpleNamespace
        raw='{"blockdevices":[{"name":"/dev/a","type":"disk","model":"SSD","children":[{"name":"/dev/a1","type":"part","mountpoints":["/home","/"]}]}]}'
        with patch.object(storage,'run',return_value=subprocess.CompletedProcess([],0,raw)),patch.object(storage.os,'stat',return_value=SimpleNamespace(st_dev=1)),patch.object(storage.os,'statvfs',return_value=SimpleNamespace(f_blocks=100,f_frsize=1024,f_bavail=4,f_bfree=4,f_files=100,f_favail=50)):
            data=storage.collect()
        self.assertEqual(len(data['items']),1)
        self.assertEqual(data['items'][0]['mount'],'/')
        self.assertEqual(data['items'][0]['percent'],96)
        self.assertIn('1 em atenção',data['text'])

    def test_external_content_is_bounded_and_siblings_not_inherited(self):
        import tempfile,json
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as folder:
            for index in range(35): (Path(folder)/f'file{index}').write_text('')
            raw=json.dumps({'blockdevices':[{'name':'/dev/usb','type':'disk','tran':'usb','mountpoints':[folder]},{'name':'/dev/internal','type':'disk','mountpoints':['/']}]})
            with patch.object(storage,'run',return_value=subprocess.CompletedProcess([],0,raw)),patch.object(storage,'health',return_value={'state':'unavailable','temperature':None,'wear':None,'note':'Unavailable'}),patch.object(storage.os,'stat',return_value=SimpleNamespace(st_dev=1)),patch.object(storage.os,'statvfs',return_value=SimpleNamespace(f_blocks=100,f_frsize=1024,f_bavail=4,f_bfree=4,f_files=100,f_favail=50)):
                data=storage.collect(True,True)
            self.assertEqual(len(data['items']),1)
            self.assertEqual(data['items'][0]['device'],'/dev/usb')
            self.assertEqual(len(data['items'][0]['files']),30)
            self.assertTrue(data['items'][0]['more'])
