import mimetypes
import urllib

from datetime import datetime

from django.shortcuts import render, redirect, HttpResponse, render_to_response, RequestContext, \
    get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, View
from django.core.files import File
from django.core.context_processors import csrf
import django.forms as forms
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
import django.db as db
from django.db.models import Q
from django.db.models.expressions import F

from .models import Task, Comment, Attachment, TaskType, TaskUserPriority, TaskView
from django.conf import settings


# Create your views here.

class TaskList(ListView):
    # request.GET.urlencode()
    model = TaskView
    paginate_by = 20
    template_name = 'taskview_list.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect(reverse('anonymous_home', args=[1, ]) + request.GET.urlencode())
        #return HttpResponse(request.GET.urlencode())
        return super(TaskList, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TaskList, self).get_context_data(**kwargs)
        get_qry = self.request.GET.urlencode()
        status_qry_val = self.request.GET.get('status_in')
        qs = None
        if status_qry_val == 'open':
            qs = TaskView.objects.filter(~Q(status=Task.CLOSED))
        elif status_qry_val == 'new':
            qs = TaskView.objects.filter(Q(status=Task.NEW))
        elif status_qry_val == 'accepted':
            qs = TaskView.objects.filter(Q(status=Task.ACCEPTED))
        elif status_qry_val == 'closed':
            qs = TaskView.objects.filter(Q(status=Task.CLOSED))
        else:
            qs = TaskView.objects.all()
        pag, context['page_obj'], context['object_list'], is_pag = self.paginate_queryset(qs, self.paginate_by)
        if get_qry:
            context['get_qry'] = '?' + get_qry
        return context


class AnonymousTaskList(TaskList):
    '''
    Task list for anonymous user
    '''
    model = Task
    template_name = 'taskview_list.html'

    def dispatch(self, request, *args, **kwargs):
        return super(TaskList, self).dispatch(request, *args, **kwargs)


class TaskDetail(DetailView):
    model = Task
    slug_field = 'id'

    def get_context_data(self, **kwargs):
        context = super(TaskDetail, self).get_context_data(**kwargs)
        attachments = Attachment.objects.filter(task=self.object)
        comments = Comment.objects.filter(task=self.object)
        children = Task.objects.filter(parent=self.object)
        context['attachments'] = attachments
        context['comments'] = comments
        context['children'] = children
        return context


class NewTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['type', 'project', 'module', 'subject', 'desc', 'executor', 'deadline_date', 'status', 'parent', ]


@method_decorator(login_required, name='dispatch')
class NewTask(View):
    template = 'task_create_form.html'

    def get(self, request, *args, **kwargs):
        tasktype = None
        try:
            tasktype = TaskType.objects.get(short_typename='TASK')
            form = NewTaskForm(initial={'type': tasktype, 'status': Task.NEW})
        except TaskType.DoesNotExist:
            form = NewTaskForm(initial={'type': tasktype, 'status': 'NEW'})
        return render_to_response(template_name=self.template, context={'form': form},
                                  context_instance=RequestContext(request, {}
                                                                  .update(csrf(request))))

    def post(self, request, *args, **kwargs):
        form = NewTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            Task.check_status(task, request)
            task.save()
            return redirect(reverse('detail', args=[task.id, ]))
        return render_to_response(template_name=self.template, context={'form': form},
                                  context_instance=RequestContext(request, {}
                                                                  .update(csrf(request))))


class EditTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['type', 'project', 'module', 'subject', 'desc', 'executor', 'deadline_date', 'status',
                  'closed', 'close_reason', 'parent']


@method_decorator(login_required, name='dispatch')
class EditTask(View):
    template = 'task_update_form.html'

    def add_context(self, task, context):
        context['object'] = task
        attachments = Attachment.objects.filter(task=task)
        comments = Comment.objects.filter(task=task)
        context['attachments'] = attachments
        context['comments'] = comments
        return

    def get(self, request, task_id, *args, **kwargs):
        task = get_object_or_404(Task, pk=task_id)
        form = EditTaskForm(instance=task)
        context = {'form': form}
        self.add_context(task, context)
        return render_to_response(template_name=self.template, context=context,
                                  context_instance=RequestContext(request, {}
                                                                  .update(csrf(request))))

    def post(self, request, task_id, *args, **kwargs):
        task = get_object_or_404(Task, pk=task_id)
        form = EditTaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save(commit=False)
            Task.check_status(task, request)
            task.save()
            return redirect(reverse('detail', args=[task.id, ]))
        context = {'form': form}
        self.add_context(task, context)
        return render_to_response(template_name=self.template, context=context,
                                  context_instance=RequestContext(request, {}
                                                                  .update(csrf(request))))


class NewAttachmentForm(forms.Form):
    task = forms.IntegerField()
    file = forms.FileField()


@method_decorator(login_required, name='dispatch')
class NewAttachment(View):
    def post(self, request, *args, **kwargs):
        form = NewAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            att = Attachment(task=Task.objects.get(pk=int(form.cleaned_data['task']))
                             , file=request.FILES['file'])
            att.save()
            return redirect(reverse('detail', args=[form.cleaned_data['task'], ]))
        return HttpResponse('Неправильно введены данные.')


class NewCommentForm(forms.Form):
    task = forms.IntegerField()
    body = forms.CharField(widget=forms.Textarea)


@method_decorator(login_required, name='dispatch')
class NewComment(View):
    def post(self, request, *args, **kwargs):
        form = NewCommentForm(request.POST)

        if form.is_valid():
            comment = Comment()
            comment.author = request.user  # form.cleaned_data['author']
            comment.body = form.cleaned_data['body']
            comment.task = Task.objects.get(pk=int(form.cleaned_data['task']))
            comment.save()
            return redirect(reverse('detail', args=[form.cleaned_data['task'], ]))
        return HttpResponse('Неправильно введены данные.')


#@login_required
def root(request):
    if not request.user.is_authenticated():
        return redirect(reverse('anonymous_home', args=[1, ])  + '?status_in=open')
    return redirect(reverse('home', args=[1, ])  + '?status_in=open')


@login_required
def serve_file(request, name):
    ctype = mimetypes.guess_type(name)
    f = None
    f = open(settings.MEDIA_ROOT + name, 'rb')
    if not f:
        return HttpResponse('Файл не найден или не существует.')
    data = File(f)
    response = HttpResponse(data, content_type=ctype)
    # todo: Сделать на Streaming response
    response['Content-Disposition'] = 'attachment; filename=' + \
                                      urllib.parse.quote(name.encode('utf-8'))
    return response


@login_required
def update_task_priority(request, task_id=None, increase=None):
    t = get_object_or_404(Task, pk=task_id)
    u = request.user
    TaskUserPriority.objects.filter(task=t, user=u).delete()
    new_priority = TaskUserPriority(task=t, user=u)
    new_priority.save()
    if increase == 'down':
        new_priority.priority = -1 * F('id')
    else:
        new_priority.priority = F('id')
    new_priority.save()
    return redirect(reverse('home', args=[1, ]) + '?' + request.GET.urlencode())
