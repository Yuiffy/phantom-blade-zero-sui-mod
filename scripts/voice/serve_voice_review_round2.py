"""Serve second-round audio comparison and independent local review records."""
import argparse
import hashlib
import json
import threading
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from paths import ROOT as WORKSPACE
ROOT = WORKSPACE / 'voice-review-round2'
MANIFEST = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
MANIFEST_SHA = hashlib.sha256((ROOT / 'manifest.json').read_bytes()).hexdigest()
ISSUES = {i['id']: i for i in MANIFEST['issues']}
MEDIA = {m['id']: m for m in MANIFEST['media']}
CANDIDATES = {c['id'] for c in MANIFEST['candidates']}
LOCK = threading.Lock()


def read_state(path):
    if path.exists():
        data = json.loads(path.read_text(encoding='utf-8'))
        if data.get('manifest_sha256') != MANIFEST_SHA:
            raise ValueError('Review belongs to another manifest; preserve it before switching sources')
        return data
    return {'manifest_sha256': MANIFEST_SHA, 'issues': {}, 'media': {}}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def host_allowed(self):
        return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}

    def do_GET(self):
        if not self.host_allowed():
            return self.response({'error': 'local only'}, 403)
        if urlsplit(self.path).path == '/api/review':
            with LOCK:
                return self.response(read_state(self.server.feedback))
        return super().do_GET()

    def do_POST(self):
        if not self.host_allowed() or self.headers.get('Origin') not in {f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'}:
            return self.response({'error': 'same origin required'}, 403)
        if urlsplit(self.path).path != '/api/review':
            return self.response({'error': 'not found'}, 404)
        try:
            length = int(self.headers.get('Content-Length', 0))
            if not 0 < length <= 16000:
                raise ValueError('Invalid body size')
            payload = json.loads(self.rfile.read(length))
            if payload.get('manifest_sha256') != MANIFEST_SHA:
                raise ValueError('Manifest mismatch')
            scope, key, item = payload.get('scope'), payload.get('id'), payload.get('item')
            if scope not in ['issues', 'media'] or key not in (ISSUES if scope == 'issues' else MEDIA) or not isinstance(item, dict):
                raise ValueError('Unknown review target')
            choice = item.get('choice')
            allowed = ({'original', 'by-event'} | set(ISSUES[key]['suggestions'])) if scope == 'issues' else ({'current', 'original'} | CANDIDATES)
            if choice is not None and choice not in allowed:
                raise ValueError('Invalid candidate')
            note = item.get('note', '')
            if not isinstance(note, str) or len(note) > 2000:
                raise ValueError('Invalid note')
            ratings = item.get('ratings', {})
            if not isinstance(ratings, dict) or any(k not in CANDIDATES or v not in [None, 'good', 'bad'] for k, v in ratings.items()):
                raise ValueError('Invalid rating')
            result = {'choice': choice, 'note': note, 'ratings': ratings,
                      'updated_at': datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')}
            with LOCK:
                state = read_state(self.server.feedback)
                state[scope][key] = result
                temporary = self.server.feedback.with_suffix('.tmp')
                temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                temporary.replace(self.server.feedback)
            self.response({'saved': True, 'scope': scope, 'id': key, 'item': result})
        except (ValueError, TypeError) as error:
            self.response({'error': str(error)}, 400)

    def list_directory(self, path):
        self.send_error(404)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=9212)
    parser.add_argument('--feedback-file', type=Path, default=ROOT / 'reviews/user-review.json')
    args = parser.parse_args()
    args.feedback_file.parent.mkdir(parents=True, exist_ok=True)
    read_state(args.feedback_file)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.feedback = args.feedback_file
    print(f'Round 2 review: http://127.0.0.1:{args.port}/', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
