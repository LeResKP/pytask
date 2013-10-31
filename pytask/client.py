import sys
import os
import socket
import json
import tempfile
import subprocess


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s cmd' % cmd)
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)

    if argv[1] == 'serve':
        import server
        server.main()
        sys.exit(0)

    HOST, PORT = "localhost", 9999
    data = " ".join(sys.argv[1:])

    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to server and send data
        sock.connect((HOST, PORT))
        sock.sendall(data + "\n")
        # Receive data from the server and shut down
        received = sock.recv(1024)
        res = json.loads(received)
        if 'editor' in res:
            n, f = tempfile.mkstemp()
            print res['content']
            open(f, 'w').write(res['content'])
            subprocess.Popen(['vi %s' % f], shell=True).wait()
            # os.popen('vim %s' % f)
            new = open(f, 'r').read()
            print new
            print f
            print type(f)
            res['content'] = new
            c = '%(action)s %(idtask)s %(content)s' % res
            sock.sendall(data + "\n")
            # Receive data from the server and shut down
            received = sock.recv(1024)
            res = json.loads(received)
            print 'RES', res
        elif 'stdout' in res:
            print res['stdout']
        else:
            print 'Response not supported'

    finally:
        sock.close()
