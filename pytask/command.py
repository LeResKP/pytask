from colorterm import colorterm, Table
from .helper import CommandMeta, Param, indent, alias
from . import models
from .conf import config
import ConfigParser
import transaction
import sqlalchemy.orm.exc as sqla_exc
from sqlalchemy import or_
import datetime


def get_active_tasktime():
    """Get the active TaskTime if we have one
    """
    try:
        return models.TaskTime.query.filter_by(end_date=None).one()
    except sqla_exc.NoResultFound:
        return None


def get_report_config(param, section=None):
    """Get the report config corresponding to the given param
    """
    if not section:
        section = config.get('report', 'section')
    else:
        section += '_report'
    try:
        return config.get(section, param)
    except ConfigParser.NoOptionError:
        return config.get('default_report', param)


def _date_to_time(d):
    """Display the time of the given date
    """
    f = get_report_config('time_format')
    return d.strftime(f)


def _date_to_str(d):
    """Display given date as str
    """
    f = get_report_config('date_format')
    return d.strftime(f)


class Command(object):

    @classmethod
    def usage(cls):
        s = []
        s += ['\n%s commands:\n' % colorterm.bold(cls._command)]
        for c in sorted(cls._commands):
            func = getattr(cls, c)
            if getattr(func, '_alias', False):
                doc = "Alias for '%s'" % func._alias
            else:
                doc = func.__doc__.strip()
            s += ['    %s: %s\n' % (colorterm.bold(c), doc)]
            if func._parser:
                s += [indent(func._parser.format_help(), 8)]
        return '\n'.join(s)


class TaskCommand(Command):
    __metaclass__ = CommandMeta
    _command = 'task'

    def ls():
        """List the tasks
        """
        rows = models.Task.query.all()
        if not rows:
            return {'msg': 'No task!'}
        keys = [k.replace('_', ' ')
                for k in config.get('ls', 'format').split(' ')]
        table = Table(*keys)
        tasktime = get_active_tasktime()
        for row in rows:
            convert = None
            if tasktime and tasktime.idtask == row.idtask:
                convert = colorterm.cyan
            table.add_row(row.get_data_for_display(_date_to_str), convert)
        return {'msg': table.display()}

    @Param('description', required=True)
    @Param('bug_id', 'b')
    @Param('project_id', 'p')
    @Param('status', 's', type="choice",
           choices=['open', 'resolved', 'closed'], default='open')
    @Param('priority', 'l', type="choice", choices=['low', 'normal', 'high'],
           default='normal')
    def add(description, bug_id=None, status=None, priority=None,
            project_id=None):
        """Add new task
        """
        rows = models.Task.query.filter_by(description=description).all()
        if rows:
            return {'err': 'The task exists with id: %i' % rows[0].idtask}
        if project_id:
            p = models.Project.query.get(project_id)
            if not p:
                return {'err': 'The project %s doesn\'t exist' % project_id}

        with transaction.manager:
            task = models.Task(
                description=description,
                bug_id=bug_id,
                status=status,
                priority=priority,
                idproject=project_id,
            )
            if status is not None and status != 'open':
                task.completed_date = datetime.datetime.now()
            models.DBSession.add(task)

        models.DBSession.add(task)
        return {'success': 'Task %i created.' % task.idtask}

    @Param('idtask', required=True)
    @Param('force', 'f', action='store_true')
    def start(idtask, force=False):
        """Start a task.
        """
        task = models.Task.query.get(idtask)
        if not task:
            return {'err': 'The task %s doesn\'t exist!' % idtask}

        d = {}
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
            res = TaskCommand.stop(active_tasktime)
            if 'err' in res:
                return res
            d['info'] = res['success']

        with transaction.manager:
            tasktime = models.TaskTime(idtask=idtask,
                                       start_date=datetime.datetime.now())
            models.DBSession.add(tasktime)
        d['success'] = 'The task %s is activated' % idtask
        return d

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
        return {'success': 'The task %i is stopped!' % idtask}

    @Param('idtask', required=True)
    def info(idtask):
        """Display information of the task.
        """
        task = models.Task.query.get(idtask)
        if not task:
            return {'err': 'The task %s doesn\'t exist!' % idtask}

        dic = task.get_data_for_display(_date_to_str)
        s = ['']
        for key in ['ID', 'Bug ID', 'Project', 'Description', 'Status',
                    'Priority', 'Creation', 'Completed']:

            s += [colorterm.underline(key) + ': %s\n' % dic[key]]

        # s += [colorterm.underline('Task') + ': %s\n' % idtask]
        # s += [colorterm.underline('Description') + ': %s\n' % task.description]
        tasktimes = models.TaskTime.query.filter_by(idtask=idtask).all()
        if tasktimes:
            s += [colorterm.underline('Duration') + ':']

        sub = []
        for tasktime in tasktimes:
            if tasktime.end_date:
                sub += ['%s - %s' % (_date_to_str(tasktime.start_date),
                                   _date_to_str(tasktime.end_date))]
            else:
                sub += ['active from %s' % _date_to_str(tasktime.start_date)]
        s += ['\n'.join(sub)]
        return {'msg': '\n'.join(s)}

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
    @Param('project_id', 'p')
    @Param('status', 's', type="choice",
           choices=['open', 'resolved', 'closed'])
    @Param('priority', 'l', type="choice", choices=['low', 'normal', 'high'])
    def modify(idtask, **kw):
        """Modify a task.
        """
        task = models.Task.query.get(idtask)
        if not task:
            return {'err': 'The task %s doesn\'t exist!' % idtask}

        done = False
        for k, v in kw.iteritems():
            if v is not None:
                if k == 'project_id':
                    p = models.Project.query.get(v)
                    if not p:
                        return {'err': 'The project %s doesn\'t exist' % v}
                    setattr(task, 'idproject', v)
                else:
                    setattr(task, k, v)
                done = True
        if not done:
            return {'err': 'No parameter given!'}
        if task.status == 'open':
            task.completed_date = None
        elif task.status is not None:
            task.completed_date = datetime.datetime.now()
        with transaction.manager:
            models.DBSession.add(task)
        return {'success': 'The task %s is modified' % idtask}

    projects = alias('project ls', 'ProjectCommand.ls')
    today = alias('report today', 'ReportCommand.today')


