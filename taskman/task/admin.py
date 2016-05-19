from django.contrib import admin
from . import models

# Register your models here.

admin.site.register(models.Task)
admin.site.register(models.TaskType)
admin.site.register(models.Attachment)
admin.site.register(models.Comment)
admin.site.register(models.Project)
admin.site.register(models.Module)