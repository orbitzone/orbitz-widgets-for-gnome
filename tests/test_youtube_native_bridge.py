import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
YOUTUBE_DIR = ROOT / 'extension' / 'youtube-widget'
sys.path.insert(0, str(YOUTUBE_DIR))
spec = importlib.util.spec_from_file_location('orbitz_youtube_widget_bridge', YOUTUBE_DIR / 'youtube-widget.py')
youtube_widget = importlib.util.module_from_spec(spec)
spec.loader.exec_module(youtube_widget)


def message(payload):
    return SimpleNamespace(get_js_value=lambda: SimpleNamespace(to_string=lambda: payload))


class YouTubeNativeBridgeTests(unittest.TestCase):
    def test_bridge_requires_the_random_token_and_exact_payload_shape(self):
        token = 'synthetic-random-token'
        self.assertEqual(youtube_widget.bridge_value(message('{"token":"synthetic-random-token","value":"idle"}'), token), 'idle')
        for payload in (
            '{"token":"wrong","value":"idle"}',
            '{"token":"☃","value":"idle"}',
            '{"token":"synthetic-random-token","value":"idle","extra":true}',
            '{"token":4,"value":"idle"}',
            'not json',
            '"idle"',
        ):
            self.assertIsNone(youtube_widget.bridge_value(message(payload), token))

    def test_bridge_rejects_oversized_messages_before_json_parsing(self):
        token = 'synthetic-random-token'
        payload = '{"token":"synthetic-random-token","value":"' + ('x' * 5000) + '"}'
        original_loads = youtube_widget.json.loads
        try:
            youtube_widget.json.loads = lambda _value: self.fail('oversized payload reached JSON parser')
            self.assertIsNone(youtube_widget.bridge_value(message(payload), token))
        finally:
            youtube_widget.json.loads = original_loads

    def test_external_links_are_limited_to_fixed_hosts_and_paths(self):
        allowed = (
            'https://www.orbit.zone/',
            'https://console.cloud.google.com/apis/credentials',
            'https://www.youtube.com/',
            'https://www.youtube.com/watch?v=abcdefghijk',
        )
        denied = (
            'http://www.orbit.zone/',
            'https://evil.example/',
            'https://www.youtube.com.evil.example/',
            'https://www.youtube.com/watch?v=bad',
            'https://www.youtube.com/watch?v=abcdefghijk&redirect=https://evil.example',
            'https://www.youtube.com/redirect?q=https://evil.example',
            'https://console.cloud.google.com/other',
            'https://www.orbit.zone:443/',
            'https://user@www.orbit.zone/',
        )
        for uri in allowed:
            with self.subTest(uri=uri):
                self.assertTrue(youtube_widget.external_uri_allowed(uri))
        for uri in denied:
            with self.subTest(uri=uri):
                self.assertFalse(youtube_widget.external_uri_allowed(uri))

    def test_native_handlers_validate_each_bridge_message(self):
        source = (YOUTUBE_DIR / 'youtube-widget.py').read_text()
        html = (YOUTUBE_DIR / 'index.html').read_text()
        self.assertIn('bridge_value(result,token)', source)
        self.assertIn('if external_uri_allowed(uri):', source)
        self.assertIn('const nativeBridgeToken=location.pathname.split', html)
        self.assertIn("bridge.postMessage(JSON.stringify({token:nativeBridgeToken,value}))", html)


if __name__ == '__main__':
    unittest.main()
