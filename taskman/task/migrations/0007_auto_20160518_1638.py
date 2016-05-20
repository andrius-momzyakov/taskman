# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-05-18 13:38
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0006_task_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Наименование модуля')),
                ('desc', models.TextField(blank=True, null=True, verbose_name='Краткое описание')),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Наименование проекта')),
                ('start_date', models.DateField(blank=True, null=True, verbose_name='Дата начала')),
                ('finish_date', models.DateField(blank=True, null=True, verbose_name='Дата окончания')),
            ],
        ),
        migrations.AddField(
            model_name='comment',
            name='created',
            field=models.DateTimeField(blank=True, default=datetime.datetime.now, null=True, verbose_name='Когда создана'),
        ),
        migrations.AlterField(
            model_name='task',
            name='closed',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Когда закрыта'),
        ),
        migrations.AddField(
            model_name='module',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='task.Project', verbose_name='Проект'),
        ),
        migrations.AddField(
            model_name='task',
            name='module',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='task.Module', verbose_name='Модуль'),
        ),
        migrations.AddField(
            model_name='task',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='task.Project', verbose_name='Проект'),
        ),
    ]
