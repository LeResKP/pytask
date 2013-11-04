import unittest

import pytask.server as server


class TestServer(unittest.TestCase):

    def test_parse_cmd_line(self):
        cmd, kw = server.parse_cmd_line('add new task 1')
        self.assertEqual(cmd, 'add')
        self.assertEqual(kw, {'idtask': 'new task 1'})
        assert(False)
