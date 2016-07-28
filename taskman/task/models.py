from datetime import datetime

from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _



# Create your models here.

class Task(models.Model):
    # Статусы
    NEW = 'NEW'
    ACCEPTED = 'ACCEPTED'
    CLOSED = 'CLOSED'

    STATUSES = (
        (NEW, _('Новая')),
        (ACCEPTED, _('В работе')),
        (CLOSED, _('Закрыта')),
    )

    # Тип закрытия
    COMPLETE = 'CT'
    DUPLICATE = 'DU'
    WONTFIX = 'WF'
    CLOSE_REASONS = (
        (COMPLETE, _('Решено')),
        (DUPLICATE, _('Дублирует существующую')),
        (WONTFIX, _('Отменено')),
    )

    subject = models.CharField(max_length=255, verbose_name=_('Задача'))
    desc = models.TextField(verbose_name=_('Описание'), null=True, blank=True)
    deadline_date = models.DateTimeField(verbose_name=_('Крайний срок'), null=True, blank=True)
    notify_before = models.IntegerField(verbose_name=_('Уведомить за (дней)'), null=True, blank=True)
    created = models.DateTimeField(verbose_name=_('Когда создана'), null=True, blank=True, default=datetime.now)
    created_by = models.ForeignKey(User, related_name='creator', verbose_name=_('Создал'), null=True, blank=True)
    updated = models.DateTimeField(verbose_name=_('Когда изменена'), null=True, blank=True, default=datetime.now)
    updated_by = models.ForeignKey(User, related_name='updater', verbose_name=_('Изменил'), null=True, blank=True)
    status = models.CharField(verbose_name=_('Статус'), max_length=30, choices=STATUSES)
    closed = models.DateTimeField(verbose_name=_('Когда закрыта'), null=True, blank=True)
    close_reason = models.CharField(max_length=2, verbose_name=_('Тип закрытия'), null=True, blank=True,
                                    choices=CLOSE_REASONS)
    parent = models.ForeignKey('self', null=True, blank=True, verbose_name=_('Родительская задача'))
    executor = models.ForeignKey(User, related_name='executor', null=True, blank=True)
    type = models.ForeignKey('TaskType', verbose_name=_('Тип'))
    project = models.ForeignKey('Project', verbose_name=_('Проект'), null=True, blank=True)
    module = models.ForeignKey('Module', verbose_name=_('Модуль'), null=True, blank=True)
    private = models.BooleanField(verbose_name=_('Частная'), default=True)

    def __str__(self):
        return self.subject

    def get_absolute_url(self):
        return reverse('detail', kwargs={'slug': self.id})

    @classmethod
    def check_status(cls, task, request, *args, **kwargs):
        if task.status == Task.ACCEPTED and (not task.executor):
            task.executor = request.user
        if task.executor and task.status == Task.NEW:
            task.status = Task.ACCEPTED
        if task.status == Task.CLOSED and not task.closed:
            task.closed = datetime.now()
        if task.closed and task.status != Task.CLOSED:
            task.status = Task.CLOSED
        if task.status == Task.CLOSED and (not task.close_reason):
            task.close_reason = Task.COMPLETE
        return

    def get_status_literal(self):
        _close_reason = ''
        if self.close_reason:
            _close_reason = '-' + dict(Task.CLOSE_REASONS)[self.close_reason]
        return dict(Task.STATUSES)[self.status] + _close_reason

    def get_private_literal(self):
        if self.private:
            return _('Да')
        return _('Нет')


class TaskType(models.Model):
    short_typename = models.CharField(max_length=30, verbose_name=_('Краткое наименование для ссылок (лат.)'), unique=True,
                                      )
    typename = models.CharField(max_length=100, verbose_name=_('Тип задачи'))

    def __str__(self):
        return self.typename

class Attachment(models.Model):
    task = models.ForeignKey(Task, verbose_name=_('Задача'))
    file = models.FileField(verbose_name=_('Файл'))

    def __str__(self):
        return self.file.name

