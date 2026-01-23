# Procfile para plataformas PaaS (Digital Ocean, Heroku, etc.)

web: gunicorn autodis_compras.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120
worker: celery -A autodis_compras worker -l info --concurrency=2
beat: celery -A autodis_compras beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
