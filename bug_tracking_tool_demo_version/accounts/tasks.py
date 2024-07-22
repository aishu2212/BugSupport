# tasks.py

from celery import shared_task
from django.utils import timezone
from .models import Bug
from django.core.mail import send_mail
from datetime import timedelta
from django.db.models import Q
@shared_task
def notify_unresolved_bugs():
    unresolved_bugs = Bug.objects.exclude(Q(status='Closed') | Q(status='Duplicate')).filter(updated_at__lte=timezone.now() - timedelta(days=10))
    print("Running Task")
    for bug in unresolved_bugs:
        # Send notification emails to assigned_to and raised_by users
        subject = f"Reminder: Unresolved Bug {bug.id}"
        message = f"Bug {bug.id} has been unresolved for more than 10 days. Please take necessary action."
        print("Running")
        send_mail(subject, message, 'softwarebugupdates@gmail.com', [bug.raised_by.email, bug.assigned_to.email])