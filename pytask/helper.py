import inspect
from optparse import OptionParser


def indent(s, spaces):
    """Indent a multiline string
    """
    lines = s.split('\n')
    lines = [(spaces * ' ') + line for line in lines]
    return '\n'.join(lines)


class RaiseOptionParser(OptionParser):

    def error(self, msg):
        raise Exception(msg)

    def _add_help_option(self):
        """Don't display help message
        """
        self.add_option("-h", "--help",
                        action="help",
                        help="")


def alias(cmd, name):
    """Create an alias for the command named name.
    cmd is just the name of the real command. (Use for the help)
    """
    fname = 'command.%s' % name

    def go(*args, **kw):
        mod = __import__('pytask')
        for c in fname.split('.'):
            mod = getattr(mod, c)
        return mod(*args, **kw)
    go._alias = cmd
    return go


class Param(object):
    """Decorator to define the function parameters.
    It will help to generate the help.
    """

    def __init__(self, name, shortcut=None, required=False, **kw):
        self.name = name
        self.shortcut = shortcut
        self.required = required
        self.kw = kw

    def __call__(self, func):
        if not getattr(func, '_params', None):
            func._params = []
        func._params.insert(0, self)
        return func

    def __repr__(self):
        return ('<Param name={name} shortcut={shortcut} '
                'required={required}').format(**self.__dict__)


def get_option_parser(func):
    """Generate the OptionParser object for the given function
    """
    parser = RaiseOptionParser()
    required = []
    has_option = False
    for p in func._params:
        if p.required:
            required += [p.name]
            continue
        has_option = True
        args = ("--%s" % p.name, )
        if p.shortcut:
            args = ("-%s" % p.shortcut, "--%s" % p.name)
        parser.add_option(*args, **p.kw)
    usage = "pytask %s %s" % (func.__name__,
                              ' '.join(map(lambda x: "'%s'" % x, required)))
    if has_option:
        usage += " Options"
    parser.usage = usage
    return parser


class CommandMeta(type):
    """Set all the functions as static method and attach some data:
        * on functions we set the option parser to parse the command line
        * on class we set the available commands
    """
    def __new__(mcs, name, bases, dic):
        commands = []
        for k, v in dic.items():
            if k.startswith('_'):
                continue
            if inspect.isfunction(v):
                v._parser = None
                if getattr(v, '_params', None):
                    v._parser = get_option_parser(v)
                    v._nb_required = len([p for p in v._params if p.required])
                else:
                    v._parser = RaiseOptionParser(add_help_option=False)
                    v._parser.usage = 'pytask %s' % k
                    v._nb_required = 0
                dic[k] = staticmethod(v)
                commands += [k]
        dic['_commands'] = commands
        return type.__new__(mcs, name, bases, dic)
