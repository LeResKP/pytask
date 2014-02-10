from . import testing

import pytask.response as response


class TestTaskCommand(testing.DBTestCase):

    def test_execute(self):
        res = response.execute(['prog'])
        self.assertEqual(res, {'msg': response.usage()})

        res = response.execute(['prog', '-h'])
        self.assertEqual(res, {'msg': response.usage()})

        res = response.execute(['prog', 'ls'])
        self.assertEqual(res, {'msg': 'No task!'})

        res = response.execute(['prog', 'add'])
        self.assertTrue("Usage: pytask add 'description'" in res['err'])
        self.assertTrue('Missing parameter!' in res['err'])

        res = response.execute(['prog', 'add', '-t'])
        self.assertTrue("Usage: pytask add 'description'" in res['err'])
        self.assertTrue('no such option: -t' in res['err'])

        res = response.execute(['prog', 'add', 'my', 'task'])
        self.assertEqual(res, {'success': 'Task 1 created.'})
