from datetime import date

from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.reverse import reverse

from .models import Alerts, Problems, Levels


User = get_user_model()


class AlertsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerts
        fields = ('alert_id', 'trigger', 'host', 'datetime', 'message','status' )



class ProblemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problems
        fields = ('problem_name', 'level', )



class LevelsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Levels
        fields = ("level_id")

