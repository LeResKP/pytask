from ..response import COMMANDS

tmpl = '''#!/bin/bash

[ "$0" = 'bash' ] || exec /usr/bin/env bash --rcfile "$0"

_cmd_cfg=(
%(commands)s
)

for cfg in "${_cmd_cfg[@]}" ; do
    read cmd opts <<< $cfg
    for opt in $opts ; do
        case $opt in
            alias)   alias $cmd="pytask $cmd" ;;
            longalias)   alias $cmd="pytask $cmd | less -F" ;;
        esac
    done
done
PS1='pytask> '
'''


def main():
    commands = []
    for name, cls in COMMANDS.iteritems():
        if name == 'task':
            commands += list(cls._commands)
        else:
            commands += [name]

    s = ["    'help longalias'"]
    for command in commands:
        s += ["    '%s alias'" % command]
    print tmpl % dict(commands='\n'.join(s))

if __name__ == '__main__':
    main()
