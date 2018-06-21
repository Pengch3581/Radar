import django_filters

from django.contrib.auth import get_user_model

from .models import Alerts, Problems, Levels

User = get_user_model()


class NullFilter(django_filters.BooleanFilter):
    """Filter on a field set as null or not."""

    def filter(self, qs, value):
        if value is not None:
            return qs.filter(**{'%s__isnull' % self.name: value})
        return qs


class AlertsFilter(django_filters.FilterSet):
    # end_min = django_filters.DateFilter(name='end', lookup_type='gte')
    # end_max = django_filters.DateFilter(name='end', lookup_type='lte')

    class Meta:
        model = Alerts
        fields = ('alert_id', 'trigger', 'host', 'datetime', 'message', 'status')


class ProblemsFilter(django_filters.FilterSet):
    pass
    # backlog = NullFilter(name='sprint')
    #
    # class Meta:
    #     model = Problems
    #     fields = ('sprint', 'status', 'assigned', 'backlog',)
    #
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.filters['assigned'].extra.update(
    #         {'to_field_name': User.USERNAME_FIELD})