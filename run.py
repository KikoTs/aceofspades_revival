# -*- coding: utf-8 -*-
import os, sys, subprocess

from retail_compat import install_literal_eval_guard

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
    application_path = os.path.dirname(os.path.abspath(sys.executable))
elif __file__:
    application_path = os.path.dirname(os.path.abspath(__file__))

os.chdir(application_path)
sys.path.insert(1, os.path.abspath(os.path.join(sys.path[0], "..", "common")))


# Install this before aoslib imports the compiled HUD module.
install_literal_eval_guard()
# Install before aoslib.run schedules GameManager.update. LoadingMenu then
# acknowledges each retained-peer map transition before InitialInfo is sent.
import session_transition_patch

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

    if sys.argv[0] != "launcher.py":
        log.startLogging(logging_file, setStdout=True)

    if sys.argv[0] == "launcher.py":
        log.addObserver(log.FileLogObserver(logging_file).emit)
        log.startLogging(sys.stdout)

    log.msg('AoS client started on %s' % time.strftime('%c'))

    if sys.argv[0] == "launcher.py":
        log.startLogging(sys.stdout) # force twisted logging

if '+debug' in sys.argv:
    init_log()
    if sys.argv[0] != "launcher.py":
        # debugger.exe is an optional frozen-build log viewer. Source runs do
        # not contain it, and a missing/corrupt viewer must never abort the
        # actual game bootstrap.
        debugger_path = os.path.join(application_path, "debugger.exe")
        if os.path.isfile(debugger_path):
            try:
                subprocess.Popen([debugger_path], cwd=application_path)
            except (OSError, ValueError) as error:
                print 'Could not start optional debugger viewer: %s' % error
        else:
            print 'Optional debugger viewer not found: %s' % debugger_path

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
