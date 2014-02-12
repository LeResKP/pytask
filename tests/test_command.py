from . import testing
import pytask.command as command
import pytask.models as models
import datetime
import transaction
from mock import patch
from pytask.conf import config


class TestFunctions(testing.DBTestCase):

    def test_get_active_tasktime(self):
        res = command.get_active_tasktime()
        self.assertEqual(res, None)

        task = models.Task(description='task 1')
        tasktime = models.TaskTime(start_date=datetime.datetime.now())
        tasktime.task = task
        models.DBSession.add(tasktime)
        res = command.get_active_tasktime()
        self.assertEqual(res, tasktime)

        tasktime.end_date = datetime.datetime.now()
        res = command.get_active_tasktime()
        self.assertEqual(res, None)

    def test__report(self):
        task = models.Task(
            description='Task 1',
            creation_date=datetime.datetime.now()
        )
        tasktime = models.TaskTime(
            start_date=datetime.datetime(2014, 2, 8, 9),
            end_date=datetime.datetime(2014, 2, 8, 14),
            task=task,
        )
        models.DBSession.add(tasktime)

        res = command._report(
            datetime.datetime(2014, 2, 7),
            datetime.datetime(2014, 2, 7))
        self.assertEqual(res, {'err': 'No task done for the period'})
        self.assertFalse('Task 1' in res)

       #  -----------|----------|-------
       #          [                 ]  (1)
       #          [       ]            (2)
       #                  [         ]  (3)
       #              [     ]          (4)

        # (1)
        res = command._report(
            datetime.datetime(2014, 2, 8),
            datetime.datetime(2014, 2, 8))
        self.assertEqual(len(res), 1)
        self.assertTrue('Task 1' in res['msg'])

        # (2)
        res = command._report(
            datetime.datetime(2014, 2, 8),
            datetime.datetime(2014, 2, 8, 12))
        self.assertEqual(len(res), 1)
        self.assertTrue('Task 1' in res['msg'])

        # (3)
        res = command._report(
            datetime.datetime(2014, 2, 8, 12),
            datetime.datetime(2014, 2, 9))
        self.assertEqual(len(res), 1)
        self.assertTrue('Task 1' in res['msg'])

        # (4)
        res = command._report(
            datetime.datetime(2014, 2, 8, 11),
            datetime.datetime(2014, 2, 8, 12))
        self.assertEqual(len(res), 1)
        self.assertTrue('Task 1' in res['msg'])

        # Not end date
        tasktime.end_date = None
        models.DBSession.add(tasktime)
        res = command._report(
            datetime.datetime(2014, 2, 8),
            datetime.datetime(2014, 2, 9))
        self.assertEqual(len(res), 1)
        self.assertTrue('Task 1' in res['msg'])

        res = command._report(
            (datetime.datetime.now() + datetime.timedelta(days=1)),
            (datetime.datetime.now() + datetime.timedelta(days=2))
        )
        self.assertEqual(res, {'err': 'Can\'t make report in the future'})

    def test__report_with_format(self):
        task = models.Task(
            description='Task 1',
            creation_date=datetime.datetime.now()
        )
        tasktime = models.TaskTime(
            start_date=datetime.datetime(2014, 2, 8, 9),
            end_date=datetime.datetime(2014, 2, 8, 14),
            task=task,
        )
        models.DBSession.add(tasktime)

        res = command._report(
            datetime.datetime(2014, 2, 8),
            datetime.datetime(2014, 2, 8))
        self.assertEqual(len(res), 1)
        self.assertTrue('Task 1' in res['msg'])
        self.assertEqual(res['msg'].count('ID'), 4)
        self.assertEqual(res['msg'].count('Bug ID'), 2)

        config.add_section('new_report')
        config.set('new_report', 'format', 'Bug_ID Duration')
        config.set('new_report', 'detail_format', '')

        res = command._report(
            datetime.datetime(2014, 2, 8),
            datetime.datetime(2014, 2, 8),
            format='new')
        self.assertEqual(len(res), 1)
        self.assertTrue('Task 1' not in res['msg'])
        # There is no details and we don't display the ID
        self.assertEqual(res['msg'].count('ID'), 1)
        self.assertEqual(res['msg'].count('Bug ID'), 1)
        config.remove_section('new_report')