def _report(start_date, end_date, **kw):
    """Make a report on the done between the given date
    """
    if start_date > datetime.datetime.now():
        return {'err': 'Can\'t make report in the future'}

    s = []
    if start_date == end_date:
        one_day = True
        s += [colorterm.bold('\nReport of the %s:' % _date_to_str(start_date))]
    else:
        one_day = False
        s += [colorterm.bold(
            '\nReport from %s to %s:' % (_date_to_str(start_date),
                                         _date_to_str(end_date)))]

    end_date = end_date + datetime.timedelta(days=1)
    rows = models.TaskTime.query.filter(
        or_(start_date < models.TaskTime.end_date,
            models.TaskTime.end_date == None)).filter(
        models.TaskTime.start_date < end_date
    ).all()

    if not rows:
        return {'err': 'No task done for the period'}

    durations = {}
    tasks = {}
    detail_data = []
    for row in rows:
        start = max(start_date, row.start_date)
        end = min(end_date, row.end_date or datetime.datetime.now())
        try:
            duration = ((end - start).total_seconds() / 3600)
        except:
            total_duration_in_seconds = lambda td: td.days * 24 * 60 * 60 + td.seconds
            duration = (total_duration_in_seconds((end - start)) / 3600.0)
        durations.setdefault(row.idtask, 0)
        durations[row.idtask] += duration
        if not row.end_date:
            end = None
        tasks[row.idtask] = row.task
        # NOTE: start is used to sort the data
        detail_data += [(start,
                         row.task.get_data_for_display(
                             _date_to_str,
                             Start=_date_to_time(start),
                             End=(end and _date_to_time(end) or 'active'),
                             Duration=round(duration, 1)))]

    keys = [k.replace('_', ' ')
            for k in get_report_config('format', kw.get('format')).split(' ')]
    table = Table(*keys)
    for idtask in sorted(durations.keys()):
        task = tasks[idtask]
        data = task.get_data_for_display(
            _date_to_str,
            Duration=round(durations[idtask], 1))
        table.add_row(data)
    s += [table.display()]

    detail_format = get_report_config('detail_format', kw.get('format'))
    if one_day:
        if detail_format:
            keys = [k.replace('_', ' ')
                    for k in detail_format.split(' ')]
            detail = Table(*keys)
            for start, dic in sorted(detail_data):
                detail.add_row(dic)

            s += ['%s' % detail.display()]
    else:
        s += [colorterm.bold('\nDetails of the report:')]
        d = (end_date - start_date).days
        for i in range(d):
            d = start_date + datetime.timedelta(i)
            if d > datetime.datetime.now():
                continue
            res = _report(d, d, **kw)
            if 'msg' in res:
                sub = res['msg']
            else:
                sub = colorterm.bold('No task on %s' % _date_to_str(d))
            s += [indent(sub, 4)]
    return {'msg': '\n\n'.join(s)}


