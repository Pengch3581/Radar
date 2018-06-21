from django.contrib.auth import get_user_model

from rest_framework import authentication, permissions, viewsets, filters,generics

from .forms import AlertsFilter, ProblemsFilter
from .models import Alerts, Problems, Levels
from .serializers import AlertsSerializer, ProblemsSerializer, LevelsSerializer
from rest_framework.response import Response
from rest_framework.decorators import detail_route , list_route
from .tasks import create_model ,delete_model,get_model,get_model_count
import json


User = get_user_model()


class DefaultsMixin(object):
    """Default settings for view authentication, permissions, filtering
     and pagination."""

    authentication_classes = (
        authentication.BasicAuthentication,
        authentication.TokenAuthentication,
    )
    permission_classes = (
        permissions.IsAuthenticated,
    )
    paginate_by = 25
    paginate_by_param = 'page_size'
    max_paginate_by = 100
    filter_backends = (
        # filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
        # filters.PermissionsFilter
    )


class AlertsViewSet(DefaultsMixin,viewsets.ModelViewSet ):
    """API endpoint for listing and creating sprints."""
    queryset = Alerts.objects.order_by('alert_id')
    #
    serializer_class = AlertsSerializer
    # filter_class = AlertsFilter
    search_fields = ('alert_id',)
    # ordering_fields = ('trigger', 'alert_id',)

    @list_route(methods=['post','get','delete'],url_path='getstocklist')
    def get_stocks(self, request, *args, **kwargs):
        if self.request.method == 'POST':
            create_model.delay(request.data)
            return Response({'succss': True, 'msg': '插入成功','data': request.data })
        if self.request.method == 'DELETE':
            delete_model.delay(request.data)
            return Response({'succss': True, 'msg': '删除成功', 'data': request.data})
        if self.request.method == 'GET':
            return Response({'succss': True})

    @list_route(methods=['post', 'get', 'delete'], url_path='getstatus')
    def post_getstatus(self, request, *args, **kwargs):
        if self.request.method == 'POST':
            if request.data['category'] == 2:
                num = get_model(request.data['status'])
                return Response({'succss': True, 'msg': '获取成功', 'data': num})
            elif request.data['category'] == 1:
                num = get_model_count()
                return Response({'succss': True, 'msg': '获取成功', 'data': num})







class ProblemsViewSet(DefaultsMixin, viewsets.ModelViewSet):
    """API endpoint for listing and creating tasks."""

    queryset = Problems.objects.all()
    serializer_class = ProblemsSerializer
    filter_class = ProblemsFilter
    search_fields = ('name', 'description',)
    ordering_fields = ('name', 'order', 'started', 'due', 'completed',)


class LevelsViewSet(DefaultsMixin, viewsets.ReadOnlyModelViewSet):
    """API endpoint for listing users."""

    lookup_field = User.USERNAME_FIELD
    lookup_url_kwarg = User.USERNAME_FIELD
    queryset = User.objects.order_by(User.USERNAME_FIELD)
    serializer_class = LevelsSerializer


search_fields = (User.USERNAME_FIELD,)