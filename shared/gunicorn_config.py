"""
Shared Gunicorn configuration template for all Heart Portal components
Each component can import and customize as needed
"""

import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"

# Worker processes
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeouts
timeout = int(os.getenv('GUNICORN_TIMEOUT', '120'))  # Increased from default 30s
graceful_timeout = 30
keepalive = 5

# Logging
errorlog = '-'  # Log to stdout for systemd
accesslog = '-'  # Log to stdout for systemd
loglevel = os.getenv('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = os.getenv('SERVICE_NAME', 'heart-portal')

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
keyfile = os.getenv('SSL_KEYFILE', None)
certfile = os.getenv('SSL_CERTFILE', None)
