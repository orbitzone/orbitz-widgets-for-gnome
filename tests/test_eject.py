import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'widgets'))
import external_storage as external

class EjectTests(unittest.TestCase):
    def test_unmount_all_verify_then_power_off(self):
        calls=[]; inventories=0
        def query(args,**kwargs):
            nonlocal inventories
            calls.append(args)
            self.assertLessEqual(kwargs['timeout'],5)
            if args[0]=='lsblk':
                inventories+=1
                data={'blockdevices':[{'name':'/dev/sdz','mountpoints':[None],'children':[
                    {'name':'/dev/sdz1','mountpoints':['/media/a'] if inventories==1 else [None]},
                    {'name':'/dev/sdz2','mountpoints':['/media/b'] if inventories==1 else [None]}]}]}
                return subprocess.CompletedProcess(args,0,json.dumps(data))
            return subprocess.CompletedProcess(args,0,'')
        with patch.object(external,'device_identity',return_value='123:8:32'),patch.object(external,'external_devices',return_value=[{'name':'sdz','identity':'123:8:32'}]),patch.object(external,'bounded_run',side_effect=query):
            result=external.eject_device('sdz','123:8:32')
        self.assertTrue(result['ok'])
        self.assertEqual([c[1] for c in calls if c[0]=='udisksctl'],['unmount','unmount','power-off'])
        self.assertTrue(all('--force' not in c for c in calls))
        self.assertEqual(calls[-2][0],'lsblk')

    def test_stale_identity_does_not_unmount(self):
        with patch.object(external,'device_identity',return_value='new'),patch.object(external,'bounded_run') as query:
            self.assertFalse(external.eject_device('sdz','old')['ok'])
            query.assert_not_called()

    def test_busy_device_does_not_power_off(self):
        calls=[]
        def query(args,**kw):
            calls.append(args)
            if args[0]=='lsblk':return subprocess.CompletedProcess(args,0,json.dumps({'blockdevices':[{'name':'/dev/sdz1','mountpoints':['/media/a']}]}))
            raise subprocess.CalledProcessError(1,args)
        with patch.object(external,'device_identity',return_value='123'),patch.object(external,'external_devices',return_value=[{'name':'sdz','identity':'123'}]),patch.object(external,'bounded_run',side_effect=query):
            self.assertFalse(external.eject_device('sdz','123')['ok'])
        self.assertFalse(any('power-off' in c for c in calls))
