import unittest
from sqlalchemy import create_engine

import pytask.command as command
import pytask.models as models


class TestTaskCommand(unittest.TestCase):

    def setUp(self):
        engine = create_engine('sqlite://')
        models.DBSession.configure(bind=engine)
        models.Base.metadata.create_all(engine)

    def tearDown(self):
        models.DBSession.remove()

    def test_ls(self):
        res = command.TaskCommand.ls()
        self.assertEqual(res, 'No task!')

        task = models.Task(description='my task')
        models.DBSession.add(task)
        res = command.TaskCommand.ls()
        self.assertEqual(res, '1 my task')

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
