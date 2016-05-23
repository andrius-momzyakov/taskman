import mimetypes
import urllib

from django.shortcuts import render, redirect, HttpResponse, render_to_response, RequestContext
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, View
from django.core.files import File
from django.core.context_processors import csrf
import django.forms as forms
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse



from .models import Task, Comment, Attachment
from django.conf import settings

# Create your views here.


class TaskList(ListView):
    model = Task
    paginate_by = 20


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
        fields = ['type', 'project', 'module', 'subject', 'desc', 'executor', 'parent', ]

@method_decorator(login_required, name='dispatch')
class NewTask(View):
    template = 'task_create_form.html'

    def get(self, request, *args, **kwargs):
        form = NewTaskForm()
        return render_to_response(template_name=self.template, context={'form':form},
                                  context_instance=RequestContext(request, {}
                                                                  .update(csrf(request))))


    def post(self, request, *args, **kwargs):
        form = NewTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            return redirect(reverse('detail', args=[task.id,]))
        return render_to_response(template_name=self.template, context={'form':form},
                                  context_instance=RequestContext(request, {}
                                                                  .update(csrf(request))))


'''
class NewTask(CreateView):
    model = Task
    template_name_suffix = '_create_form'
    fields = ['type', 'project', 'module', 'subject', 'desc', 'executor', 'created_by',
              'created', 'parent', ]
'''


@method_decorator(login_required, name='dispatch')
class EditTask(UpdateView):
    model = Task
    slug_field = 'id'
    fields = ['type', 'project', 'module', 'subject', 'desc', 'executor', 'closed',
              'close_reason', 'parent', ]
    template_name_suffix = '_update_form'

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
    return redirect('/task/page1/')


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
    response['Content-Disposition'] = 'attachment; filename=' + \
                                      urllib.parse.quote(name.encode('utf-8'))
    return response
