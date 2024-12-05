mkdir -p /var/log/gunicorn
mkdir -p /home/ubuntu/main/cnext-toolshub/sitemap
touch /var/log/gunicorn/debug.log
#nohup gunicorn cnext_backend.wsgi:application --name cnext --timeout 300 --workers=2 --threads=4 --bind=0.0.0.0:8081 --log-level=error --error-logfile /var/log/gunicorn/debug.log --log-file /var/log/gunicorn/debug.log  --capture-output  &
nohup uwsgi --http :8081 --module cnext_backend.wsgi:application --procname-prefix cnext --workers 4 --threads 2 --harakiri 5000 --max-requests 50000 --http-timeout 5000 --socket myapp.sock --buffer-size 65536 --vacuum --master --enable-threads --logto /var/log/gunicorn/debug.log &
tail -f /var/log/gunicorn/*
