create or replace view task_vtask_null as
select t.*, tup.prty
from task_task t left outer join
( select t.prty, t.user_id, t.task_id
  from
    (select max(p.priority) prty, p.user_id user_id, p.task_id task_id from task_taskuserpriority p
     group by p.user_id, p.task_id) as t
) as tup on t.id = tup.task_id;

create or replace view task_vtask as
select
    t.id,
    t.subject,
    t."desc",
    t.deadline_date,
    t.notify_before,
    t.created,
    t.updated,
    t.closed,
    t.close_reason,
    t.created_by_id,
    t.parent_id,
    t.updated_by_id,
    t.executor_id,
    t.type_id,
    t.module_id,
    t.project_id,
    t.status,
    coalesce(t.prty, -1) prty
from task_vtask_null t;