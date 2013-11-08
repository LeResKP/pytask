#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import SocketServer
import cmd
import json
import inspect
import re


AVAILABLE_CMDS = {}

regex_dq = re.compile(r'("[^"]+")')


def get_args(func):
    argspec = inspect.getargspec(func)
    args = argspec.args[1:]
    required_args = args[:]
    non_required_args = []
    defaults = argspec.defaults
    if defaults:
        if len(defaults) == len(args):
            required_args = []
            non_required_args = args[:]
        else:
            required_args = args[:len(defaults)]
            non_required_args = args[len(defaults):]
    dic = {
        'required_args': required_args,
        'non_required_args': non_required_args,
        'args': args,
        'func': func,
    }
    return dic


AVAILABLE_CMDS = {
    'report': {},
    '': {},
}

for k, v in cmd.TaskCmd.available_cmds.items():
    dic = get_args(v)
    # dic['func'] = getattr(cmd.TaskCmd, dic['func'])
    dic['cls'] = cmd.TaskCmd
    AVAILABLE_CMDS[''][k] = dic

for k, v in cmd.ReportCmd.available_cmds.items():
    dic = get_args(v)
    # dic['func'] = getattr(cmd.ReportCmd, dic['func'])
    dic['cls'] = cmd.ReportCmd
    AVAILABLE_CMDS['report'][k] = dic


    # print k, v
    # if k.startswith('_'):
    #     continue
    # if inspect.isfunction(v):
    #     dic = get_args(v)
    #     AVAILABLE_CMDS[k] = dic


def replacer(match):
    return match.group(1).replace(' ', u'µ')


def parse_cmd_line(line):
    line = regex_dq.sub(replacer, line)
    lis = line.split(' ')
    func = lis.pop(0)
    dic = AVAILABLE_CMDS['']
    if func in AVAILABLE_CMDS:
        dic = AVAILABLE_CMDS[func]
        func = lis.pop(0)

    if func not in dic:
        raise Exception('Unavailable command %s' % func)

    dic = dic[func]

    kw = {}
    to_remove = []
    for v in lis:
        for a in dic['non_required_args']:
            if v.startswith('%s:' % a):
                value = v.replace('%s:' % a, '').replace(u'µ', ' ')
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                kw[a] = value
                to_remove += [v]

    for v in to_remove:
        lis.remove(v)

    args = dic['required_args'][:]
    if not getattr(dic['func'], 'key_required', False):
        args += dic['non_required_args']

    lis = [l.replace(u'µ', ' ') for l in lis]
    for k, v in zip(args, lis):
        if k in kw:
            continue
        kw[k] = v

    if kw and len(lis) > len(args):
        kw[k] += ' %s' % (' '.join(lis[len(args):]))

    for k in dic['required_args']:
        if k not in kw:
            raise Exception('Missing required arg %s' % k)

    return dic['func'], dic['cls'], kw


def run_cmd(data):
    func, cls, kw = parse_cmd_line(data)
    # func = getattr(cmd.TaskCmd, func)
    return json.dumps(func(cls, **kw))


class TaskTCPHandler(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        # print "{} wrote:".format(self.client_address[0])
        # print self.data
        d = run_cmd(self.data)
        self.request.sendall(d)


def main():

    print cmd.TaskCmd()
    HOST, PORT = "localhost", 9999

    # Create the server, binding to localhost on port 9999
    server = SocketServer.TCPServer((HOST, PORT), TaskTCPHandler)

    print 'Server running on %s:%s' % (HOST, PORT)
    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()


if __name__ == "__main__":
    main()
