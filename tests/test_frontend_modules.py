"""Frontend extraction contracts, with synthetic input and no network/GTK session."""
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

YOUTUBE = Path(__file__).resolve().parents[1] / 'extension' / 'youtube-widget'
sys.path.insert(0, str(YOUTUBE))
import youtube_api as api
import youtube_server as server


class YouTubeBoundaryTests(unittest.TestCase):
    def request(self, action, data=None, origin='http://127.0.0.1:1234', path=None):
        handler = object.__new__(server.make_handler('synthetic-token'))
        raw = json.dumps(data or {}).encode()
        handler.path = path or '/synthetic-token/' + action
        handler.headers = {'Origin': origin, 'Content-Length': str(len(raw))}
        handler.rfile = io.BytesIO(raw)
        handler.server = SimpleNamespace(server_port=1234, cache={})
        replies = []
        handler.reply = lambda *args: replies.append(args)
        handler.do_POST()
        return replies[-1], handler

    def test_loopback_origin_and_token_required_before_api(self):
        with patch.object(server, 'search') as search:
            self.assertEqual(self.request('search', {'query': 'test'}, origin='https://example.invalid')[0][0], 403)
            self.assertEqual(self.request('search', {'query': 'test'}, path='/wrong/search')[0][0], 403)
            search.assert_not_called()

    def test_search_and_missing_key_contract(self):
        items = [{'id': 'abcdefghijk', 'title': 'Synthetic'}]
        with patch.object(server, 'search', return_value=items) as search:
            reply, handler = self.request('search', {'query': 'test'})
            self.assertEqual(reply, (200, {'items': items}))
            self.assertEqual(handler.server.cache['test'][1], items)
            search.assert_called_once_with('test')
        with patch.object(server, 'search', side_effect=api.MissingAPIKey('Configure')):
            reply, _ = self.request('search', {'query': 'test'})
            self.assertEqual(reply, (400, {'error': 'Configure', 'code': 'key_required'}))

    def test_invalid_requests_and_comment_cache(self):
        self.assertEqual(self.request('search', {'query': ''})[0][0], 400)
        self.assertEqual(self.request('comments', {'video': []})[0][0], 400)
        self.assertEqual(self.request('unknown')[0][0], 404)
        with patch.object(server, 'comments', return_value={'items': [], 'nextPage': ''}) as comments:
            reply, handler = self.request('comments', {'video': 'abcdefghijk'})
            self.assertEqual(reply[0], 200)
            self.assertIn(('abcdefghijk', ''), handler.server.comment_cache)
            comments.assert_called_once_with('abcdefghijk', '')

    def test_document_get_keeps_token_boundary(self):
        handler = object.__new__(server.make_handler('synthetic-token'))
        replies = []
        handler.reply = lambda *args: replies.append(args)
        handler.path = '/index.html'
        handler.do_GET()
        self.assertEqual(replies[-1], (404, {}))
        handler.path = '/synthetic-token/'
        handler.do_GET()
        self.assertEqual(replies[-1][0], 200)
        self.assertEqual(replies[-1][2], 'text/html')
        self.assertIn(b'<title>YouTube</title>', replies[-1][1])

    def test_local_key_permissions_and_validation(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(api, 'CONFIG', Path(folder) / 'youtube.json'):
            self.assertEqual(api.read_key(), '')
            with self.assertRaises(ValueError):
                api.save_key('invalid')
            key = 'synthetic_key_' + 'x' * 25
            api.save_key(key)
            self.assertEqual(api.read_key(), key)
            self.assertEqual(api.CONFIG.stat().st_mode & 0o777, 0o600)
            api.CONFIG.unlink()
            target = Path(folder) / 'target'
            target.write_text(json.dumps({'key': key}))
            api.CONFIG.symlink_to(target)
            self.assertEqual(api.read_key(), '')


if __name__ == '__main__':
    unittest.main()
