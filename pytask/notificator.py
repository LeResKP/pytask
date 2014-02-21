import time
import socket
import json
from pytask import command, models
from daemon import runner
import datetime


HOST, PORT = "localhost", 9999


def send_notification(title, msg):
    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to server and send data
        sock.connect((HOST, PORT))
        data = json.dumps({
            'title': title,
            'msg': msg,
        })
        sock.sendall(data + "\n")
    finally:
        sock.close()


NOTIFY_NO_TASK = 1
NOTIFY_TASK = 2


class Notificator():

    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path = '/tmp/pytask-notificator.pid'
        self.pidfile_timeout = 5

    def run(self):
        cache = {}
        while True:
            active = models.Status.query.one().active
            if not active:
                time.sleep(5)
                continue

            tasktime = command.get_active_tasktime()
            if not tasktime:
                now = datetime.datetime.utcnow()
                send = True
                if NOTIFY_NO_TASK in cache:
                    delta = now - cache[NOTIFY_NO_TASK]
                    if delta < datetime.timedelta(seconds=5):
                        send = False
                if send:
                    send_notification('pytask', 'No task activated')
                    cache[NOTIFY_NO_TASK] = datetime.datetime.utcnow()
            else:
                now = datetime.datetime.utcnow()
                send = True
                if NOTIFY_TASK in cache:
                    delta = now - cache[NOTIFY_TASK]
                    if delta < datetime.timedelta(seconds=5):
                        send = False
                if send:
                    send_notification(
                        'pytask',
                        'The task %i is always activated:\n %s ' % (
                            tasktime.idtask,
                            tasktime.task.description
                        ))
                    cache[NOTIFY_TASK] = datetime.datetime.utcnow()
            time.sleep(2)


def main():
    app = Notificator()
    daemon_runner = runner.DaemonRunner(app)
    daemon_runner.do_action()


if __name__ == '__main__':
    main()
