import models
import transaction
import datetime
import json
from colorterm import colorterm
import sqlalchemy.orm.exc as sqla_exc


def _info(s):
    return colorterm.blue(s)


def _success(s):
    return colorterm.green(s)


def _failure(s):
    return colorterm.red(s)


def _get_active():
    try:
        return models.TaskTime.query.filter_by(end_date=None).one()
    except sqla_exc.NoResultFound:
        return None


def ls(*args):
    rows = models.Task.query.all()
    s = ''
    active_idtask = None
    active = _get_active()
    if active:
        active_idtask = active.idtask
    for row in rows:
        if row.idtask == active_idtask:
            s += _info('%i: %s\n' % (row.idtask, row.description))
        else:
            s += '%i: %s\n' % (row.idtask, row.description)
    return {'stdout': s}


def add(description):
    with transaction.manager:
        task = models.Task(description=description)
        models.DBSession.add(task)
    return {'stdout': _success('Task added.')}


def active(*args):
    try:
        tasktime = _get_active()
    except sqla_exc.MultipleResultsFound, e:
        return {'stderr': _failure('There is a problem in the DB: %s' % e)}

    if not tasktime:
        return {'stdout': _success('No active task!')}

    return {'stdout': _info('Current task: %s' % tasktime.idtask)}


def info(idtask):
    task = models.Task.query.filter_by(idtask=idtask).one()
    lis = [colorterm.blue(task.description)]
    tasktimes = models.TaskTime.query.filter_by(idtask=idtask).all()
    for row in tasktimes:
        if not row.end_date:
            lis += [_info('%s: active' % row.start_date)]
        else:
            lis += ['%s: %s' % (row.start_date, row.end_date)]
    return {'stdout': '\n'.join(lis)}


def start(idtask):
    # TODO: check the idtask exist and no other is started
    with transaction.manager:
        tasktime = models.TaskTime(idtask=idtask, start_date=datetime.datetime.now())
        models.DBSession.add(tasktime)
    return {'stdout': _success('Task %s started.' % idtask)}


def stop():
    try:
        tasktime = _get_active()
    except sqla_exc.MultipleResultsFound, e:
        return {'stderr': _failure('There is a problem in the DB: %s' % e)}

    if not tasktime:
        return {'stdout': _failure('No active task!')}

    idtask = tasktime.idtask
    with transaction.manager:
        tasktime.end_date = datetime.datetime.now()
        models.DBSession.add(tasktime)
    return {'stdout': _success('Task %s stopped.' % idtask)}


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
    return {'stdout': _success('Task %s updated.' % idtask)}
