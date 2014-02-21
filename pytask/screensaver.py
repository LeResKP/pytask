import dbus
import gobject
from dbus.mainloop.glib import DBusGMainLoop

from pytask import models, command
import transaction



class PytaskScreensaver(object):

    def __init__(self):
        dbus_loop = DBusGMainLoop()
        bus = dbus.SessionBus(mainloop=dbus_loop)
        bus.add_signal_receiver(self.set_status,
                                signal_name='ActiveChanged',
                                dbus_interface='org.gnome.ScreenSaver')
        self.active = True
        self.last_taskid = None
        gobject.MainLoop().run()

    def set_status(self, status):
        self.active = not status
        if status:
            # The screensaver is enabled
            print 'screen saver enabled'
            tasktime = command.get_active_tasktime()
            if tasktime:
                self.last_taskid = tasktime.idtask
                print command.TaskCommand.stop()
                print 'task stopped'
        else:
            if self.last_taskid:
                print 'Restart task'
                print command.TaskCommand.start(self.last_taskid)
                self.last_taskid = None

        # Update the status table which is used by the notification daemon.
        dbstatus = models.Status.query.one()
        with transaction.manager:
            dbstatus.active = self.active


if __name__ == '__main__':
    PytaskScreensaver()
