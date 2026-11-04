"""
Gunicorn configuration for Black Eagles Zipline production deployment.
Developed by PL SOFT TECH SOLUTIONS.
"""

import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 60
keepalive = 5

accesslog = "/var/log/black_eagles_zipline/gunicorn_access.log"
errorlog = "/var/log/black_eagles_zipline/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "black_eagles_zipline"
pythonpath = "/var/www/black_eagles_zipline"
