#!/usr/bin/env python3
"""Panel local para las herramientas educativas de reconocimiento."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import json, subprocess, sys, threading, time, ipaddress, socket, re

BASE=Path(__file__).resolve().parent
HTML=(BASE/'index.html').read_bytes() if (BASE/'index.html').exists() else b''
LOCK=threading.Lock()
LAB=None
PORT=8766

def is_local_host(value):
    return value in ('127.0.0.1','localhost','[::1]')

def lab_running():
    global LAB
    return LAB is not None and LAB.poll() is None

def execute(script, args, timeout):
    cmd=[sys.executable,str(BASE/script),*args]
    try:
        p=subprocess.run(cmd,cwd=BASE,text=True,capture_output=True,timeout=timeout)
    except subprocess.TimeoutExpired:
        return {'error':f'La operación superó {timeout} segundos'}
    if p.returncode:
        return {'error':(p.stderr or p.stdout).strip()[-1400:] or f'Error {p.returncode}'}
    try:
        # Scripts emit JSON and a final confirmation line.
        decoder=json.JSONDecoder()
        return decoder.raw_decode(p.stdout.lstrip())[0]
    except Exception:
        return {'error':'La herramienta devolvió una respuesta no válida','detalle':p.stdout[-800:]}

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def send(self,code,obj):
        data=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.end_headers();self.wfile.write(data)
    def permitted(self):
        host=self.headers.get('Host','').split(':')[0].lower()
        origin=self.headers.get('Origin')
        if not is_local_host(host): return False
        if origin:
            u=urlsplit(origin)
            if u.scheme!='http' or not is_local_host(u.hostname) or u.port!=PORT: return False
        return True
    def do_GET(self):
        if not self.permitted():return self.send(403,{'error':'Acceso local únicamente'})
        if self.path=='/':
            data=(BASE/'index.html').read_bytes()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'")
            self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        elif self.path=='/app.js' or self.path=='/style.css':
            file=BASE/self.path[1:];data=file.read_bytes();mime='text/javascript' if file.suffix=='.js' else 'text/css'
            self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        elif self.path=='/api/status':
            with LOCK: active=lab_running()
            self.send(200,{'running':active,'port':8000})
        elif self.path=='/api/logs':
            path=BASE/'peticiones.jsonl';lines=path.read_text(encoding='utf-8').splitlines()[-100:] if path.exists() else []
            records=[]
            for line in reversed(lines):
                try:records.append(json.loads(line))
                except json.JSONDecodeError:pass
            self.send(200,{'records':records})
        else:self.send(404,{'error':'No encontrado'})
    def do_POST(self):
        global LAB
        if not self.permitted():return self.send(403,{'error':'Acceso local únicamente'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<0 or size>8192:raise ValueError('Tamaño no permitido')
            body=json.loads(self.rfile.read(size))
            if not isinstance(body,dict):raise ValueError('Formato incorrecto')
        except (ValueError,json.JSONDecodeError):return self.send(400,{'error':'Solicitud no válida'})
        if self.path=='/api/enumerate':
            host=str(body.get('host','')).strip()
            if not re.fullmatch(r'[a-zA-Z0-9._:-]{1,253}',host) or host.startswith('-'):
                return self.send(400,{'error':'Introduce un dominio o dirección IP válida'})
            active=body.get('active') is True
            ports=str(body.get('ports','80,443,8000'))
            if active:
                if body.get('authorized') is not True:return self.send(400,{'error':'Debes confirmar que tienes autorización'})
                try:
                    nums={int(p.strip()) for p in ports.split(',')}
                    if not nums or len(nums)>100 or any(not 1<=n<=65535 for n in nums):raise ValueError()
                except ValueError:return self.send(400,{'error':'Puertos inválidos (máximo 100)'})
            args=[host,'--salida',str(BASE/'enumeracion.json')]
            if active:args+=['--activo','--autorizado','--puertos',ports]
            with LOCK:result=execute('enumeracion.py',args,85)
            return self.send(200,result)
        if self.path=='/api/headers':
            url=str(body.get('url','')).strip()
            try:
                parsed=urlsplit(url)
                if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password:raise ValueError()
            except ValueError:return self.send(400,{'error':'Introduce una URL HTTP o HTTPS válida'})
            with LOCK:result=execute('cabeceras.py',[url,'--salida',str(BASE/'cabeceras.json')],20)
            return self.send(200,result)
        if self.path=='/api/lab/start':
            with LOCK:
                if not lab_running():
                    LAB=subprocess.Popen([sys.executable,str(BASE/'servidor.py'),'--host','127.0.0.1','--puerto','8000','--log',str(BASE/'peticiones.jsonl')],cwd=BASE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                running=lab_running()
            return self.send(200,{'running':running,'message':'Servidor iniciado' if running else 'No se pudo iniciar. Comprueba si el puerto 8000 está ocupado.'})
        if self.path=='/api/lab/stop':
            with LOCK:
                if lab_running():
                    LAB.terminate()
                    try:LAB.wait(timeout=3)
                    except subprocess.TimeoutExpired:LAB.kill();LAB.wait()
                running=lab_running()
            return self.send(200,{'running':running})
        return self.send(404,{'error':'No encontrado'})

if __name__=='__main__':
    print(f'Panel web: http://127.0.0.1:{PORT}',flush=True)
    try:ThreadingHTTPServer(('127.0.0.1',PORT),Handler).serve_forever()
    except KeyboardInterrupt:pass
    finally:
        if lab_running():LAB.terminate()
