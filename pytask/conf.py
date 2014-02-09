import ConfigParser
import os

config = ConfigParser.ConfigParser()
config.read(['pytask.cfg', os.path.expanduser('~/.pytask')])
