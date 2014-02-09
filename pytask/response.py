import sys
import shlex
from colorterm import colorterm
from .command import TaskCommand, ReportCommand, ProjectCommand


COMMAND_CLASSES = [TaskCommand, ProjectCommand, ReportCommand]

COMMANDS = {}
for cls in COMMAND_CLASSES:
    COMMANDS[cls._command] = cls


def get_command_class(cmd):
    """Get the command class
    """
    if cmd in COMMANDS:
        return COMMANDS[cmd]
    return None


def usage():
    """Usage of pytask
    """
    s = []
    for cls in COMMAND_CLASSES:
        s += [cls.usage()]
    return '\n\n'.join(s)


def execute(argv=sys.argv):
    """Parse the command line and call the corresponding method
    """
    if ''.join(argv[1:]).strip() in ['-h', '--help', 'help']:
        return {'msg': usage()}

    if len(argv) < 2:
        return {'msg': usage()}

    cmd = argv[1]
    consume = 2
    command_class = get_command_class(cmd)
    if not command_class:
        command_class = TaskCommand
    else:
        consume = 3
        if len(argv) < 3:
            return {
                'err': 'Error: Missing parameter!'
            }
        cmd = argv[2]

    if cmd not in getattr(command_class, '_commands'):
        return {'err': 'Command %s not found!' % cmd}

    func = getattr(command_class, cmd)
    if not func._parser:
        return func()

    try:
        (options, args) = func._parser.parse_args(argv[consume:])
    except Exception, e:
        return {'err': '%s\nError: %s' % (
            func._parser.format_help(),
            str(e))}
    nb = func._nb_required
    if len(args) < nb:
        return {
            'err': '%s\nError: Missing parameter!' % func._parser.format_help()
        }

    tmp = args[:nb]
    if len(args) > nb:
        tmp[-1] += ' ' + ' '.join(args[nb:])
    return func(*tmp, **vars(options))


def print_error(s):
    print >> sys.stderr, colorterm.red(s)


def print_msg(s):
    print s


def print_info(s):
    print colorterm.blue(s)


def print_success(s):
    print colorterm.green(s)


def main(command_str=None):
    if command_str:
        res = execute(shlex.split(command_str))
    else:
        res = execute()

    if not isinstance(res, dict):
        print >> sys.stderr, 'Bad response'
        exit(1)

    if 'err' in res:
        print_error(res['err'])
    if 'info' in res:
        print_info(res['info'])
    if 'success' in res:
        print_success(res['success'])
    if 'msg' in res:
        print_msg(res['msg'])
    if 'confirm' in res:
        s = raw_input(res['confirm'] + ' (Y/n):')
        if s.strip() in ['y', '']:
            main('prog ' + res['command'])
        else:
            print_info('Operation aborted!')


if __name__ == '__main__':
    main()
