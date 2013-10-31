import models
import transaction
import datetime

# Bash color:
# http://misc.flogisoft.com/bash/tip_colors_and_formatting


def ls(*args):
    rows = models.Task.query.all()
    s = ''
    for row in rows:
        s += '%i: %s\n' % (row.idtask, row.name)
    return s


def add(name):
    with transaction.manager:
        task = models.Task(name=name)
        models.DBSession.add(task)
    return 'Task added.'


def active(*args):
    tasktime = models.TaskTime.query.filter_by(end_date=None).one()
    return info(tasktime.idtask)


def info(idtask):
    task = models.Task.query.filter_by(idtask=idtask).one()
    s = '%s\n' % task.name
    tasktimes = models.TaskTime.query.filter_by(idtask=idtask).all()
    for row in tasktimes:
        s += '%s: %s\n' % (row.start_date, row.end_date or 'Active')
    return s


def start(idtask):
    # TODO: check the idtask exist and no other is started
    with transaction.manager:
        tasktime = models.TaskTime(idtask=idtask, start_date=datetime.datetime.now())
        models.DBSession.add(tasktime)
    return 'Task %s started.' % idtask


def stop(idtask):
    with transaction.manager:
        # TODO: can failed
        tasktime = models.TaskTime.query.filter_by(idtask=idtask, end_date=None).one()
        tasktime.end_date = datetime.datetime.now()
        models.DBSession.add(tasktime)
    return 'Task %s stopped.' % idtask
