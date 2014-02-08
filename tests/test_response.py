import unittest
from sqlalchemy import create_engine

import pytask.response as response
import pytask.models as models


class TestTaskCommand(unittest.TestCase):

    def setUp(self):
        engine = create_engine('sqlite://')
        models.DBSession.configure(bind=engine)
        models.Base.metadata.create_all(engine)

    def test_main(self):
        res = response.main(['prog'])
        self.assertEqual(res, response.usage())

        res = response.main(['prog', '-h'])
        self.assertEqual(res, response.usage())

        res = response.main(['prog', 'ls'])
        self.assertEqual(res, 'No task!')

        res = response.main(['prog', 'add'])
        self.assertTrue('Usage: add description' in res['err'])
        self.assertTrue('Missing parameter!' in res['err'])

        res = response.main(['prog', 'add', '-t'])
        self.assertTrue('Usage: add description' in res['err'])
        self.assertTrue('no such option: -t' in res['err'])

        res = response.main(['prog', 'add', 'my', 'task'])
        self.assertEqual(res, 'Task 1 created.')
