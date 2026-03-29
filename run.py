# -*- coding: utf-8 -*-
import os, sys

'''
# No longer necessary as the public build has no console
if not __debug__:
    class HideOutput():
        def __init__(self):
            pass
        def write(self, string):
            pass
        def flush(self):
            pass
    sys.stdout = HideOutput()
    sys.stderr = HideOutput()
'''

print 'Starting Ace of Spades...'
print 'Debug: %s' % __debug__
PROGRESSBAR_ICON_BASE = 0x50
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)

os.chdir(os.path.join(os.getcwd(), application_path))
sys.path.insert(1, sys.path[0] + "/../common")

def init_log():
    global logging_file
    import sys, time, os
    from twisted.python import log
    from twisted.python.logfile import DailyLogFile

    log_file = "./logs/log.txt"
    try:
        os.makedirs(os.path.dirname(log_file))
    except OSError:
        pass
    logging_file = DailyLogFile(log_file, '.')
    log.addObserver(log.FileLogObserver(logging_file).emit)
    log.startLogging(sys.stdout)
    log.msg('AoS client started on %s' % time.strftime('%c'))
    log.startLogging(sys.stdout) # force twisted logging

if '+debug' in sys.argv:
    init_log()

try:
    import aoslib.run
except SystemExit:
    pass

# TODO : This should only be executed for standalone builds. How to detect that?
#try:
#    import aoslib.run
#except Exception as e:
#    import traceback
#    print traceback.format_exc()
#    logging_file.flush() # Flush on error