class TestTaskCommand(testing.DBTestCase):

    def test_ls(self):
        res = command.TaskCommand.ls()
        self.assertEqual(res, {'msg': 'No task!'})

        task = models.Task(description='my task')
        models.DBSession.add(task)
        res = command.TaskCommand.ls()
        self.assertTrue('my task' in res['msg'])

    def test_add(self):
        res = command.TaskCommand.add('my task')
        self.assertEqual(res, {'success': 'Task 1 created.'})
        task = models.Task.query.one()
        self.assertEqual(task.description, 'my task')
        self.assertTrue(task.creation_date)
        res = command.TaskCommand.add('my task')
        self.assertEqual(res, {'err': 'The task exists with id: 1'})

        res = command.TaskCommand.add('my task2', bug_id='1234')
        self.assertEqual(res, {'success': 'Task 2 created.'})
        task = models.Task.query.get(2)
        self.assertEqual(task.description, 'my task2')
        self.assertEqual(task.bug_id, '1234')

        res = command.TaskCommand.add('my task3', project_id='1234')
        self.assertEqual(res, {'err': 'The project 1234 doesn\'t exist'})

        with transaction.manager:
            project = models.Project(name='project1')
            models.DBSession.add(project)

        models.DBSession.add(project)

        res = command.TaskCommand.add('my task3', project_id=project.idproject)
        self.assertEqual(res, {'success': 'Task 3 created.'})
        task = models.Task.query.get(3)
        self.assertEqual(task.project.idproject, project.idproject)
        self.assertEqual(task.status, None)
        self.assertEqual(task.completed_date, None)

        res = command.TaskCommand.add('my task4', status='resolved')
        self.assertEqual(res, {'success': 'Task 4 created.'})
        task = models.Task.query.get(4)
        self.assertEqual(task.status, 'resolved')
        self.assertTrue(task.completed_date)

    def test_start(self):
        res = command.TaskCommand.start(1)
        self.assertEqual(res, {'err': 'The task 1 doesn\'t exist!'})

        with transaction.manager:
            task = models.Task(description='task 1')
            models.DBSession.add(task)

        models.DBSession.add(task)
        self.assertEqual(task.times, [])

        res = command.TaskCommand.start(1)
        self.assertEqual(res, {'success': 'The task 1 is activated'})

        self.assertEqual(len(models.TaskTime.query.all()), 1)
        task = models.Task.query.get(1)
        self.assertTrue(len(task.times), 1)
        self.assertFalse(task.times[0].end_date)

        res = command.TaskCommand.start(1)
        self.assertEqual(res, {'err': 'The task 1 is already activated!'})

        with transaction.manager:
            task2 = models.Task(description='task 2')
            models.DBSession.add(task2)

        res = command.TaskCommand.start(2)
        self.assertEqual(
            res,
            {
                'command': 'start -f 2',
                'confirm': ('An other task 1 is already activated! '
                            'Do you want to stop it?')
            })

        res = command.TaskCommand.start(2, force=True)
        self.assertEqual(res, {
            'info': 'The task 1 is stopped!',
            'success': 'The task 2 is activated'
        })

        task1 = models.Task.query.get(1)
        task2 = models.Task.query.get(2)
        self.assertEqual(len(task1.times), 1)
        self.assertEqual(len(task2.times), 1)
        self.assertTrue(task1.times[0].end_date)
        self.assertFalse(task2.times[0].end_date)

    def test_stop(self):
        res = command.TaskCommand.stop()
        self.assertEqual(res, {'err': 'No active task!'})
        with transaction.manager:
            task = models.Task(description='task 1')
            models.DBSession.add(task)
        command.TaskCommand.start(1)
        res = command.TaskCommand.stop()
        self.assertEqual(res, {'success': 'The task 1 is stopped!'})
        task = models.Task.query.get(1)
        self.assertEqual(len(task.times), 1)
        self.assertTrue(task.times[0].end_date)

    def test_info(self):
        res = command.TaskCommand.info(1)
        self.assertEqual(res, {'err': 'The task 1 doesn\'t exist!'})

        task = models.Task(description='task 1')
        models.DBSession.add(task)
        res = command.TaskCommand.info(1)
        self.assertEqual(len(res), 1)
        self.assertTrue('Task 1:' in res['msg'])
        self.assertTrue('Duration:' not in res['msg'])

        tasktime = models.TaskTime(start_date=datetime.datetime.now())
        tasktime.task = task
        models.DBSession.add(task)

        res = command.TaskCommand.info(1)
        self.assertEqual(len(res), 1)
        self.assertTrue('Task 1:' in res['msg'])
        self.assertTrue('Duration:' in res['msg'])

    def test_active(self):
        res = command.TaskCommand.active()
        self.assertEqual(res, {'err': 'No active task!'})

        task = models.Task(description='task 1')
        tasktime = models.TaskTime(start_date=datetime.datetime.now())
        tasktime.task = task
        models.DBSession.add(task)
        res = command.TaskCommand.active()
        self.assertEqual(len(res), 1)
        self.assertTrue('Task 1:' in res['msg'])

    def test_modify(self):
        res = command.TaskCommand.modify(1)
        self.assertEqual(res, {'err': 'The task 1 doesn\'t exist!'})

        task = models.Task(description='task 1')
        with transaction.manager:
            models.DBSession.add(task)

        res = command.TaskCommand.modify(1)
        self.assertEqual(res, {'err': 'No parameter given!'})

        res = command.TaskCommand.modify(1, description='New description')
        self.assertEqual(res, {'success': 'The task 1 is modified'})
        task = models.Task.query.get(1)
        self.assertEqual(task.description, 'New description')

        res = command.TaskCommand.modify(1, project_id=1234)
        self.assertEqual(res, {'err': 'The project 1234 doesn\'t exist'})

        with transaction.manager:
            project = models.Project(name='project1')
            models.DBSession.add(project)

        models.DBSession.add(project)
        res = command.TaskCommand.modify(1, project_id=project.idproject)
        self.assertEqual(res, {'success': 'The task 1 is modified'})
        task = models.Task.query.get(1)
        self.assertEqual(task.project.idproject, project.idproject)
        self.assertEqual(task.status, None)
        self.assertEqual(task.completed_date, None)

        res = command.TaskCommand.modify(1, status='closed')
        self.assertEqual(res, {'success': 'The task 1 is modified'})
        task = models.Task.query.get(1)
        self.assertEqual(task.status, 'closed')
        self.assertTrue(task.completed_date)

        res = command.TaskCommand.modify(1, status='open')
        self.assertEqual(res, {'success': 'The task 1 is modified'})
        task = models.Task.query.get(1)
        self.assertEqual(task.status, 'open')
        self.assertFalse(task.completed_date)


