#!/usr/bin/env python3
"""Enumeración DNS/WHOIS y comprobación TCP en objetivos autorizados."""
import argparse
import datetime
import ipaddress
import json
import shutil
import socket
import subprocess


def consultar_whois(host):
    """Devuelve información WHOIS sin confundir errores con falta de instalación."""
    if not shutil.which('whois'):
        return {'whois_estado': 'no_instalado', 'whois_resumen': 'Instala whois con sudo dnf install whois'}
    # www es un nombre de host, no el dominio registrado; se retira para el caso habitual.
    dominio = host[4:] if host.lower().startswith('www.') else host
    try:
        respuesta = subprocess.run(
            ['whois', dominio], capture_output=True, text=True,
            timeout=15, check=False
        )
    except subprocess.TimeoutExpired:
        return {'whois_dominio': dominio, 'whois_estado': 'timeout',
                'whois_resumen': 'La consulta WHOIS excedió los 15 segundos.'}
    except OSError as exc:
        return {'whois_dominio': dominio, 'whois_estado': 'error',
                'whois_resumen': f'No se pudo ejecutar WHOIS: {exc}'}

    contenido = '\n'.join(x for x in (respuesta.stdout.strip(), respuesta.stderr.strip()) if x)
    datos = {'whois_dominio': dominio, 'whois_codigo_salida': respuesta.returncode}
    if 'This TLD has no whois server' in contenido:
        datos.update(whois_estado='sin_servidor_whois',
                     whois_resumen=contenido[:4000])
        if dominio.lower().endswith('.es'):
            datos['whois_url'] = 'https://www.dominios.es/en'
    elif contenido:
        datos.update(whois_estado='respuesta' if respuesta.returncode == 0 else 'error_consulta',
                     whois_resumen=contenido[:4000])
    else:
        datos.update(whois_estado='sin_respuesta', whois_resumen='WHOIS no devolvió información.')
    return datos


def main():
    p = argparse.ArgumentParser(description='Enumeración DNS/WHOIS y TCP autorizada')
    p.add_argument('objetivo', help='Dominio o IP objetivo')
    p.add_argument('--activo', action='store_true', help='Comprobar puertos TCP')
    p.add_argument('--autorizado', action='store_true', help='Confirmar autorización para el escaneo')
    p.add_argument('--puertos', default='21,22,25,53,80,110,143,443,8080,8443')
    p.add_argument('--salida', default='enumeracion.json')
    a = p.parse_args()
    if a.activo and not a.autorizado:
        p.error('Para escanear usa --autorizado únicamente si tienes permiso')
    host = a.objetivo.strip()
    if not host or any(c in host for c in '/:@ ') or host.startswith('-'):
        p.error('Indica solo un dominio o IP, sin URL ni puerto')
    try:
        ips = sorted({info[4][0] for info in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)})
    except socket.gaierror as exc:
        p.error(f'No se pudo resolver: {exc}')
    resultado = {
        'objetivo': host,
        'fecha_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'pasiva': {'ips': ips}, 'activa': []
    }
    try:
        ipaddress.ip_address(host)
    except ValueError:
        resultado['pasiva'].update(consultar_whois(host))
    if a.activo:
        try:
            puertos = sorted({int(x.strip()) for x in a.puertos.split(',')})
        except ValueError:
            p.error('Los puertos deben ser números separados por comas')
        if not puertos or len(puertos) > 100 or any(not 1 <= n <= 65535 for n in puertos):
            p.error('Indica entre 1 y 100 puertos válidos (1-65535)')
        for ip in ips[:4]:
            for puerto in puertos:
                try:
                    with socket.create_connection((ip, puerto), timeout=0.6):
                        resultado['activa'].append({'ip': ip, 'puerto': puerto, 'estado': 'abierto'})
                except OSError:
                    pass
    with open(a.salida, 'w', encoding='utf-8') as archivo:
        json.dump(resultado, archivo, indent=2, ensure_ascii=False)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    print(f'Guardado en {a.salida}')


if __name__ == '__main__':
    main()
