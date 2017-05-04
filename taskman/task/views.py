import mimetypes
import urllib
import os
from datetime import datetime

from django.shortcuts import render, redirect, HttpResponse, render_to_response, \
    get_object_or_404
from django.template import RequestContext
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, View
from django.core.files import File
#from django.core.context_processors import csrf
from django.views import csrf
import django.forms as forms
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
import django.db as db
from django.db.models import Q
from django.db.models.expressions import F
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Task, Comment, Attachment, TaskType, TaskUserPriority, TaskView, OnlineSettings, \
                    Project, UserProfile, TaskPriority

from django.conf import settings



# Create your views here.

def check_setting(key, val):
    try:
        setting = OnlineSettings.objects.get(code=key)
        if setting.value == val:
            return True
    except OnlineSettings.DoesNotExist:
        return False


class TaskForeignKeyChoices:
    @classmethod
    def get_created_by_choices(cls):
        # TODO: filter choices depending on user's profile
        return [(user.id, user) for user in User.objects.all()]

    @classmethod
    def get_executor_choices(cls):
        # TODO: filter choices depending on user's profile
        return [(user.id, user) for user in User.objects.all()]

    @classmethod
    def get_project_choices(cls, user=None):
        # TODO: filter choices depending on user's profile
        try:
            profile = UserProfile.objects.get(user=user)
        except:
            profile = None
        qs = None
        if profile:
            if profile.project_can_access.count() > 0:
                qs = profile.project_can_access.all()
        if not qs:
            qs = Project.objects.all()

        return [(project.id, project) for project in qs]

    @classmethod
    def get_type_choices(cls):
        return [(tt.id, tt) for tt in TaskType.objects.all()]


class MyFilterForm(forms.Form):
    def __init__(self, *args, user=None, **kwargs):
        super(MyFilterForm, self).__init__(*args, *kwargs)
        _choices = TaskForeignKeyChoices.get_project_choices(user=user)
        # print(_choices)
        self.fields['project'] = forms.MultipleChoiceField(label="Проект",
                                                           choices=_choices,
                                                           required=False)

    id = forms.IntegerField(label="#", required=False)
    type = forms.MultipleChoiceField(label="Тип задачи", choices=TaskForeignKeyChoices.get_type_choices, required=False)
    subject = forms.CharField(max_length=255, label='Задача', initial='', required=False)
    desc = forms.CharField(max_length=255, label='Описание', initial='', required=False)
    cmmnt = forms.CharField(max_length=255, label='Комментарий', initial='', required=False)
    created_by = forms.MultipleChoiceField(label="Автор", choices=TaskForeignKeyChoices.get_created_by_choices(),
                                           required=False)
    executor = forms.MultipleChoiceField(label="Исполнитель", choices=TaskForeignKeyChoices.get_executor_choices,
                                         required=False)
    project = forms.MultipleChoiceField(label="Проект", choices=TaskForeignKeyChoices.get_project_choices, required = False)
    status = forms.MultipleChoiceField(label="Статус", choices=Task.STATUSES, required=False)
    close_reason = forms.MultipleChoiceField(label="Тип закрытия", choices=Task.CLOSE_REASONS, required=False)
    created1 = forms.DateTimeField(label="Дата создания от", required=False)
    created2 = forms.DateTimeField(label="Дата создания до", required=False)
    dd_date1 = forms.DateTimeField(label="Срок от", required=False)
    dd_date2 = forms.DateTimeField(label="Срок до", required=False)
    closed1 = forms.DateTimeField(label="Дата закрытия от", required=False)
    closed2 = forms.DateTimeField(label="Дата закрытия до", required=False)


