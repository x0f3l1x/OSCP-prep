# ReconLab — panel web local

Interfaz de navegador para las tres herramientas Python de la práctica: enumeración DNS/WHOIS y TCP, análisis de cabeceras HTTP y servidor de captura User-Agent.

## Instalar y ejecutar en Fedora

```bash
sudo dnf install -y python3 whois
cd ~/Desktop/recon_web
python3 dashboard.py
```

Abre **http://127.0.0.1:8766** en Chrome o Firefox. Mantén abierta la terminal mientras utilizas el panel. Pulsa Ctrl+C para detenerlo.

No se necesitan paquetes Python adicionales. Si el puerto 8766 está ocupado, detén el proceso que lo utiliza. El servidor de laboratorio utiliza el puerto 8000 y debe estar libre para que el botón Iniciar funcione.

## Uso

1. **Reconocimiento:** escribe un dominio para DNS/WHOIS. Para TCP, activa la casilla y confirma autorización. Usa `127.0.0.1` y puerto `8000` con el servidor de laboratorio.
2. **Cabeceras HTTP:** inicia el servidor de laboratorio y analiza `http://127.0.0.1:8000`.
3. **Servidor & User-Agent:** pulsa Iniciar, visita `http://127.0.0.1:8000` y actualiza los registros. Para probar valores personalizados: `curl -A 'OSCP-Lab/1.0' http://127.0.0.1:8000`.
4. Descarga los resultados JSON desde el panel. Los scripts también escriben `enumeracion.json`, `cabeceras.json` y `peticiones.jsonl` en esta carpeta.

## Notas técnicas y seguridad

- El panel y el servidor de laboratorio escuchan exclusivamente en `127.0.0.1`.
- El panel ejecuta los scripts mediante `subprocess` sin shell, con límites de tiempo y validación de entradas.
- La enumeración TCP debe limitarse a equipos propios o con autorización expresa.
- Las cabeceras ausentes no prueban por sí solas una vulnerabilidad; HSTS solo es relevante sobre HTTPS.
- WHOIS tradicional puede no ofrecer resultados para dominios `.es`.
- No expongas el panel a Internet ni lo uses como servicio multiusuario. Es una herramienta educativa local.
