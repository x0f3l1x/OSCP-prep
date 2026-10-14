#!/usr/bin/env python3
"""Auditoría informativa de cabeceras HTTP de seguridad."""
import argparse, json, urllib.request, urllib.error, urllib.parse
HEADERS={
 'Strict-Transport-Security':'Exige HTTPS en futuras conexiones',
 'Content-Security-Policy':'Restringe fuentes de contenido y scripts',
 'X-Content-Type-Options':'Evita interpretar tipos MIME inesperados',
 'Referrer-Policy':'Controla la información enviada en Referer',
 'Permissions-Policy':'Limita funciones del navegador',
 'X-Frame-Options':'Controla el uso de marcos (alternativa: CSP frame-ancestors)',
 'Cross-Origin-Opener-Policy':'Aísla contextos de navegación',
 'Cross-Origin-Resource-Policy':'Controla cargas de recursos entre orígenes',
}
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

def main():
 p=argparse.ArgumentParser(description='Comprobación de cabeceras de seguridad')
 p.add_argument('url');p.add_argument('--salida',default='cabeceras.json');a=p.parse_args()
 u=urllib.parse.urlsplit(a.url)
 if u.scheme not in ('http','https') or not u.hostname or u.username or u.password: p.error('URL HTTP(S) válida requerida')
 req=urllib.request.Request(a.url,headers={'User-Agent':'PracticaSeguridad/1.0'},method='GET')
 opener=urllib.request.build_opener(NoRedirect)
 try:
  with opener.open(req,timeout=8) as r: status=r.status;h=dict(r.headers.items())
 except urllib.error.HTTPError as e: status=e.code;h=dict(e.headers.items())
 except (urllib.error.URLError,TimeoutError) as e: p.error(str(e))
 lower={k.lower():v for k,v in h.items()}
 checks={k:{'presente':k.lower() in lower,'valor':lower.get(k.lower()),'funcion':v} for k,v in HEADERS.items()}
 result={'url':a.url,'status':status,'cabeceras_recibidas':h,'seguridad':checks,'nota':'La presencia no garantiza una configuración segura. HSTS solo tiene efecto por HTTPS; CSP frame-ancestors puede sustituir X-Frame-Options.'}
 print(json.dumps(result,indent=2,ensure_ascii=False))
 with open(a.salida,'w',encoding='utf-8') as f:json.dump(result,f,indent=2,ensure_ascii=False)
 print('Guardado en',a.salida)
if __name__=='__main__':main()
