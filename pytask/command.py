from .helper import CommandMeta, Param
from . import models
import transaction


class TaskCommand(object):
    __metaclass__ = CommandMeta

    def ls():
        """List the tasks
        """
        rows = models.Task.query.all()
        if not rows:
            return 'No task!'
        return '\n'.join(['%s %s' % (row.idtask, row.description)
                          for row in rows])

    @Param('description', required=True)
    def add(description):
        """Add new task
        """
        rows = models.Task.query.filter_by(description=description).all()
        if rows:
            raise Exception('The task exists with id: %i' % rows[0].idtask)
        with transaction.manager:
            task = models.Task(description=description)
            models.DBSession.add(task)

        models.DBSession.add(task)
        return 'Task %i created.' % task.idtask