class MyFilter:
    def __init__(self, request, qs):
        self.request = request
        self.form = MyFilterForm(request.GET, user=request.user)
        self.qs = qs

    def filter(self):
        if self.form.is_valid():
            _id = self.form.cleaned_data['id']
            _type = self.form.cleaned_data['type']
            _subject = self.form.cleaned_data['subject']
            _desc = self.form.cleaned_data['desc']
            _cmmnt = self.form.cleaned_data['cmmnt']
            _created_by = self.form.cleaned_data['created_by']
            _executor = self.form.cleaned_data['executor']
            _project = self.form.cleaned_data['project']
            _statuses = self.form.cleaned_data['status']
            _close_reason = self.form.cleaned_data['close_reason']
            _created1 = self.form.cleaned_data['created1']
            _created2 = self.form.cleaned_data['created2']
            _dd_date1 = self.form.cleaned_data['dd_date1']
            _dd_date2 = self.form.cleaned_data['dd_date2']
            _closed1 = self.form.cleaned_data['closed1']
            _closed2 = self.form.cleaned_data['closed2']
            _qs = self.qs
            if _id:
                _qs = _qs.filter(id=int(_id))
            if _type:
                _qs = _qs.filter(type__in=[TaskType.objects.get(pk=int(t[0])) for  t in _type])
            if _subject:
                _qs = _qs.filter(subject__icontains=_subject)
            if _desc:
                _qs = _qs.filter(desc__icontains=_desc)
            if _cmmnt:
                _cmmnt_qs = Comment.objects.filter(body__icontains=_cmmnt)
                _qs = _qs.filter(pk__in=[cmmnt.task.id for cmmnt in _cmmnt_qs])
            if _created_by:
                _qs = _qs.filter(created_by__in=[User.objects.get(pk=int(user[0])) for user in _created_by])
            if _executor:
                _qs = _qs.filter(executor__in=[User.objects.get(pk=int(user[0])) for user in _executor])
            if _project:
                _qs = _qs.filter(project__in=[Project.objects.get(pk=int(pr[0])) for pr in _project])
            if _statuses:
                _qs = _qs.filter(status__in=[s for s in _statuses])
            if _close_reason:
                _qs = _qs.filter(close_reason__in=[s for s in _close_reason])
            if _created1:
                _qs = _qs.filter(closed__gte=_created1)
            if _created2:
                _qs = _qs.filter(closed__lte=_created2)
            if _dd_date1:
                _qs = _qs.filter(closed__gte=_dd_date1)
            if _dd_date2:
                _qs = _qs.filter(closed__lte=_dd_date2)
            if _closed1:
                _qs = _qs.filter(closed__gte=_closed1)
            if _closed2:
                _qs = _qs.filter(closed__lte=_closed2)
            return _qs
        return self.qs # на случай ошибки валидации формы


