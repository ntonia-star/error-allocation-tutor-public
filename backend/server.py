"""Single-process, bounded HTTP service. Only explicitly allowlisted public files are served."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import json, mimetypes, os, threading, time
from backend import config
from backend.agent import ask, AgentError
from backend.retrieval import CORPUS
from backend.calculator import execute

WEB=config.ROOT/'frontend'
LIMIT=int(os.getenv('RATE_LIMIT_PER_HOUR','40'))
MODEL_SLOTS=threading.BoundedSemaphore(int(os.getenv('MAX_MODEL_CONCURRENCY','3')))
RATE_LOCK=threading.Lock(); RATES={}
EXERCISES=json.loads((config.ROOT/'knowledge_base/structured_knowledge/exercises.json').read_text(encoding='utf-8'))

class Server(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,*args,**kwargs):
        self.slots=threading.BoundedSemaphore(32)
        super().__init__(*args,**kwargs)
    def process_request(self,request,client_address):
        if not self.slots.acquire(blocking=False): request.close(); return
        try: super().process_request(request,client_address)
        except Exception: self.slots.release(); raise
    def process_request_thread(self,*args):
        try: super().process_request_thread(*args)
        finally: self.slots.release()

class Handler(BaseHTTPRequestHandler):
    server_version='CourseAssistant'
    def setup(self):
        super().setup(); self.connection.settimeout(120)
    def log_message(self,format,*args): pass # no user questions, keys, or upstream bodies in logs
    def respond(self,code,data,ctype='application/json; charset=utf-8'):
        if not isinstance(data,bytes): data=json.dumps(data,ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(data)))
        self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.send_header('Cache-Control','no-store' if ctype.startswith('application/json') else 'no-cache')
        self.end_headers()
        try: self.wfile.write(data)
        except (BrokenPipeError,ConnectionResetError): pass
    def file(self,path):
        if not path.is_file(): return self.respond(404,{'error':'文件不存在'})
        self.respond(200,path.read_bytes(),mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
    def do_GET(self):
        path=urlparse(self.path)
        if path.path=='/api/health': return self.respond(200,{'ok':True,'model_configured':bool(config.API_KEY),'chunks':len(CORPUS)})
        if path.path=='/api/knowledge': return self.respond(200,{'items':CORPUS})
        if path.path=='/api/exercises': return self.respond(200,{'items':EXERCISES})
        if path.path in ('/api/source/book','/api/source/slides'):
            try: page=int(parse_qs(path.query).get('page',['0'])[0])
            except ValueError: return self.respond(400,{'error':'页码无效'})
            kind=path.path.rsplit('/',1)[-1]
            expected_kind='教材' if kind=='book' else '课件'
            allowed={s.get('pdf_page') for c in CORPUS for s in c.get('sources',[]) if s.get('kind')==expected_kind}
            if page not in allowed: return self.respond(404,{'error':'未收录此来源页'})
            return self.file(config.ROOT/'knowledge_base/pages'/f'{kind}-{page}.png')
        relative='index.html' if path.path=='/' else path.path.lstrip('/')
        target=(WEB/relative).resolve()
        if not target.is_relative_to(WEB.resolve()) or target.suffix.lower() not in ('.html','.js','.css','.woff','.woff2','.ttf','.svg','.ico'):
            return self.respond(404,{'error':'页面不存在'})
        return self.file(target)
    def do_POST(self):
        origin=self.headers.get('Origin')
        expected=os.getenv('PUBLIC_ORIGIN','').rstrip('/')
        # TLS is terminated by the hosting proxy. Browsers cannot choose the Host
        # header, so matching this request's host preserves same-origin checks.
        local_origins={f'{scheme}://{self.headers.get("Host")}' for scheme in ('http','https')}
        if origin and origin not in ({expected} if expected else local_origins):
            return self.respond(403,{'error':'请求来源未获允许'})
        if self.headers.get('Content-Type','').split(';')[0]!='application/json': return self.respond(415,{'error':'请求格式不正确'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=40000: return self.respond(413,{'error':'请求内容过长或为空'})
            body=json.loads(self.rfile.read(length))
            if not isinstance(body,dict): raise ValueError()
        except Exception: return self.respond(400,{'error':'请求内容无效'})
        path=urlparse(self.path).path
        if path=='/api/calculate':
            try: return self.respond(200,{'result':execute(body.get('name'),body.get('arguments',{}))})
            except Exception: return self.respond(400,{'error':'请检查输入数值、单位及适用条件。'})
        if path not in ('/api/chat','/api/practice'): return self.respond(404,{'error':'接口不存在'})
        # Ignore client-supplied forwarding headers; use trusted socket identity.
        ip=self.client_address[0]; now=time.monotonic()
        with RATE_LOCK:
            for old in list(RATES):
                if now-RATES[old][0]>=3600: del RATES[old]
            start,count=RATES.get(ip,(now,0))
            if count>=LIMIT: return self.respond(429,{'error':'本小时提问较多，请稍后继续。'})
            RATES[ip]=(start,count+1)
        if not MODEL_SLOTS.acquire(blocking=False): return self.respond(503,{'error':'当前提问较多，请稍后重试。'})
        try:
            level=body.get('level','理解')
            if level not in ('记忆','理解','应用'): raise ValueError('练习层次无效')
            result=ask(body.get('question','请生成一道误差分配练习。'),body.get('mode','standard'),body.get('history',[]),
                       'practice' if path=='/api/practice' else 'chat',level)
            self.respond(200,result)
        except ValueError as exc: self.respond(400,{'error':str(exc)[:150]})
        except AgentError as exc: self.respond(502,{'error':str(exc)})
        except Exception: self.respond(500,{'error':'服务暂时不可用，请稍后重试。'})
        finally: MODEL_SLOTS.release()

def main():
    port=int(os.getenv('PORT','8000')); host=os.getenv('HOST','127.0.0.1')
    print(f'误差分配智能教学助手：http://{host}:{port}',flush=True)
    Server((host,port),Handler).serve_forever()
if __name__=='__main__': main()
