import taskman.wsgi

from task.models import TaskUserPriority, TaskPriority

prev = None
for p_orig in TaskUserPriority.objects.all():
    if prev and p_orig.task.id == prev.task.id:
        if p_orig.priority > prev.priority:
            new_priority = TaskPriority(id=prev.id, task=p_orig.task, priority=p_orig.priority)
        else:
            new_priority = TaskPriority(id=prev.id, task=prev.task, priority=prev.priority)
    else:
        new_priority = TaskPriority(id=p_orig.id, task=p_orig.task, priority=p_orig.priority)
    new_priority.save()
