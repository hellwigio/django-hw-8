# Homework 10 — Task manager ORM queries

The implementation is in `core/homework10.py` and uses
the existing `Task` and `SubTask` models. Status values are taken from
`Task.Status`: `new`, `in_progress`, `done` (labels: New, In progress, Done).

Use Python 3.14+ because the existing models use `uuid.uuid7`.

```sh
make install
make migrate
.venv/bin/python manage.py shell -c "from core.homework10 import run; run()"
```

Run against a separate homework database. The command creates the required
task and two subtasks, reads New tasks and overdue Done subtasks, updates
the three requested fields, and deletes the created task. Django cascades
the deletion to its subtasks. It prints the records and verifies deletion.
Everything runs in one transaction; a failure rolls back the changes.
It never deletes pre-existing tasks to make room for duplicate titles.

The overdue Done query may return an empty list: all records created by the
assignment initially have status New. No extra records or status changes
are required to execute this query.

## Lesson materials

Checked against the two notes linked from Python Adv 19 (Django lessons 19 and 20):
https://lms.itcareerhub.de/course/section.php?id=6475

The solution uses Django Shell and the existing Django ORM, as in the notes:
`objects.create()`, `filter()`, `values()`, `update()`, `delete()`, `exists()`,
`count()`, the `deadline__lt` lookup and `on_delete=models.CASCADE`.
Dates use Python `datetime.timedelta` and Django `timezone.now()` for the
existing timezone-aware DateTimeFields. No additional third-party dependency
is needed. Q, F and bulk operations are covered in the notes but are not
needed for these assignment queries.

The management command `python manage.py homework10` is an alternative launcher
for the same queries. The transaction is a safeguard for repeatable execution.
