#!/bin/bash

[ "$0" = 'bash' ] || exec /usr/bin/env bash --rcfile "$0"

_cmd_cfg=(
	'add     alias'
	'start   alias'
	'stop    alias'
	'info    alias'
	'ls      alias'
	'active  alias'
)

for cfg in "${_cmd_cfg[@]}" ; do
	read cmd opts <<< $cfg
	for opt in $opts ; do
		case $opt in
			alias)   alias $cmd="pytask $cmd" ;;
		esac
	done
done
PS1='pytask> '

