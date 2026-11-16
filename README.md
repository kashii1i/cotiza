# Cotiza

Sistema web de cotizaciones desarrollado con Python y Flask.

## Requisitos

- Python 3.11+
- Entorno virtual `venv`

## Configuración inicial

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecutar la aplicación

```bash
python run.py
```

La aplicación se levantará en http://127.0.0.1:5000

## Desarrollo local

Para desarrollo local, configura `APP_ENV=development` en `.env`. En este modo se permite
HTTP y, si falta `SECRET_KEY`, se genera una clave temporal para esa ejecución. No uses
esa configuración en producción. En producción, define una clave persistente generada con:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

El primer administrador solo se crea cuando la base de datos no contiene usuarios y están
definidas `ADMIN_USERNAME` y `ADMIN_PASSWORD` en el entorno.

Flask-Limiter usa memoria local si no se configura `RATELIMIT_STORAGE_URI`. En despliegues
con varios procesos o instancias, configura un almacenamiento compartido compatible, por
ejemplo Redis, para que el límite de intentos sea común a todos los workers.

## Variables de entorno

Copia `.env.example` a `.env` y ajusta sus valores antes de usar la app en entornos reales.