class Comment(models.Model):
    task = models.ForeignKey(Task, verbose_name=_('Задача'))
    author = models.ForeignKey(User, verbose_name=_('Автор'))
    created = models.DateTimeField(verbose_name=_('Когда создана'), null=True, blank=True, default=datetime.now)
    body = models.TextField(verbose_name=_('Комментарий'))
    parent = models.ForeignKey('self', null=True, blank=True)
    attachments = models.ManyToManyField('Attachment', verbose_name=_('Файлы'), blank=True)

class Project(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Наименование проекта'), unique=True)
    start_date = models.DateField(verbose_name=_('Дата начала'), null=True, blank=True)
    finish_date = models.DateField(verbose_name=_('Дата окончания'), null=True, blank=True)

    def __str__(self):
        return self.name


class Module(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Наименование модуля'), unique=True)
    desc = models.TextField(verbose_name=_('Краткое описание'), null=True, blank=True)
    project = models.ForeignKey(Project, verbose_name=_('Проект'), null=True, blank=True)

    def __str__(self):
        return self.name


class TaskUserPriority(models.Model):
    '''
    Primary key's value is used as priority value
    '''
    priority = models.IntegerField(verbose_name=_('Значение приоритета'), null=True, blank=True)
    task = models.ForeignKey(Task, verbose_name=_('Задача'), )
    user = models.ForeignKey(User, verbose_name=_('Пользователь'))


class TaskView(models.Model):
    subject = models.CharField(max_length=255, verbose_name=_('Задача'))
    desc = models.TextField(verbose_name=_('Описание'), null=True, blank=True)
    deadline_date = models.DateTimeField(verbose_name=_('Крайний срок'), null=True, blank=True)
    notify_before = models.IntegerField(verbose_name=_('Уведомить за (дней)'), null=True, blank=True)
    created = models.DateTimeField(verbose_name=_('Когда создана'), null=True, blank=True,
                                   default=datetime.now)
    created_by = models.ForeignKey(User, related_name='vcreator', on_delete=models.DO_NOTHING,
                                   verbose_name=_('Создал'), null=True, blank=True)
    updated = models.DateTimeField(verbose_name=_('Когда изменена'), null=True, blank=True,
                                   default=datetime.now)
    updated_by = models.ForeignKey(User, related_name='vupdater', on_delete=models.DO_NOTHING,
                                   verbose_name=_('Изменил'), null=True, blank=True)
    status = models.CharField(verbose_name=_('Статус'), max_length=30, choices=Task.STATUSES)
    closed = models.DateTimeField(verbose_name=_('Когда закрыта'), null=True, blank=True)
    close_reason = models.CharField(max_length=2, verbose_name=_('Тип закрытия'), null=True,
                                    blank=True, choices=Task.CLOSE_REASONS)
    parent = models.ForeignKey('self', on_delete=models.DO_NOTHING, null=True, blank=True)
    executor = models.ForeignKey(User, related_name='vexecutor', on_delete=models.DO_NOTHING,
                                 null=True, blank=True)
    type = models.ForeignKey('TaskType', verbose_name=_('Тип'), on_delete=models.DO_NOTHING)
    project = models.ForeignKey('Project', verbose_name=_('Проект'), on_delete=models.DO_NOTHING,
                                null=True, blank=True)
    module = models.ForeignKey('Module', verbose_name=_('Модуль'), on_delete=models.DO_NOTHING,
                               null=True, blank=True)
    prty = models.IntegerField(verbose_name=_('Приоритет (не задавать вручную!)'), default=0)
    private = models.BooleanField(verbose_name=_('Частная'), default=True)

    class Meta:
        managed = False
        db_table = 'task_vtask'
        ordering = ['-prty']

    def get_status_literal(self):
        _close_reason = ''
        if self.close_reason:
            _close_reason = '-' + dict(Task.CLOSE_REASONS)[self.close_reason]
        return dict(Task.STATUSES)[self.status] + _close_reason

    def __str__(self):
        return self.subject