class TaskList(ListView):
    # request.GET.urlencode()
    model = TaskView
    paginate_by = 20
    template_name = 'taskview_list.html'

    def dispatch(self, request, *args, **kwargs):

        if not request.user.is_authenticated():
            if check_setting('VEIL_LIST', 'Y'):
                return redirect(reverse('login', ) + '?next=' + request.path)
            return redirect(reverse('anonymous_home', args=[1, ]) + request.GET.urlencode())

        if request.GET.get('gotolast'):

            if request.GET.get('gotolast').upper()=='YES':
                status_qry_val = self.request.GET.get('status_in')
                qs = self.get_filtered_qs(status_qry_val=status_qry_val)
                pag, page_obj, object_list, is_pag = self.paginate_queryset(qs, self.paginate_by)
                last_page = pag.num_pages
                qry = ''
                if status_qry_val:
                    qry = '?status_in={}'.format(status_qry_val)
                return redirect(reverse('home', args=[last_page, ]) + qry)

            if request.GET:
                get_qry = request.GET.urlencode()
                return HttpResponse(get_qry)
                return redirect(reverse('home', args=[1,]) + '?' + get_qry)

        current_page_num = int(kwargs.get('page', None))
        get_qry = self.request.GET.urlencode()
        if (not current_page_num is None) and (current_page_num != 1):
            my_filter = MyFilter(self.request, self.get_filtered_qs()).filter()
            paginator_obj = Paginator(my_filter, self.paginate_by)
            if paginator_obj.num_pages < current_page_num:
                current_page_num = paginator_obj.num_pages
                return redirect(reverse('home', args=[current_page_num, ]) + '?' + get_qry)

        return super(TaskList, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TaskList, self).get_context_data(**kwargs)
        get_qry = self.request.GET.urlencode()
        status_qry_val = self.request.GET.get('status_in')
        qs = self.get_filtered_qs(status_qry_val=status_qry_val)
        filter = MyFilter(self.request, qs)
        pag, context['page_obj'], context['object_list'], is_pag = self.paginate_queryset(filter.filter(), self.paginate_by)
        context['page_numbers'] = map(lambda x: x + 1, list(range(pag.num_pages)))
        context['filter_form'] = MyFilterForm(self.request.GET, user=self.request.user)  # filter.form
        if get_qry:
            context['get_qry'] = '?' + get_qry
        return context

    def get_filtered_qs(self, status_qry_val=None):
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

        if self.request.user.is_authenticated():
            uid = self.request.user.id
            # filter(Q(prty_user_id=self.request.user)|Q(prty_user_id__isnull=True))
            qs = qs.filter(Q(private=False) | Q(private=True, created_by=self.request.user))
            try:
                profile = UserProfile.objects.get(user=self.request.user)
            except:
                profile = None
            if profile and profile.project_can_access.count() > 0:
                qs = qs.filter(Q(project__in=[p for p in profile.project_can_access.all()]))
        else:
            qs = qs.filter(Q(private=False))

        return qs


class AnonymousTaskList(TaskList):
    '''
    Task list for anonymous user
    '''
    model = Task
    template_name = 'taskview_list.html'

    def dispatch(self, request, *args, **kwargs):
        if check_setting('VEIL_LIST', 'Y'):
            return redirect(reverse('login', ) + '?next=' + request.path)
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
        if self.request.GET.get('gotolast'):
            if self.request.GET.get('gotolast').upper() == 'YES':
                context['gotolast4open'] = '&gotolast=yes'
                context['gotolast4all'] = '?gotolast=yes'
        return context

    def dispatch(self, request, *args, **kwargs):
        task = self.get_object()
        if task.private and task.created_by != request.user:
            return throw_error(request, 'У вас нет прав на просмотр данной задачи. <a href="{}">Назад</a>'
                                .format(request.META.get('HTTP_REFERER', '') + request.META.get('QUERY_STRING', '')))
        return super(TaskDetail, self).dispatch(request, *args, **kwargs)


class NewTaskForm(forms.ModelForm):
    # TODO:
    def __init__(self, *args, user=None, status=Task.NEW, type_id=None, **kwargs):
        super().__init__(*args, *kwargs)
        project_required = False
        try:
            profile = UserProfile.objects.get(user=user)
            if profile.project_can_access.count() > 0:
                qs = profile.project_can_access.all()
                project_required = True
            else:
                qs = Project.objects.all()
        except:
            qs = Project.objects.all()
        self.fields['type'].widget.selected = type_id
        self.fields['status'].initial = status
        if project_required:
            self.fields['project'].queryset = qs
            self.fields['project'].required = True

    class Meta:
        model = Task
        fields = ['type', 'project', 'module', 'subject', 'desc', 'executor', 'deadline_date', 'private',
                  'status', 'parent', ]

        widgets = {
            'deadline_date': forms.TextInput(attrs={'class': 'dt-picker'}),
            'subject': forms.TextInput(attrs={'size': '80'}),
            'desc': forms.Textarea(attrs={'cols': '80'}),
        }


