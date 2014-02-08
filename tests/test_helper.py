import unittest
import sys
import StringIO
import pytask.helper as helper
import shlex


class TestHelper(unittest.TestCase):

    def test_param(self):
        param = helper.Param('description')
        self.assertEqual(param.name, 'description')

        func = lambda: True
        res = param(func)
        self.assertEqual(res, func)
        self.assertEqual(res._params, [param])

        param2 = helper.Param('bug_id', 'b', required=True)
        self.assertEqual(param2.name, 'bug_id')
        self.assertEqual(param2.shortcut, 'b')
        self.assertEqual(param2.required, True)

        res = param2(func)
        self.assertEqual(res._params, [param2, param])

    def test_get_option_parser(self):
        param = helper.Param('description', required=True)
        func = lambda: True
        res = param(func)
        parser = helper.get_option_parser(res)
        try:
            stderr = sys.stderr
            sys.stderr = StringIO.StringIO()
            parser.parse_args(shlex.split('hello -t world'))
            assert(False)
        except SystemExit, e:
            self.assertEqual(str(e), '2')
        finally:
            sys.stderr = stderr

        param2 = helper.Param('test', 't', required=True)
        res = param2(func)
        parser = helper.get_option_parser(res)
        try:
            stderr = sys.stderr
            sys.stderr = StringIO.StringIO()
            parser.parse_args(shlex.split('hello -t world'))
            assert(False)
        except SystemExit, e:
            self.assertEqual(str(e), '2')
        finally:
            sys.stderr = stderr

        func = lambda: True
        param2 = helper.Param('test', 't')
        res = param2(func)
        parser = helper.get_option_parser(res)
        (options, args) = parser.parse_args(shlex.split('hello -t world'))
        self.assertEqual(vars(options), {'test': 'world'})
        self.assertEqual(args, ['hello'])

    def test_command_meta(self):

        class TestMeta(object):
            __metaclass__ = helper.CommandMeta

            @helper.Param('description')
            @helper.Param('test', required=True)
            def test():
                return 'Hello world'

            def test1():
                return 'test1'

        self.assertEqual(TestMeta._commands, ['test', 'test1'])
        self.assertTrue(TestMeta.test._parser)
        self.assertEqual(TestMeta.test._nb_required, 1)
        self.assertEqual(TestMeta.test1._parser, None)

        res = TestMeta.test()
        self.assertEqual(res, 'Hello world')
