
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bug_tracking_tool.settings')

app = Celery('bug_tracking_tool')


app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'

# Define periodic tasks using Celery Beat
app.conf.beat_schedule = {
    'notify-unresolved-bugs': {
        'task': 'accounts.tasks.notify_unresolved_bugs',  # Task to execute
        'schedule': crontab(hour=14, minute=47),  # Daily at this time
    },
}

app.autodiscover_tasks()
