import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

bind = os.getenv('GUNICORN_BIND', 'unix:/tmp/tareas.sock')
workers = os.getenv('GUNICORN_WORKERS', '3')
worker_class = 'sync'
timeout = 120
graceful_timeout = 30
keepalive = 5

log_dir = BASE_DIR / 'logs'
log_dir.mkdir(parents=True, exist_ok=True)

accesslog = str(log_dir / 'gunicorn_access.log')
errorlog = str(log_dir / 'gunicorn_error.log')
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')

capture_output = True
