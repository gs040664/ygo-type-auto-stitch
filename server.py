#!/usr/bin/env python3
"""Local CORS-safe image/API proxy for the YGO TYPE demo, standard library only."""
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen
import json, re, sys, time, webbrowser, zipfile, threading

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / '.cache'
CACHE.mkdir(exist_ok=True)
HOST, PORT = '127.0.0.1', 8765
MAX_FILE = 4_000_000
_catalog = None
_catalog_lock = threading.Lock()

def full_catalog():
    global _catalog
    if _catalog is not None: return _catalog
    with _catalog_lock:
        if _catalog is not None: return _catalog
        path=CACHE/'cards.zip'
        if not path.exists() or time.time()-path.stat().st_mtime>14*86400:
            req=Request('https://ygocdb.com/api/v0/cards.zip',headers={'User-Agent':'YGOTypePersonalFanTool/1.0'})
            with urlopen(req,timeout=35) as resp: data=resp.read(35_000_001)
            if len(data)>35_000_000: raise ValueError('Catalogue zip too large')
            path.write_bytes(data)
        with zipfile.ZipFile(path) as z:
            cards=json.loads(z.read('cards.json'))
        _catalog=list(cards.values()) if isinstance(cards,dict) else cards
        return _catalog

@lru_cache(maxsize=1)
def card_names():
    return json.dumps([
        [card['id'], card.get('jp_name'), card.get('sc_name'), card.get('en_name')]
        for card in full_catalog()
        if isinstance(card.get('id'), int) and card['id'] > 0
    ], ensure_ascii=False, separators=(',', ':')).encode('utf-8')

class Handler(BaseHTTPRequestHandler):
    def send(self, status, data, mimetype='application/json; charset=utf-8'):
        self.send_response(status)
        self.send_header('Content-Type', mimetype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Cache-Control','public, max-age=3600')
        self.send_header('X-Content-Type-Options','nosniff')
        self.end_headers()
        try: self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError): pass

    def get_remote(self, url, cache_key, ttl=86400):
        dest=CACHE/cache_key
        if dest.exists() and time.time()-dest.stat().st_mtime < ttl:return dest.read_bytes()
        req=Request(url,headers={'User-Agent':'YGOTypePersonalFanTool/1.0 (+local user)', 'Accept':'application/json,image/jpeg,*/*'})
        with urlopen(req,timeout=14) as resp:
            length=resp.headers.get('Content-Length')
            if length and int(length)>MAX_FILE:raise ValueError('Response too large')
            body=resp.read(MAX_FILE+1)
        if len(body)>MAX_FILE:raise ValueError('Response too large')
        dest.write_bytes(body)
        return body

    def do_GET(self):
        path=urlparse(self.path); q=parse_qs(path.query)
        if path.path in ('/','/index.html'):
            return self.send(200,(ROOT/'index.html').read_bytes(),'text/html; charset=utf-8')
        if path.path=='/card-names.json':
            try:
                return self.send(200, card_names())
            except Exception as e:
                return self.send(502, json.dumps({'error': str(e)}).encode())
        if path.path=='/api/image':
            card_id=q.get('id',[''])[0]
            if not re.fullmatch(r'[0-9]{1,10}',card_id or ''):return self.send(400,b'{"error":"bad card id"}')
            edition = q.get('edition', ['jp'])[0]
            if edition not in ('jp', 'sc', 'en'):
                return self.send(400, b'{"error":"bad edition"}')
            try:
                data = self.get_remote(
                    f'https://cdn.233.momobako.com/ygoimg/{edition}/{card_id}.webp',
                    f'image_{edition}_{card_id}.webp', 90 * 86400,
                )
                return self.send(200, data, 'image/webp')
            except Exception as e:return self.send(502,json.dumps({'error':str(e)},ensure_ascii=False).encode())
        self.send(404,b'Not found','text/plain')

if __name__=='__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--build-index':
        Path(sys.argv[2]).write_bytes(card_names())
        sys.exit(0)
    print('YGO TYPE 已啟動: http://127.0.0.1:8765')
    print('不需要安裝任何 Python 套件。按 Ctrl+C 關閉。')
    try:
        srv=ThreadingHTTPServer((HOST,PORT),Handler)
        webbrowser.open(f'http://{HOST}:{PORT}/')
        srv.serve_forever()
    except KeyboardInterrupt: print('\n已停止。')
    except OSError as exc: print(f'無法啟動：{exc}')
