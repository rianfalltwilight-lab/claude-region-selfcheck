import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from config import claude_environment, load_env, public_config, server_address
from server import make_handler, page_bytes


class ConfigTests(unittest.TestCase):
    def test_file_and_process_precedence(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / '.env'
            path.write_text('# comment\nSELFCHECK_PORT="12345"\n', encoding='utf-8')
            with patch.dict('os.environ', {'SELFCHECK_PORT': '23456'}, clear=True):
                self.assertEqual(load_env(path)['SELFCHECK_PORT'], '23456')

    def test_public_config_does_not_export_secrets(self):
        config = public_config({'CLAUDE_PROXY_URL': 'http://user:secret@localhost:7897', 'ANTHROPIC_API_KEY': 'secret'})
        self.assertNotIn('secret', json.dumps(config))
        self.assertEqual(config['expectedTimeZone'], 'Asia/Tokyo')

    def test_loopback_and_bounds(self):
        for values in ({'SELFCHECK_HOST': '0.0.0.0'}, {'SELFCHECK_PORT': '0'}, {'SELFCHECK_PORT': '65536'}):
            with self.assertRaises(ValueError):
                server_address(values)
        with self.assertRaises(ValueError):
            public_config({'SELFCHECK_RTC_TIMEOUT_MS': '0'})

    def test_proxy_required_and_lowercase_replaced(self):
        for proxy in ('', 'socks5://localhost:7897', 'http://localhost:notaport'):
            with self.assertRaises(ValueError):
                claude_environment({'CLAUDE_PROXY_URL': proxy}, {})
        parent = {'https_proxy': 'http://old:80', 'ALL_PROXY': 'socks5://old:80', 'PATH': 'kept'}
        child = claude_environment({'CLAUDE_PROXY_URL': 'http://127.0.0.1:7897'}, parent)
        self.assertEqual(child['HTTPS_PROXY'], 'http://127.0.0.1:7897')
        self.assertNotIn('https_proxy', child)
        self.assertNotIn('ALL_PROXY', child)
        self.assertEqual(parent['https_proxy'], 'http://old:80')

    def test_script_config_escaping(self):
        body = page_bytes({'expectedTimeZone': '</script><script>alert(1)</script>'}).decode()
        self.assertIn('\\u003c/script>', body)
        self.assertNotIn('/* SERVER_CONFIG */', body)

    def test_http_routes_without_opening_a_listener(self):
        handler_type = make_handler(public_config({}))
        class MemorySocket:
            def __init__(self, request):
                self.request = io.BytesIO(request)
                self.response = bytearray()
            def makefile(self, mode, *args):
                return self.request
            def sendall(self, data):
                self.response.extend(data)
        def get(path, host='127.0.0.1:18765'):
            socket = MemorySocket(f'GET {path} HTTP/1.0\r\nHost: {host}\r\nAccept-Language: ja,en;q=0.9\r\n\r\n'.encode())
            handler_type(socket, ('127.0.0.1', 1), SimpleNamespace(server_port=18765))
            return bytes(socket.response)
        response = get('/headers')
        self.assertIn(b'200 OK', response)
        self.assertEqual(json.loads(response.split(b'\r\n\r\n')[1])['Accept-Language'], 'ja,en;q=0.9')
        self.assertIn(b'404', get('/.env'))
        self.assertIn(b'403', get('/headers', 'untrusted.example:18765'))
        self.assertIn(b'window.REGION_SELFCHECK_CONFIG=', get('/'))


if __name__ == '__main__':
    unittest.main()
