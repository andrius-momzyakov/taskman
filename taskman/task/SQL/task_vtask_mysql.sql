create or replace view task_vtmp as select max(p.priority) prty, p.user_id, p.task_id
from task_taskuserpriority p
group by p.user_id, p.task_id;

create or replace view task_vtask as
select t.*, IFNULL(tup.prty, 0) prty
from task_task t left outer join
task_vtmp as tup on t.id = tup.task_id;