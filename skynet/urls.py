from rest_framework.routers import DefaultRouter
from django.conf.urls import url, include
from . import views


router = DefaultRouter()
router.register(r'Alerts', views.AlertsViewSet,base_name='Alerts')
router.register(r'Problems', views.ProblemsViewSet)
router.register(r'Levels', views.LevelsViewSet)


