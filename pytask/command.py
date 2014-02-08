from .helper import CommandMeta, Param
from . import models
import transaction
import sqlalchemy.orm.exc as sqla_exc
import datetime


def get_active_tasktime():
    """Get the active TaskTime if we have one
    """
    try:
        return models.TaskTime.query.filter_by(end_date=None).one()
    except sqla_exc.NoResultFound:
        return None


class TaskCommand(object):
    __metaclass__ = CommandMeta

    def ls():
        """List the tasks
        """
        rows = models.Task.query.all()
        if not rows:
            return 'No task!'
        return '\n'.join(['%s %s %s' % (row.idtask,
                                        row.description,
                                        row.bug_id or '')
                          for row in rows])

    @Param('description', required=True)
    @Param('bug_id', 'b')
    def add(description, bug_id=None):
        """Add new task
        """
        rows = models.Task.query.filter_by(description=description).all()
        if rows:
            raise Exception('The task exists with id: %i' % rows[0].idtask)
        with transaction.manager:
            task = models.Task(description=description, bug_id=bug_id)
            models.DBSession.add(task)

        models.DBSession.add(task)
        return 'Task %i created.' % task.idtask

    @Param('idtask', required=True)
    @Param('force', 'f', action='store_true')
    def start(idtask, force=False):
        """Start a task.
        """
        task = models.Task.query.get(idtask)
        if not task:
            return {'err': 'The task %s doesn\'t exist!' % idtask}

        s = []
        active_tasktime = get_active_tasktime()
        if active_tasktime:
            if active_tasktime.idtask == task.idtask:
                return {'err': 'The task %s is already activated!' % idtask}
            if force is not True:
                return {
                    'confirm': (
                        'An other task %s '
                        'is already activated! '
                        'Do you want to stop it?' % active_tasktime.idtask),
                    'command': 'start -f %s' % idtask
                }
            s += [TaskCommand.stop(active_tasktime)]

        with transaction.manager:
            tasktime = models.TaskTime(idtask=idtask,
                                       start_date=datetime.datetime.now())
            models.DBSession.add(tasktime)
        s += ['The task %s is activated' % idtask]
        return '\n'.join(s)

    def stop(tasktime=None):
        """Stop a task.
        """
        if not tasktime:
            tasktime = get_active_tasktime()
        if not tasktime:
            return {'err': 'No active task!'}
        idtask = tasktime.idtask
        with transaction.manager:
            tasktime.end_date = datetime.datetime.now()
            models.DBSession.add(tasktime)
        return 'The task %i is stopped!' % idtask

    @Param('idtask', required=True)
    def info(idtask):
        """Display information of the task.
        """
        task = models.Task.query.get(idtask)
        if not task:
            return {'err': 'The task %s doesn\'t exist!' % idtask}
        s = ['Task %s:' % idtask]
        s += ['Description: %s' % task.description]
        tasktimes = models.TaskTime.query.filter_by(idtask=idtask).all()
        if tasktimes:
            s += ['Duration:']
        for tasktime in tasktimes:
            if tasktime.end_date:
                s += ['%s - %s' % (tasktime.start_date,
                                   tasktime.end_date)]
            else:
                s += ['active from %s' % tasktime.start_date]
        return '\n'.join(s)

    def active():
        """Display information about the active task.
        """
        tasktime = get_active_tasktime()
        if not tasktime:
            return {'err': 'No active task!'}
        return TaskCommand.info(tasktime.idtask)

    @Param('idtask', required=True)
    @Param('description', 'd')
    @Param('bug_id', 'b')
    def modify(idtask, **kw):
        """Modify a task.
        """
        task = models.Task.query.get(idtask)
        if not task:
            return {'err': 'The task %s doesn\'t exist!' % idtask}

        done = False
        for k, v in kw.iteritems():
            if v is not None:
                setattr(task, k, v)
                done = True

        if not done:
            return {'err': 'No parameter given!'}
        with transaction.manager:
            models.DBSession.add(task)
        return 'The task %s is modified' % idtask
