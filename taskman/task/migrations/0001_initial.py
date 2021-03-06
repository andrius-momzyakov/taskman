# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-05-17 15:04
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='', verbose_name='Файл')),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField(verbose_name='Комментарий')),
                ('attachments', models.ManyToManyField(to='task.Attachment', verbose_name='Файлы')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Автор')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='task.Comment')),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=255, verbose_name='Задача')),
                ('desc', models.TextField(blank=True, null=True, verbose_name='Описание')),
                ('deadline_date', models.DateField(verbose_name='Крайний срок')),
                ('notify_before', models.IntegerField(verbose_name='Уведомить за (дней)')),
                ('created', models.DateTimeField(blank=True, default=datetime.datetime.now, null=True, verbose_name='Когда создана')),
                ('updated', models.DateTimeField(blank=True, default=datetime.datetime.now, null=True, verbose_name='Когда изменена')),
                ('closed', models.DateTimeField(blank=True, default=datetime.datetime.now, null=True, verbose_name='Когда закрыта')),
                ('close_reason', models.CharField(blank=True, choices=[('CT', 'Завершено'), ('DU', 'Дублирует существующую'), ('WF', 'Отменено')], max_length=2, null=True, verbose_name='Тип закрытия')),
                ('attachments', models.ManyToManyField(to='task.Attachment', verbose_name='Файлы')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='creator', to=settings.AUTH_USER_MODEL, verbose_name='Создал')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='task.Task')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='updater', to=settings.AUTH_USER_MODEL, verbose_name='Изменил')),
            ],
        ),
        migrations.CreateModel(
            name='TaskType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('typename', models.CharField(max_length=100, verbose_name='Тип задачи')),
            ],
        ),
    ]
