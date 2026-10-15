import sys
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'widgets'))
import network_quality as quality

class QualityTests(unittest.TestCase):
    def test_parsing(self):
        text='5 packets transmitted, 4 received, 20% packet loss, time 1000ms\nrtt min/avg/max/mdev = 1.2/3.4/6.7/2.1 ms'
        self.assertEqual(quality.parse_ping(text),(20,3.4,2.1))
        self.assertEqual(quality.parse_ping('5 packets transmitted, 0 received, 100% packet loss'),(100,None,None))
        for text in ('unavailable','0% packet loss','200% packet loss'):
            with self.assertRaises(ValueError): quality.parse_ping(text)

    def test_gateway_and_bounded_probe(self):
        with patch.object(quality,'run',return_value=subprocess.CompletedProcess([],0,'[{"gateway":"192.168.1.1","metric":100},{"gateway":"10.0.0.1","metric":10}]')):
            self.assertEqual(quality.gateway(),'10.0.0.1')
        with patch.object(quality,'run',return_value=subprocess.CompletedProcess([],1,'100% packet loss')) as run:
            data=quality.probe('Internet','1.1.1.1')
            self.assertEqual(data['loss'],100)
            self.assertEqual(run.call_args.kwargs['timeout'],4)
            self.assertIn('5',run.call_args.args[0])
        self.assertTrue(quality.probe('Roteador',None)['error'])
        with patch.object(quality,'run',side_effect=OSError()):
            self.assertTrue(quality.probe('Internet','1.1.1.1')['error'])
