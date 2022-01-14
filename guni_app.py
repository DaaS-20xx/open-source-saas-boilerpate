pidfile = 'app.pid'
worker_tmp_dir = '/dev/shm'
worker_class = 'gthread'
workers = 1
worker_connections = 1000
timeout = 30
keepalive = 2
threads = 2
proc_name = 'application'
bind = '0.0.0.0:5000'
backlog = 2048
accesslog = '-'
errorlog = '-'