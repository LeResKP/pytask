import unittest

import json
import pytask.server as server


class TestServer(unittest.TestCase):

    def test_get_args(self):

        def func(cls):
            pass

        expected = {
            'non_required_args': [],
            'args': [],
            'required_args': [],
            'func': func,
        }
        res = server.get_args(func)
        self.assertEqual(res, expected)

        def func(cls, idtask):
            pass

        expected = {
            'non_required_args': [],
            'args': ['idtask'],
            'required_args': ['idtask'],
            'func': func,
        }
        res = server.get_args(func)
        self.assertEqual(res, expected)

        def func(cls, idtask, description):
            pass

        expected = {
            'non_required_args': [],
            'args': ['idtask', 'description'],
            'required_args': ['idtask', 'description'],
            'func': func,
        }
        res = server.get_args(func)
        self.assertEqual(res, expected)

        def func(cls, idtask, description=None):
            pass

        expected = {
            'non_required_args': ['description'],
            'args': ['idtask', 'description'],
            'required_args': ['idtask'],
            'func': func,
        }
        res = server.get_args(func)
        self.assertEqual(res, expected)

    def test_parse_cmd_line(self):
        try:
            cmd, kw = server.parse_cmd_line('unexisting')
            assert(False)
        except Exception, e:
            self.assertEqual(str(e), 'Unavailable command unexisting')

        cmd, kw = server.parse_cmd_line('add new task 1')
        self.assertEqual(cmd, 'add')
        self.assertEqual(kw, {'description': 'new task 1'})

        cmd, kw = server.parse_cmd_line('add new task 1 project:1')
        self.assertEqual(cmd, 'add')
        self.assertEqual(kw, {'description': 'new task 1', 'project': '1'})

        cmd, kw = server.parse_cmd_line('add project:1 new task 1')
        self.assertEqual(cmd, 'add')
        self.assertEqual(kw, {'description': 'new task 1', 'project': '1'})

        cmd, kw = server.parse_cmd_line('add project:"project 1" new task 1')
        self.assertEqual(cmd, 'add')
        self.assertEqual(kw, {'description': 'new task 1',
                              'project': 'project 1'})

        cmd, kw = server.parse_cmd_line('ls')
        self.assertEqual(cmd, 'ls')
        self.assertEqual(kw, {})

        cmd, kw = server.parse_cmd_line('ls something')
        self.assertEqual(cmd, 'ls')
        self.assertEqual(kw, {})

        d = json.dumps({'a': 1, 'b': 2})
        cmd, kw = server.parse_cmd_line('update 1 %s' % d)
        self.assertEqual(cmd, 'update')
        self.assertEqual(kw, {'idtask': '1',
                              'json_content': d})

        cmd, kw = server.parse_cmd_line('today')
        self.assertEqual(cmd, 'today')
        self.assertEqual(kw, {})

        cmd, kw = server.parse_cmd_line('today -1')
        self.assertEqual(cmd, 'today')
        self.assertEqual(kw, {'delta': '-1'})

        try:
            cmd, kw = server.parse_cmd_line('add')
            assert(False)
        except Exception, e:
            self.assertEqual(str(e), 'Missing required arg description')
