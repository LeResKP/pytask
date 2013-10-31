import models
import transaction
import datetime
import json

# Bash color:
# http://misc.flogisoft.com/bash/tip_colors_and_formatting


def add_color(color, s):
    return '\x1b[01;%sm%s\x1b[00m' % (color, s)


def green(s):
    return add_color(32, s)


def blue(s):
    return add_color(34, s)


def ls(*args):
    rows = models.Task.query.all()
    s = ''
    for row in rows:
        s += '%i: %s\n' % (row.idtask, row.name)
    return {'stdout': s}


def add(name):
    with transaction.manager:
        task = models.Task(name=name)
        models.DBSession.add(task)
    return {'stdout': green('Task added.')}


def active(*args):
    tasktime = models.TaskTime.query.filter_by(end_date=None).one()
    return {'stdout': info(tasktime.idtask)}


def info(idtask):
    task = models.Task.query.filter_by(idtask=idtask).one()
    lis = [blue(task.name)]
    tasktimes = models.TaskTime.query.filter_by(idtask=idtask).all()
    for row in tasktimes:
        if not row.end_date:
            lis += [blue('%s: active' % row.start_date)]
        else:
            lis += ['%s: %s' % (row.start_date, row.end_date)]
    return {'stdout': '\n'.join(lis)}


def start(idtask):
    # TODO: check the idtask exist and no other is started
    with transaction.manager:
        tasktime = models.TaskTime(idtask=idtask, start_date=datetime.datetime.now())
        models.DBSession.add(tasktime)
    return {'stdout': green('Task %s started.' % idtask)}


def stop(idtask):
    with transaction.manager:
        # TODO: can failed
        tasktime = models.TaskTime.query.filter_by(idtask=idtask, end_date=None).one()
        tasktime.end_date = datetime.datetime.now()
        models.DBSession.add(tasktime)
    return {'stdout': green('Task %s stopped.' % idtask)}


def edit(idtask):
    task = models.Task.query.filter_by(idtask=idtask).one()
    return {
        'editor': True,
        'content': {'name': task.name},
        'idtask': idtask,
        'action': 'update'}


def update(*args):
    lis = args[0].split(' ')
    idtask = lis[0]
    dic = json.loads(' '.join(lis[1:]))
    with transaction.manager:
        task = models.Task.query.filter_by(idtask=int(idtask)).one()
        task.name = dic['name']
        models.DBSession.add(task)
    return {'stdout': green('Task updated.')}
