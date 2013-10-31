import SocketServer
import cmd


def run_cmd(data):
    lis = data.split(' ')
    method = lis[0]
    args = ' '.join(lis[1:])
    func = getattr(cmd, method, None)
    if not func:
        return 'Undefined method'
    return func(args)


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
        self.request.sendall(run_cmd(self.data))

if __name__ == "__main__":
    HOST, PORT = "localhost", 9999

    # Create the server, binding to localhost on port 9999
    server = SocketServer.TCPServer((HOST, PORT), TaskTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
