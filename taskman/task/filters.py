import django_filters as f

from . import models as m


class TaskFilter(f.FilterSet):
    commentbody = f.MethodFilter(action='get_qs_by_comment', label='Комментарий')

    class Meta:
        model = m.Task
        fields = {
            'subject': ['icontains'],
            'desc': ['icontains'],
        }

    def get_qs_by_comment(self, queryset, value):
        return queryset.filter(pk__in=[comment.task.id for comment in m.Comment.objects.filter(body__icontains=value)])
