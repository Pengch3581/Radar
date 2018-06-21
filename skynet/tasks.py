from celery import task,platforms
import requests
import json
from rest_framework import authentication, permissions, viewsets
from .models import Alerts

platforms.C_FORCE_ROOT = True

@task
def create_model(data):
    if Alerts.objects.filter(alert_id=data['alert_id']):
        Alerts.objects.filter(alert_id=data['alert_id']).update(trigger=data['trigger'],host=data['host'],datetime=data['datetime'],message=data['message'],status=data['status'])
    else:
        Alerts.objects.create(alert_id=data['alert_id'],trigger=data['trigger'], host=data['host'], datetime=data['datetime'], message=data['message'], status=data['status'])


@task
def delete_model(data):
    Alerts.objects.filter(alert_id=data['alert_id']).delete()


def get_model(data):
    num = Alerts.objects.filter(status=data).count()
    return num

def get_model_count():
    num = Alerts.objects.filter().count()
    return num