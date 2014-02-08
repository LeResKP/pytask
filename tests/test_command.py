from . import testing
import pytask.command as command
import pytask.models as models
import datetime
import transaction


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


class TestTaskCommand(testing.DBTestCase):

    def test_ls(self):
        res = command.TaskCommand.ls()
        self.assertEqual(res, 'No task!')

        task = models.Task(description='my task')
        models.DBSession.add(task)
        res = command.TaskCommand.ls()
        self.assertEqual(res, '1 my task ')

    def test_add(self):
        res = command.TaskCommand.add('my task')
        self.assertEqual(res, 'Task 1 created.')
        task = models.Task.query.one()
        self.assertEqual(task.description, 'my task')
        self.assertTrue(task.creation_date)
        try:
            command.TaskCommand.add('my task')
        except Exception, e:
            self.assertEqual(str(e), 'The task exists with id: 1')

        res = command.TaskCommand.add('my task2', bug_id='1234')
        self.assertEqual(res, 'Task 2 created.')
        task = models.Task.query.get(2)
        self.assertEqual(task.description, 'my task2')
        self.assertEqual(task.bug_id, '1234')

    def test_start(self):
        res = command.TaskCommand.start(1)
        self.assertEqual(res, {'err': 'The task 1 doesn\'t exist!'})

        with transaction.manager:
            task = models.Task(description='task 1')
            models.DBSession.add(task)

        models.DBSession.add(task)
        self.assertEqual(task.times, [])

        res = command.TaskCommand.start(1)
        self.assertEqual(res, 'The task 1 is activated')

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
        self.assertEqual(res,
                         'The task 1 is stopped!\nThe task 2 is activated')

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
        self.assertEqual(res, 'The task 1 is stopped!')
        task = models.Task.query.get(1)
        self.assertEqual(len(task.times), 1)
        self.assertTrue(task.times[0].end_date)

    def test_info(self):
        res = command.TaskCommand.info(1)
        self.assertEqual(res, {'err': 'The task 1 doesn\'t exist!'})

        task = models.Task(description='task 1')
        models.DBSession.add(task)
        res = command.TaskCommand.info(1)
        self.assertTrue('Task 1:' in res)
        self.assertTrue('Duration:' not in res)

        tasktime = models.TaskTime(start_date=datetime.datetime.now())
        tasktime.task = task
        models.DBSession.add(task)

        res = command.TaskCommand.info(1)
        self.assertTrue('Task 1:' in res)
        self.assertTrue('Duration:' in res)

    def test_active(self):
        res = command.TaskCommand.active()
        self.assertEqual(res, {'err': 'No active task!'})

        task = models.Task(description='task 1')
        tasktime = models.TaskTime(start_date=datetime.datetime.now())
        tasktime.task = task
        models.DBSession.add(task)
        res = command.TaskCommand.active()
        self.assertTrue('Task 1:' in res)

    def test_modify(self):
        res = command.TaskCommand.modify(1)
        self.assertEqual(res, {'err': 'The task 1 doesn\'t exist!'})

        task = models.Task(description='task 1')
        with transaction.manager:
            models.DBSession.add(task)

        res = command.TaskCommand.modify(1)
        self.assertEqual(res, {'err': 'No parameter given!'})

        res = command.TaskCommand.modify(1, description='New description')
        self.assertEqual(res, 'The task 1 is modified')
        task = models.Task.query.get(1)
        self.assertEqual(task.description, 'New description')
