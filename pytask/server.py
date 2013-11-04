import SocketServer
import cmd
import json
import inspect


AVAILABLE_CMDS = {}

def get_args(func):
    argspec = inspect.getargspec(func)
    required_args = argspec.args
    non_required_args = []
    if argspec.defaults:
        required_args = argspec.args[:len(argspec.defaults)]
        non_required_args = argspec.args[len(argspec.defaults):]
    return required_args, non_required_args, argspec.args


AVAILABLE_CMDS = {}
for k, v in cmd.__dict__.items():
    if k.startswith('_'):
        continue
    if inspect.isfunction(v):
        required_args, non_required_args, args = get_args(v)
        AVAILABLE_CMDS[k] = {
            'func': v,
            'args': args,
            'required_args': required_args,
            'non_required_args': non_required_args,
        }


def parse_cmd_line(line):
    lis = line.split(' ')
    func = lis.pop(0)
    if func not in AVAILABLE_CMDS:
        return 'Unavailable command %s' % func

    dic = AVAILABLE_CMDS[func]

    kw = {}
    for k, v in zip(dic['args'], lis):
        kw[k] = v

    if len(lis) > len(dic['args']):
        kw[k] += ' %s' %  (' '.join(lis[len(dic['args']):]))

    for k in dic['required_args']:
        if k not in kw:
            raise Exception('Missing required arg %s' % k)

    return func, kw


def run_cmd(data):
    func, kw = parse_cmd_line(data)
    func = getattr(cmd, func)
    return json.dumps(func(**kw))


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
    HOST, PORT = "localhost", 9999

    # Create the server, binding to localhost on port 9999
    server = SocketServer.TCPServer((HOST, PORT), TaskTCPHandler)

    print 'Server running on %s:%s' % (HOST, PORT)
    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()


if __name__ == "__main__":
    main()
