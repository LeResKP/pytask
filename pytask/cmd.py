import models
import transaction
import datetime
import json
import inspect
from functools import wraps
from colorterm import colorterm, Table
import sqlalchemy.orm.exc as sqla_exc


def _info(s):
    return colorterm.cyan(s)


def _success(s):
    return colorterm.green(s)


def _failure(s):
    return colorterm.red(s)


def _get_active():
    try:
        return models.TaskTime.query.filter_by(end_date=None).one()
    except sqla_exc.NoResultFound:
        return None


def catch(func):
    @wraps(func)
    def wrapper(*args, **kw):
        try:
            return func(*args, **kw)
        except Exception, e:
            return {'stderr': _failure('%s: %s' % (func.__name__, unicode(e)))}
    return wrapper


class StaticMethodMeta(type):

    def __new__(mcs, name, bases, dic):
        available_cmds = {}
        for k, v in dic.items():
            if k.startswith('_'):
                continue
            if inspect.isfunction(v):
                dic[k] = classmethod(catch(v))
                available_cmds[k] = v

        dic['available_cmds'] = available_cmds
        return type.__new__(mcs, name, bases, dic)


class TaskCmd(object):
    __metaclass__ = StaticMethodMeta

    def r(cls):
        raise Exception('Error')

    def ls(cls):
        rows = models.Task.query.all()
        active_idtask = None
        active = _get_active()
        if active:
            active_idtask = active.idtask
        table = Table('ID', 'Project', 'Description')
        for row in rows:
            convert = None
            if row.idtask == active_idtask:
                convert = colorterm.cyan
            table.add_row({
                'ID': row.idtask,
                'Project': (row.project and row.project.name or None),
                'Description': row.description,
            }, convert)
        return {'stdout': table.display()}

    def add(cls, description, project=None):
        with transaction.manager:
            task = models.Task(description=description)
            models.DBSession.add(task)
        return {'stdout': _success('Task added.')}

    def active(cls):
        try:
            tasktime = _get_active()
        except sqla_exc.MultipleResultsFound, e:
            return {'stderr': _failure('There is a problem in the DB: %s' % e)}

        if not tasktime:
            return {'stdout': _success('No active task!')}

        return {'stdout': _info('Current task: %s' % tasktime.idtask)}

    def info(cls, idtask=None):
        if not idtask:
            active = _get_active()
            if not active:
                return {'stderr': _failure('No idtask given and no active task')}
            task = active.task
        task = models.Task.query.filter_by(idtask=idtask).one()
        lis = [colorterm.blue(task.description)]
        tasktimes = models.TaskTime.query.filter_by(idtask=idtask).all()
        for row in tasktimes:
            if not row.end_date:
                lis += [_info('%s: active' % row.start_date)]
            else:
                lis += ['%s: %s' % (row.start_date, row.end_date)]
        return {'stdout': '\n'.join(lis)}

    def start(cls, idtask, confirm=None):
        # TODO: check the idtask exist and no other is started
        active = _get_active()
        if active:
            if confirm:
                cls.stop()
            else:
                if active.idtask == int(idtask):
                    return {'stdout': _info('Task %s is already actived.' % idtask)}
                return {
                    'confirm': True,
                    'stdout': (
                        'Task %s is active, '
                        'would you want to stop it (yes to confirm)?' % idtask),
                    'action': 'start',
                    'idtask': idtask,
                }
        with transaction.manager:
            tasktime = models.TaskTime(idtask=idtask, start_date=datetime.datetime.now())
            models.DBSession.add(tasktime)
        return {'stdout': _success('Task %s started.' % idtask)}

    def stop(cls):
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

    def edit(cls, idtask):
        task = models.Task.query.filter_by(idtask=idtask).one()
        return {
            'editor': True,
            'content': {'description': task.description},
            'idtask': idtask,
            'action': 'update'}

    def update(cls, idtask, json_content):
        dic = json.loads(json_content)
        with transaction.manager:
            task = models.Task.query.filter_by(idtask=int(idtask)).one()
            task.description = dic['description']
            models.DBSession.add(task)
        return {'stdout': _success('Task %s updated.' % idtask)}

    def modify(cls, idtask, project=None):
        with transaction.manager:
            task = models.Task.query.filter_by(idtask=int(idtask)).one()
            if project is not None:
                if not project:
                    task.project = None
                else:
                    try:
                        pobj = models.Project.query.filter_by(name=project).one()
                    except sqla_exc.NoResultFound:
                        pobj = models.Project(name=project)
                        models.DBSession.add(pobj)
                    task.project = pobj

            models.DBSession.add(task)
        return {'stdout': _success('Task %s updated.' % idtask)}
