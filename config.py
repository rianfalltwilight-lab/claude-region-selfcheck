"""Small explicit .env reader; no third-party dependency or secret export."""
import os
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent


def load_env(path=None):
    values = {}
    path = Path(path) if path is not None else ROOT / '.env'
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                raise ValueError('Invalid .env line: expected KEY=value')
            key, value = line.split('=', 1)
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            values[key.strip()] = value
    # Only explicit process variables override the local file.
    values.update(os.environ)
    return values


def public_config(values):
    timeout = int(values.get('SELFCHECK_RTC_TIMEOUT_MS', '10000'))
    if not 1000 <= timeout <= 60000:
        raise ValueError('SELFCHECK_RTC_TIMEOUT_MS must be 1000..60000')
    stun = values.get('SELFCHECK_STUN_URL', 'stun:stun.l.google.com:19302')
    if not stun.startswith(('stun:', 'stuns:')) or any(c.isspace() for c in stun):
        raise ValueError('SELFCHECK_STUN_URL must be a STUN URL')
    return {
        'expectedTimeZone': values.get('SELFCHECK_EXPECTED_TIMEZONE', 'Asia/Tokyo'),
        'expectedLanguages': [s.strip() for s in values.get('SELFCHECK_EXPECTED_LANGUAGES', 'ja,en').split(',') if s.strip()],
        'stunUrl': stun,
        'rtcTimeoutMs': timeout,
    }


def server_address(values):
    host = values.get('SELFCHECK_HOST', '127.0.0.1')
    if host not in ('127.0.0.1', 'localhost'):
        raise ValueError('SELFCHECK_HOST must be 127.0.0.1 or localhost')
    port = int(values.get('SELFCHECK_PORT', '18765'))
    if not 1 <= port <= 65535:
        raise ValueError('SELFCHECK_PORT must be 1..65535')
    return host, port


def claude_environment(values, base=None):
    proxy = values.get('CLAUDE_PROXY_URL', '').strip()
    try:
        parsed = urlsplit(proxy)
        parsed.port  # Validate the optional port without printing credentials.
    except ValueError:
        raise ValueError('CLAUDE_PROXY_URL is not a valid HTTP proxy URL') from None
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.path not in ('', '/') or parsed.query or parsed.fragment:
        raise ValueError('Set CLAUDE_PROXY_URL to your working http:// or https:// proxy')
    env = dict(os.environ if base is None else base)
    # Lowercase proxy variables can take precedence; remove them from this child only.
    for key in list(env):
        if key.lower() in ('http_proxy', 'https_proxy', 'all_proxy', 'no_proxy'):
            del env[key]
    env.update(HTTP_PROXY=proxy, HTTPS_PROXY=proxy,
               NO_PROXY=values.get('CLAUDE_NO_PROXY', 'localhost,127.0.0.1,::1'),
               TZ=values.get('CLAUDE_TZ', 'Asia/Tokyo'))
    return env
