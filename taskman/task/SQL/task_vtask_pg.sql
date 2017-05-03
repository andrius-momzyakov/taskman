CREATE OR REPLACE VIEW task_vtask_null AS
 SELECT t.id,
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
    tp.priority AS prty,
    t.private
   FROM task_task t
     LEFT JOIN  task_taskpriority tp ON t.id = tp.task_id;

ALTER TABLE task_vtask_null
  OWNER TO postgres;

CREATE OR REPLACE VIEW task_vtask AS
 SELECT t.id,
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
    COALESCE(t.prty, (-1)) AS prty,
    t.private
   FROM task_vtask_null t;

ALTER TABLE task_vtask
  OWNER TO postgres;
