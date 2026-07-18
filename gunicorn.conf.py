import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

bind = os.getenv('GUNICORN_BIND', 'unix:/tmp/tareas.sock')
workers = os.getenv('GUNICORN_WORKERS', '3')
worker_class = 'sync'
timeout = 120
graceful_timeout = 30
keepalive = 5

accesslog = str(BASE_DIR / 'logs' / 'gunicorn_access.log')
errorlog = str(BASE_DIR / 'logs' / 'gunicorn_error.log')
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')

capture_output = True
