from datetime import datetime

from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User



# Create your models here.

class Task(models.Model):
    # Статусы
    NEW = 'NEW'
    ACCEPTED = 'ACCEPTED'
    CLOSED = 'CLOSED'

    STATUSES = (
        (NEW, 'Новая'),
        (ACCEPTED, 'В работе'),
        (CLOSED, 'Закрыта'),
    )

    # Тип закрытия
    COMPLETE = 'CT'
    DUPLICATE = 'DU'
    WONTFIX = 'WF'
    CLOSE_REASONS = (
        (COMPLETE, 'Завершено'),
        (DUPLICATE, 'Дублирует существующую'),
        (WONTFIX, 'Отменено'),
    )

    subject = models.CharField(max_length=255, verbose_name='Задача')
    desc = models.TextField(verbose_name='Описание', null=True, blank=True)
    deadline_date = models.DateField(verbose_name='Крайний срок', null=True, blank=True)
    notify_before = models.IntegerField(verbose_name='Уведомить за (дней)', null=True, blank=True)
    created = models.DateTimeField(verbose_name='Когда создана', null=True, blank=True, default=datetime.now)
    created_by = models.ForeignKey(User, related_name='creator', verbose_name='Создал', null=True, blank=True)
    updated = models.DateTimeField(verbose_name='Когда изменена', null=True, blank=True, default=datetime.now)
    updated_by = models.ForeignKey(User, related_name='updater', verbose_name='Изменил', null=True, blank=True)
    status = models.CharField(verbose_name='Статус', max_length=30, choices=STATUSES)
    closed = models.DateTimeField(verbose_name='Когда закрыта', null=True, blank=True)
    close_reason = models.CharField(max_length=2, verbose_name='Тип закрытия', null=True, blank=True,
                                    choices=CLOSE_REASONS)
    #attachments = models.ManyToManyField('Attachment', verbose_name='Файлы', blank=True, null=True)
    parent = models.ForeignKey('self', null=True, blank=True)
    executor = models.ForeignKey(User, related_name='executor', null=True, blank=True)
    type = models.ForeignKey('TaskType', verbose_name='Тип')
    project = models.ForeignKey('Project', verbose_name='Проект', null=True, blank=True)
    module = models.ForeignKey('Module', verbose_name='Модуль', null=True, blank=True)
    priority = models.IntegerField(verbose_name='Приоритет (не задавать вручную!)', default=0)

    class Meta:
        ordering = ['-priority', 'id']

    def __str__(self):
        return self.subject

    def get_absolute_url(self):
        return reverse('detail', kwargs={'slug': self.id})

    @classmethod
    def check_status(cls, task):
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
        return dict(Task.STATUSES)[self.status]


class TaskType(models.Model):
    short_typename = models.CharField(max_length=30, verbose_name='Краткое наименование для ссылок (лат.)', unique=True,
                                      )
    typename = models.CharField(max_length=100, verbose_name='Тип задачи')

    def __str__(self):
        return self.typename

class Attachment(models.Model):
    task = models.ForeignKey(Task, verbose_name='Задача')
    file = models.FileField(verbose_name='Файл')

    def __str__(self):
        return self.file.name

class Comment(models.Model):
    task = models.ForeignKey(Task, verbose_name='Задача')
    author = models.ForeignKey(User, verbose_name='Автор')
    created = models.DateTimeField(verbose_name='Когда создана', null=True, blank=True, default=datetime.now)
    body = models.TextField(verbose_name='Комментарий')
    parent = models.ForeignKey('self', null=True, blank=True)
    attachments = models.ManyToManyField('Attachment', verbose_name='Файлы', blank=True)

class Project(models.Model):
    name = models.CharField(max_length=255, verbose_name='Наименование проекта', unique=True)
    start_date = models.DateField(verbose_name='Дата начала', null=True, blank=True)
    finish_date = models.DateField(verbose_name='Дата окончания', null=True, blank=True)

    def __str__(self):
        return self.name


class Module(models.Model):
    name = models.CharField(max_length=255, verbose_name='Наименование модуля', unique=True)
    desc = models.TextField(verbose_name='Краткое описание', null=True, blank=True)
    project = models.ForeignKey(Project, verbose_name='Проект', null=True, blank=True)

    def __str__(self):
        return self.name

