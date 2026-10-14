#!/usr/bin/env python3
"""Servidor HTTP educativo: captura User-Agent y cabeceras de solicitudes recibidas."""
import argparse,datetime,json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  record={'fecha_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'ip_cliente':self.client_address[0],'ruta':self.path,'user_agent':self.headers.get('User-Agent','(no enviado)'),'cabeceras':dict(self.headers.items())}
  print(json.dumps(record,ensure_ascii=False),flush=True)
  with open(self.server.logfile,'a',encoding='utf-8') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
  body=b'<h1>Servidor de practica HTTP</h1><p>Solicitud recibida.</p>'
  self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
 def log_message(self,*args): pass
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--host',default='127.0.0.1');p.add_argument('--puerto',type=int,default=8000);p.add_argument('--log',default='peticiones.jsonl');a=p.parse_args()
 server=ThreadingHTTPServer((a.host,a.puerto),Handler);server.logfile=a.log
 print(f'Servidor: http://{a.host}:{a.puerto} | Log: {a.log} | Ctrl+C para detener',flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
