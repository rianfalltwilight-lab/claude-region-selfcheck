"""Serve the diagnostic page on loopback; never expose .env or directory listings."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from config import ROOT, load_env, public_config, server_address


def page_bytes(settings):
    text = (ROOT / 'Browser-Region-SelfCheck.html').read_text(encoding='utf-8')
    config_json = json.dumps(settings, ensure_ascii=False).replace('<', '\\u003c')
    return text.replace('/* SERVER_CONFIG */', 'window.REGION_SELFCHECK_CONFIG=' + config_json + ';').encode('utf-8')


def make_handler(settings):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            # Reject cross-origin/host-rebinding attempts before returning browser headers.
            if self.headers.get('Host') not in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'):
                self.send_error(403)
                return
            path = urlsplit(self.path).path
            if path == '/headers':
                body = json.dumps({'Accept-Language': self.headers.get('Accept-Language'),
                                   'User-Agent': self.headers.get('User-Agent')}, ensure_ascii=False).encode('utf-8')
                content_type = 'application/json; charset=utf-8'
            elif path in ('/', '/Browser-Region-SelfCheck.html'):
                body = page_bytes(settings)
                content_type = 'text/html; charset=utf-8'
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass
    return Handler


def main():
    values = load_env()
    address = server_address(values)
    server = ThreadingHTTPServer(address, make_handler(public_config(values)))
    print(f'Open http://{address[0]}:{address[1]} in your Claude browser profile. Ctrl+C to stop.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