@method_decorator(login_required, name='dispatch')
class NewTask(View):
    template = 'task_create_form.html'

    def get(self, request, *args, **kwargs):
        tasktype = None
        try:
            tasktype = TaskType.objects.get(short_typename='TASK')
            form = NewTaskForm(user=request.user, status=Task.NEW, type_id=tasktype.id)
        except TaskType.DoesNotExist:
            form = NewTaskForm(user=request.user, status=Task.NEW, type_id=tasktype.id)
        return render_to_response(template_name=self.template, context={'form': form},
                                  context_instance=RequestContext(request, {}
                                                                  .update(csrf(request))))

    def post(self, request, *args, **kwargs):
        form = NewTaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            Task.check_status(task, request)
            task.save()
            update_task_priority(request, task_id=task.id, increase='down')
            return redirect(reverse('detail', args=[task.id, ]) + '?gotolast=yes')
        return render_to_response(template_name=self.template, context={'form': form},
                                  context_instance=RequestContext(request, {}
                                                                  .update(csrf(request))))


class EditTaskForm(forms.ModelForm):
    # TODO: limit project choice when needed
    file = forms.FileField(label='Файл', required=False)
    comment = forms.CharField(label='Комментарий', widget=forms.Textarea(attrs={'cols': 80}), required=False)

    class Meta:
        model = Task
        fields = ['type', 'project', 'module', 'subject', 'desc', 'executor', 'deadline_date', 'private', 'status',
                  'closed', 'close_reason', 'parent']
        widgets = {
            'closed': forms.TextInput(attrs={'class': 'dt-picker'}),
            'deadline_date': forms.TextInput(attrs={'class': 'dt-picker'}),
            'subject': forms.TextInput(attrs={'size': '80'}),
            'desc': forms.Textarea(attrs={'cols': '80'}),
        }

    def save(self, commit=True, user=None):

        def save_comment(task_instance, body, author=user):
            cmmt = Comment(task=task_instance, body=body, author=user)
            cmmt.save()

        try:
            comment_message = 'Пользователь {} внес правки:\n'.format(user)
            changes_done = False
            saved_task = Task.objects.get(pk=self.instance.id)
            for attribute in ['type', 'subject', 'desc', 'executor', 'private', 'status', 'close_reason',
                              'deadline_date', 'project', 'parent', 'closed']:
                if getattr(saved_task, attribute) != self.cleaned_data[attribute]:
                    val1 = ''
                    val2 = ''
                    if attribute == 'status':
                        val1 = dict(Task.STATUSES).get(getattr(saved_task, attribute), '-')
                        val2 = dict(Task.STATUSES).get(self.cleaned_data[attribute], '-')
                    elif attribute == 'close_reason':
                        val1 = dict(Task.CLOSE_REASONS).get(getattr(saved_task, attribute), '-')
                        val2 = dict(Task.CLOSE_REASONS).get(self.cleaned_data[attribute], '-')
                    else:
                        val1 = getattr(saved_task, attribute)
                        val2 = self.cleaned_data[attribute]
                        if val1 is None:
                            val1 = ''
                        if val2 is None:
                            val2 = ''
                    comment_message += '{} изменен(а) с "{}" на "{}"\n'\
                                       .format(self.instance._meta.get_field_by_name(attribute)[0].verbose_name,
                                               val1,
                                               val2)
                    changes_done = True
            if changes_done:
                save_comment(task_instance=self.instance,
                             body=comment_message, author=user)
        except Task.DoesNotExist:
            pass
        if self.cleaned_data['file']:
            att = Attachment(task=Task.objects.get(pk=self.instance.id),
                             file=self.cleaned_data['file'])
            att.save()
            save_comment(task_instance=self.instance,
                         body='Пользователь {} добавил вложение "{}"'.format(user, self.cleaned_data['file']),
                         author=user)
        if self.cleaned_data['comment']:
            save_comment(task_instance=self.instance,
                         body=self.cleaned_data['comment'], author=user )
        return super(EditTaskForm, self).save(commit=commit)


