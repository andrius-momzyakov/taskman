import mimetypes
import urllib

from django.shortcuts import render, redirect, HttpResponse
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, View
from django.core.files import File
import django.forms as forms
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


from .models import Task, Comment, Attachment
from django.conf import settings

# Create your views here.


class TaskList(ListView):
    model = Task


class TaskDetail(DetailView):
    model = Task
    slug_field = 'id'

    def get_context_data(self, **kwargs):
        context = super(TaskDetail, self).get_context_data(**kwargs)
        attachments = Attachment.objects.filter(task=self.object)
        comments = Comment.objects.filter(task=self.object)
        context['attachments'] = attachments
        context['comments'] = comments
        return context


@method_decorator(login_required, name='dispatch')
class NewTask(CreateView):
    model = Task
    template_name_suffix = '_create_form'
    fields = ['type', 'project', 'module', 'subject', 'desc', 'executor', 'created_by', 'created', 'parent', ]


@method_decorator(login_required, name='dispatch')
class EditTask(UpdateView):
    model = Task
    slug_field = 'id'
    fields = ['type', 'project', 'module', 'subject', 'desc', 'executor', 'closed', 'close_reason', 'parent', ]
    template_name_suffix = '_update_form'
    slug_field = 'id'

    def get_context_data(self, **kwargs):
        context = super(EditTask, self).get_context_data(**kwargs)
        attachments = Attachment.objects.filter(task=self.object)
        comments = Comment.objects.filter(task=self.object)
        context['attachments'] = attachments
        context['comments'] = comments
        return context


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
            return redirect('/task/detail/{}/'.format(form.cleaned_data['task']))
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
            comment.author = request.user #form.cleaned_data['author']
            comment.body = form.cleaned_data['body']
            comment.task = Task.objects.get(pk=int(form.cleaned_data['task']))
            comment.save()
            return redirect('/task/detail/{}/'.format(form.cleaned_data['task']))
        return HttpResponse('Неправильно введены данные.')


def root(request):
    return redirect('/task/')


def serve_file(request, name):
    ctype = mimetypes.guess_type(name)
    f = None
    f = open(settings.MEDIA_ROOT + name, 'rb')
    #except FileNotFoundError:
    #    return HttpResponse('Файл не найден')
    if not f:
        return HttpResponse('Файл не найден или не существует.')
    data = File(f)
    response = HttpResponse(data, content_type=ctype)
    # todo: Сделать на Streaming response
    #chunk_size = 8192
    #response = StreamingHttpResponse(FileWrapper(f, chunk_size),
    #                       content_type=mimetypes.guess_type(f)[0])
    #response['Content-Length'] = os.path.getsize(the_file)
    response['Content-Disposition'] = 'attachment; filename=' + urllib.parse.quote(name.encode('utf-8'))
    return response
