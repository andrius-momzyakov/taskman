import django_filters as f
from django.db.models import Q
from django.db.models.expressions import F
import django.forms as forms

from . import models as m


class TaskFilter(f.FilterSet):
    OPEN = 'OPEN'
    CLOSED = 'CLOSED'

    FILTER_STATUSES = (
        (OPEN, 'Открыта'),
        (CLOSED, 'Закрыта'),
    )

    subject = f.CharFilter(name='subject', lookup_expr='icontains', label='Задача')
    desc = f.CharFilter(name='desc', lookup_expr='icontains', label='Описание')
    commentbody = f.MethodFilter(action='get_qs_by_comment', label='Комментарий')
    created = f.DateFromToRangeFilter(name='created', label='Дата созд.')
    closed = f.DateFromToRangeFilter(name='closed', label='Дата закр.')
    status = f.MultipleChoiceFilter(choices=m.Task.STATUSES, label='Статус')
    close_reason = f.MultipleChoiceFilter(choices=m.Task.CLOSE_REASONS, label='Тип закр.')

    class Meta:
        model = m.TaskView
        fields = ['subject', 'desc', 'created', 'closed', 'status', 'close_reason']
        widgets = {
            'created': forms.TextInput(attrs={'class': 'dt-picker'}),
            'closed': forms.TextInput(attrs={'class': 'dt-picker'}),
        }

    @staticmethod
    def get_qs_by_comment(queryset, value):
        return queryset.filter(pk__in=[comment.task.id for comment in m.Comment.objects.filter(body__icontains=value)])

