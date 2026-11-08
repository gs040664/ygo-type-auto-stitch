#!/usr/bin/env python3
"""Local CORS-safe image/API proxy for the YGO TYPE demo, standard library only."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs, quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json, re, time, webbrowser, zipfile, io, threading

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
        if path.path=='/api/search':
            word=q.get('q',[''])[0][:12]
            try: start=max(0,min(500,int(q.get('start',['0'])[0])))
            except ValueError: start=0
            if not word:return self.send(400,b'{"error":"missing query"}')
            url=f'https://ygocdb.com/api/v0/?search={quote(word)}&start={start}'
            key=f'search_{word.encode().hex()}_{start}.json'
            try:return self.send(200,self.get_remote(url,key,12*3600))
            except Exception as e:return self.send(502,json.dumps({'error':str(e)},ensure_ascii=False).encode())
        if path.path=='/api/search-all':
            word=q.get('q',[''])[0][:12]
            if not word:return self.send(400,b'{"error":"missing query"}')
            try:
                cards=full_catalog()
                results=[c for c in cards if word in (c.get('cn_name') or c.get('sc_name') or '') and isinstance(c.get('id'),int) and c.get('id')>0]
                results.sort(key=lambda c:(len(c.get('cn_name') or c.get('sc_name') or ''),c.get('id',0)))
                return self.send(200,json.dumps({'result':results[:150]},ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                return self.send(502,json.dumps({'error':str(e)},ensure_ascii=False).encode('utf-8'))
        if path.path=='/api/image':
            card_id=q.get('id',[''])[0]
            if not re.fullmatch(r'[0-9]{1,10}',card_id or ''):return self.send(400,b'{"error":"bad card id"}')
            try:
                data=self.get_remote(f'https://cdn.233.momobako.com/ygopro/pics/{card_id}.jpg',f'image_{card_id}.jpg',90*86400)
                return self.send(200,data,'image/jpeg')
            except Exception as e:return self.send(502,json.dumps({'error':str(e)},ensure_ascii=False).encode())
        self.send(404,b'Not found','text/plain')

if __name__=='__main__':
    print('YGO TYPE 已啟動: http://127.0.0.1:8765')
    print('不需要安裝任何 Python 套件。按 Ctrl+C 關閉。')
    try:
        srv=ThreadingHTTPServer((HOST,PORT),Handler)
        webbrowser.open(f'http://{HOST}:{PORT}/')
        srv.serve_forever()
    except KeyboardInterrupt: print('\n已停止。')
    except OSError as exc: print(f'無法啟動：{exc}')