class EditTaskFormGuest(EditTaskForm):
    # TODO: limit project choice when needed
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
        delete_attachment_allowed = False
        if task.created_by != request.user:
            # без поля private
            form = EditTaskFormGuest(instance=task)
        else:
            form = EditTaskForm(instance=task)
            delete_attachment_allowed = True
        context = {'form': form}
        if delete_attachment_allowed or request.user.is_superuser:
            context.update({'delete_attachment_allowed': True})
        context.update({'STATIC_URL':settings.STATIC_URL})
        self.add_context(task, context)
        return render_to_response(template_name=self.template, context=context,
                                  context_instance=RequestContext(request, {}
                                                                  .update(csrf(request))))

    def post(self, request, task_id, *args, **kwargs):
        task = get_object_or_404(Task, pk=task_id)
        if task.created_by != request.user:
            # без поля private
            form = EditTaskForm(request.POST, request.FILES, instance=task)
        else:
            form = EditTaskForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            task = form.save(commit=False, user=request.user)
            Task.check_status(task, request)
            task.save()
            return redirect(reverse('detail', args=[task.id, ]))
        context = {'form': form}
        self.add_context(task, context)
        return render_to_response(template_name=self.template, context=context,
                                  context_instance=RequestContext(request, {}
                                                                  .update(csrf(request))))

    def dispatch(self, request, task_id, *args, **kwargs):
        task = get_object_or_404(Task, pk=task_id)
        if task.private and task.created_by != request.user:
            return throw_error(request, 'У вас нет прав на редактирование данной задачи. <a href="{}">Назад</a>'
                                .format(request.META.get('HTTP_REFERER', '') + request.META.get('QUERY_STRING', '')))
        return super(EditTask, self).dispatch(request, task_id, *args, **kwargs)


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
        return throw_error(request, 'Неправильно введены данные о вложении.')


def delete_task_attachment(request, a_id):
    '''
    deletes task attachment
    :param request:
    :param a_id: attachment id
    :return:
    '''
    obj_id = int(a_id)
    obj = Attachment.objects.get(pk=obj_id)
    task = obj.task
    if request.user.is_superuser or request.user == task.created_by:
        ospath = settings.MEDIA_ROOT
        try:
            os.remove(ospath + obj.file.name)
        except OSError:
            try:
                os.remove(ospath + obj.file.name[1:])
            except FileNotFoundError:
                pass
        obj.delete()
        body = 'Пользователь {} удалил вложение "{}".'.format(request.user, obj.file.name)
        commnt = Comment(task=task, body=body, author=request.user)
        commnt.save()
    else:
        throw_error(request, 'Удалять вложения может только заявитель (автор) задачи. <a href="{}">Назад</a>'
                                .format(request.META.get('HTTP_REFERER', '') + request.META.get('QUERY_STRING', '')))
    return redirect(reverse('edit', args=[task.id,]))


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
        return throw_error(request, 'Неправильно введен комментарий.')


#@login_required
def root(request):
    if not request.user.is_authenticated():
        if check_setting('VEIL_LIST', 'Y'):
            return redirect(reverse('login', ) + '?next=' + request.path)
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
def update_task_priority_view(request, task_id=None, increase=None):
    update_task_priority(request, task_id=task_id, increase=increase)
    return redirect(reverse('home', args=[1, ]) + '?' + request.GET.urlencode())


def update_task_priority(request, task_id=None, increase=None):
    t = get_object_or_404(Task, pk=task_id)
    # u = request.user
    TaskPriority.objects.filter(task=t).delete()
    new_priority = TaskPriority(task=t)
    new_priority.save()
    print(new_priority.id)
    if increase == 'down':
        new_priority.priority = -1 * F('id')
    else:
        new_priority.priority = F('id')
    new_priority.save()

def throw_error(request, message):
    return ShowErrorMessage().get(request, message=message)

class ShowErrorMessage(View):
    template = 'error.html'
    #message = None

    def get(self, request, message, *args, **kwargs):
        context = {'message': message}
        return render(request, template_name=self.template, context=context)

