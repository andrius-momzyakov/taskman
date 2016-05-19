import mimetypes
import urllib

from django.shortcuts import render, redirect, HttpResponse
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.core.files import File

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
        attachments = self.object.attachments.all() #Attachment.objects.filter(task=self.object)
        comments = Comment.objects.filter(task=self.object)
        context['attachments'] = attachments
        context['comments'] = comments
        return context


class NewTask(CreateView):
    model = Task
    template_name_suffix = '_create_form'
    fields = ['type', 'project', 'module', 'subject', 'desc', 'executor', 'created_by', 'created', 'parent',
              'attachments']


class EditTask(UpdateView):
    model = Task
    slug_field = 'id'
    fields = ['type', 'project', 'module', 'subject', 'desc', 'executor', 'closed', 'close_reason', 'parent',
              'attachments']
    template_name_suffix = '_update_form'
    slug_field = 'id'

    def get_context_data(self, **kwargs):
        context = super(EditTask, self).get_context_data(**kwargs)
        attachments = self.object.attachments.all()
        comments = Comment.objects.filter(task=self.object)
        context['attachments'] = attachments
        context['comments'] = comments
        return context


class NewComment(CreateView):
    # TODO: Законсить обработчик
    model = Comment
    fields = ['author', 'body']

def new(request):
    pass


def root(request):
    return redirect('/task/')


def edit(request):
    pass

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