class ReportCommand(Command):
    __metaclass__ = CommandMeta
    _command = 'report'

    @Param('format', 'f')
    @Param('delta', 'd')
    def today(**kw):
        """Create a report of the done of today.
        """
        now = datetime.datetime.now()
        start_date = now.replace(minute=0, hour=0, second=0, microsecond=0)
        if kw.get('delta'):
            start_date = start_date - datetime.timedelta(days=int(kw['delta']))
        end_date = start_date
        return _report(start_date, end_date, **kw)

    @Param('format', 'f')
    @Param('delta', 'd')
    def week(**kw):
        """Create a report of the done of the week.
        We start from the last monday to the friday of the same week.
        """
        now = datetime.datetime.now()
        now = now.replace(minute=0, hour=0, second=0, microsecond=0)
        start_date = now + datetime.timedelta(days=-now.weekday())
        delta = kw.get('delta')
        if delta:
            delta = int(delta) * 7
            start_date = start_date - datetime.timedelta(days=delta)
        end_date = start_date + datetime.timedelta(days=4)
        return _report(start_date, end_date, **kw)

    @Param('startdate', required=True)
    @Param('enddate', required=True)
    @Param('format', 'f')
    def date(startdate, enddate, **kw):
        """Create a report between given dates.
        """
        date_str_format = '%Y/%m/%d'
        start_date = datetime.datetime.strptime(startdate, date_str_format)
        end_date = datetime.datetime.strptime(enddate, date_str_format)
        return _report(start_date, end_date, **kw)

    @Param('startdate', required=True)
    @Param('enddate', required=True)
    def a9(startdate, enddate):
        date_str_format = '%Y/%m/%d'
        start_date = datetime.datetime.strptime(startdate, date_str_format)
        end_date = datetime.datetime.strptime(enddate, date_str_format)

        if start_date > datetime.datetime.now():
            return {'err': 'Can\'t make report in the future'}

        s = []
        end_date = end_date + datetime.timedelta(days=1)
        rows = models.TaskTime.query.filter(
            or_(start_date < models.TaskTime.end_date,
                models.TaskTime.end_date == None)).filter(
            models.TaskTime.start_date < end_date
        ).all()

        lis = []
        dic = {}
        for row in rows:
            start = max(start_date, row.start_date)
            end = min(end_date, row.end_date or datetime.datetime.now())
            try:
                duration = ((end - start).total_seconds() / 3600)
            except:
                total_duration_in_seconds = lambda td: td.days * 24 * 60 * 60 + td.seconds
                duration = (total_duration_in_seconds((end - start)) / 3600.0)

            bug_id = row.task.bug_id
            if not bug_id and row.task.project:
                bug_id = row.task.project.bug_id
            assert(bug_id), row.task.description
            s = '%(startdate)s-+0200 +%(duration)sh # %(description)s' % {
                'startdate': start.strftime('%Y-%m-%d-%H:%M:%S'),
                'duration': round(duration, 1),
                'description': row.task.description,
            }
            dic.setdefault(bug_id, []).append(s)

        lis = ['supplement resource Aurelien {']
        for bud_id, values in dic.iteritems():
            if bug_id == 'reactivity':
                lis += ['  plan:booking postrms.reactivity_weekly']
            else:
                lis += ['  plan:booking postrms.issue_%s' % bud_id]
            for v in values:
                lis += ['   %s' % v]
            lis += ['']
        lis += ['}']
        return {'msg': "\n".join(lis)}


class ProjectCommand(Command):
    __metaclass__ = CommandMeta
    _command = 'project'

    def ls():
        """List the projects.
        """
        rows = models.Project.query.all()
        if not rows:
            return {'msg': 'No project!'}

        table = Table('ID', 'Name', 'Bug_ID')
        for row in rows:
            table.add_row({
                'ID': row.idproject,
                'Name': row.name,
                'Bug_ID': row.bug_id,
            })
        return {'msg': table.display()}

    @Param('name', required=True)
    @Param('bug_id', 'b')
    def add(name, bug_id=None):
        """Add new task
        """
        rows = models.Project.query.filter_by(name=name).all()
        if rows:
            return {
                'err': 'The project exists with id: %i' % rows[0].idproject}
        with transaction.manager:
            project = models.Project(
                name=name,
                bug_id=bug_id,
            )
            models.DBSession.add(project)

        models.DBSession.add(project)
        return {'success': 'Project %i created.' % project.idproject}

    @Param('idproject', required=True)
    @Param('name', 'n')
    @Param('bug_id', 'b')
    def modify(idproject, **kw):
        """Add new task
        """
        project = models.Project.query.get(idproject)
        if not project:
            return {'err': 'The project %s doesn\'t exist!' % idproject}

        done = False
        for k, v in kw.iteritems():
            if v is not None:
                setattr(project, k, v)
                done = True
        if not done:
            return {'err': 'No parameter given!'}
        with transaction.manager:
            models.DBSession.add(project)
        return {'success': 'The project %s is modified' % idproject}
