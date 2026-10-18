import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'widgets'))
import external_storage as external

class ExternalDevicesTests(unittest.TestCase):
    def test_physical_devices_separate_and_partitions_aggregated(self):
        devices=[{'name':'sda','type':'disk','tran':'usb','children':[{'name':'sda1','type':'part','mountpoints':['/media/a']},{'name':'sda2','type':'part','mountpoints':['/media/a2']}]},{'name':'sdb','type':'disk','tran':'usb','children':[{'name':'sdb1','type':'part','mountpoints':['/media/b']}]},{'name':'sdc','type':'disk','tran':'usb','mountpoints':[None]}]
        def usage(point):
            return SimpleNamespace(used=20 if point=='/media/b' else 60,free=80 if point=='/media/b' else 40)
        identities={'/media/a':1,'/media/a2':2,'/media/b':3}
        with patch.object(external,'load',return_value=None),patch.object(external,'save'),patch.object(external,'bounded_run',return_value=subprocess.CompletedProcess([],0,json.dumps({'blockdevices':devices}))),patch.object(external.Path,'stat',lambda p:SimpleNamespace(st_dev=identities[str(p)])),patch.object(external.shutil,'disk_usage',side_effect=usage):
            result=external.external_devices()
        self.assertEqual([d['name'] for d in result],['sda','sdb','sdc'])
        self.assertEqual(result[0]['percent'],60)
        self.assertEqual(len(result[0]['mounts']),2)
        self.assertEqual(result[1]['percent'],20)
        self.assertIsNone(result[2]['percent'])
