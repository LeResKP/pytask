import sys
from .command import TaskCommand


def indent(s, spaces):
    """Indent a multiline string
    """
    lines = s.split('\n')
    lines = [(spaces * ' ') + line for line in lines]
    return '\n'.join(lines)


def usage():
    """Usage of pytask
    """
    s = []
    for c in TaskCommand._commands:
        func = getattr(TaskCommand, c)
        s += ['%s: %s' % (c, func.__doc__.strip())]
        if func._parser:
            s += [indent(func._parser.format_help(), 4)]
    return '\n'.join(s)


def main(argv=sys.argv):
    """Parse the command line and call the corresponding method
    """
    if ''.join(argv[1:]).strip() in ['-h', '--help']:
        return usage()

    if len(argv) < 2:
        return usage()

    cmd = argv[1]
    if cmd not in TaskCommand._commands:
        return {'err': 'Command %s not found!' % cmd}

    func = getattr(TaskCommand, cmd)
    if not func._parser:
        return func()

    try:
        (options, args) = func._parser.parse_args(argv[2:])
    except Exception, e:
        return {'err': '%s\nError: %s' % (
            func._parser.format_help(),
            str(e))}
    nb = TaskCommand.add._nb_required
    if len(args) < nb:
        return {
            'err': '%s\nError: Missing parameter!' % func._parser.format_help()
        }

    tmp = args[:nb]
    tmp[-1] += ' ' + ' '.join(args[nb:])
    return func(*tmp, **vars(options))


if __name__ == '__main__':
    res = main()
    if isinstance(res, dict) and 'err' in res:
        print >> sys.stderr, res['err']
        exit(1)
    print res
