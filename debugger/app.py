# -*- coding: utf-8 -*-

import os
import sys
import time

program_dir = os.path.dirname(
    os.path.abspath(sys.executable)
)

log_path = os.path.join(
    program_dir,
    'logs',
    'log.txt'
)

log_dir = os.path.dirname(log_path)

if not os.path.isdir(log_dir):
    os.makedirs(log_dir)

if not os.path.isfile(log_path):
    open(log_path, 'ab').close()

log_file = open(log_path, 'rb')

try:
    while True:
        line = log_file.readline()

        if line:
            sys.stdout.write(line)
            sys.stdout.flush()
        else:
            # Если файл был очищен
            if os.path.getsize(log_path) < log_file.tell():
                log_file.close()
                log_file = open(log_path, 'rb')

            time.sleep(0.1)

except KeyboardInterrupt:
    pass

finally:
    log_file.close()