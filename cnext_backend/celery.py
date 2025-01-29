import os
from celery import Celery
from django.conf import settings
from datetime import timedelta


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cnext_backend.settings')

app = Celery('cnext_backend')


app.config_from_object('django.conf:settings', namespace='CELERY')


app.autodiscover_tasks()


app.conf.beat_schedule = {
    'generate-url-aliases': {
        'task': 'college_compare.tasks.generate_url_aliases',
        'schedule': timedelta(days=7), 
    },
}


app.conf.update(
    worker_prefetch_multiplier=1,    
    task_acks_late=True,            
    task_reject_on_worker_lost=True, 
    task_serializer='json',         
    result_serializer='json',
    accept_content=['json'],
)