class TestReportCommand(testing.DBTestCase):

    def test_today(self):
        from datetime import datetime
        with patch('datetime.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2014, 2, 8, 12, 0, 0)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            with patch('pytask.command._report') as mock_report:
                command.ReportCommand.today()
            mock_report.assert_called_with(mock_dt(2014, 2, 8),
                                           mock_dt(2014, 2, 8))

    def test_today_with_format(self):
        from datetime import datetime
        with patch('datetime.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2014, 2, 8, 12, 0, 0)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            with patch('pytask.command._report') as mock_report:
                command.ReportCommand.today(format='new')
            mock_report.assert_called_with(mock_dt(2014, 2, 8),
                                           mock_dt(2014, 2, 8),
                                           format='new')

    def test_week(self):
        from datetime import datetime

        with patch('datetime.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2014, 2, 2, 12, 0, 0)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            with patch('pytask.command._report') as mock_report:
                command.ReportCommand.week()
            mock_report.assert_called_with(mock_dt(2014, 1, 27),
                                           mock_dt(2014, 1, 31))
        for day in range(3, 10):
            with patch('datetime.datetime') as mock_dt:
                mock_dt.now.return_value = datetime(2014, 2, day, 12, 0, 0)
                mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
                with patch('pytask.command._report') as mock_report:
                    command.ReportCommand.week()
                mock_report.assert_called_with(mock_dt(2014, 2, 3),
                                               mock_dt(2014, 2, 7))

        with patch('datetime.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2014, 2, 10, 12, 0, 0)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            with patch('pytask.command._report') as mock_report:
                command.ReportCommand.week()
            mock_report.assert_called_with(mock_dt(2014, 2, 10),
                                           mock_dt(2014, 2, 14))

    def test_week_with_format(self):
        from datetime import datetime

        with patch('datetime.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2014, 2, 2, 12, 0, 0)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            with patch('pytask.command._report') as mock_report:
                command.ReportCommand.week(format='new')
            mock_report.assert_called_with(mock_dt(2014, 1, 27),
                                           mock_dt(2014, 1, 31),
                                           format='new')

    def test_date(self):
        from datetime import datetime

        with patch('datetime.datetime') as mock_dt:
            mock_dt.strptime.return_value = datetime(2014, 2, 3, 0, 0, 0)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            with patch('pytask.command._report') as mock_report:
                command.ReportCommand.date('2014/02/03', '2014/02/07')
            # NOTE: same date because of the mock
            mock_report.assert_called_with(mock_dt(2014, 2, 3),
                                           mock_dt(2014, 2, 3))

    def test_date_with_format(self):
        from datetime import datetime

        with patch('datetime.datetime') as mock_dt:
            mock_dt.strptime.return_value = datetime(2014, 2, 3, 0, 0, 0)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            with patch('pytask.command._report') as mock_report:
                command.ReportCommand.date('2014/02/03', '2014/02/07', format='new')
            # NOTE: same date because of the mock
            mock_report.assert_called_with(mock_dt(2014, 2, 3),
                                           mock_dt(2014, 2, 3), format='new')


class TestProjectCommand(testing.DBTestCase):

    def test_ls(self):
        res = command.ProjectCommand.ls()
        self.assertEqual(res, {'msg': 'No project!'})

        project = models.Project(name='my project')
        models.DBSession.add(project)
        res = command.ProjectCommand.ls()
        self.assertTrue('my project' in res['msg'])

    def test_add(self):
        res = command.ProjectCommand.add('my project')
        self.assertEqual(res, {'success': 'Project 1 created.'})
        project = models.Project.query.one()
        self.assertEqual(project.name, 'my project')
        res = command.ProjectCommand.add('my project')
        self.assertEqual(res, {'err': 'The project exists with id: 1'})

        res = command.ProjectCommand.add('my project2', bug_id='1234')
        self.assertEqual(res, {'success': 'Project 2 created.'})
        project = models.Project.query.get(2)
        self.assertEqual(project.name, 'my project2')
        self.assertEqual(project.bug_id, '1234')

    def test_modify(self):
        res = command.ProjectCommand.modify(1)
        self.assertEqual(res, {'err': 'The project 1 doesn\'t exist!'})

        project = models.Project(name='project 1')
        with transaction.manager:
            models.DBSession.add(project)

        res = command.ProjectCommand.modify(1)
        self.assertEqual(res, {'err': 'No parameter given!'})

        res = command.ProjectCommand.modify(1, name='New name')
        self.assertEqual(res, {'success': 'The project 1 is modified'})
        project = models.Project.query.get(1)
        self.assertEqual(project.name, 'New name')
