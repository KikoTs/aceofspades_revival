import time
from shared.constants import DEBUG_BUILD
WINDOW = 10
ENABLED = DEBUG_BUILD

class Entry(object):
    time_spent = 0.0

    def __init__(self):
        self.entries = []
        self.start_time = 0
        self.max = 0.0
        self.frame_time = 0.0

    def start(self):
        self.start_time = time.clock()

    def stop(self):
        dt = time.clock() - self.start_time
        self.frame_time += dt

    def new_frame(self):
        self.time_spent += self.frame_time
        self.entries.append(self.frame_time)
        if self.frame_time > self.max:
            self.max = self.frame_time
        if len(self.entries) > WINDOW:
            old_dt = self.entries.pop(0)
            self.time_spent -= old_dt
        self.frame_time = 0.0

    def get_average(self):
        return self.time_spent / len(self.entries)

    def get_max(self):
        current = self.max
        self.max = 0.0
        return current


class Profiler(object):
    start_time = None
    entry = None

    def __init__(self):
        self.entries = {}
        self.entry_list = []
        try:
            from aoslib.text import Label
            self.label = Label(font_name='', font_size=14, bold=False, color=(255,
                                                                              255,
                                                                              255,
                                                                              255))
        except:
            pass

    def start(self, name):
        self.entry_list.append(self.entry)
        try:
            entry = self.entries[name]
        except KeyError:
            entry = Entry()
            self.entries[name] = entry

        self.entry = entry
        entry.start()
        entry.indent = len(self.entry_list) - 1

    def stop(self):
        self.entry.stop()
        self.entry = self.entry_list.pop()

    def new_frame(self):
        for entry in self.entries.itervalues():
            entry.new_frame()

    def print_status(self):
        for name, entry in self.entries.iteritems():
            print '%s: %.4fms (%.4fms)' % (name, entry.get_average() * 1000.0, entry.get_max() * 1000.0)

        print ''

    def display_status(self, window):
        entry_array = []
        for name, entry in self.entries.iteritems():
            entry_array.append([name, entry])

        sorted_array = sorted(entry_array, key=(lambda item: item[1].start_time))
        y = 50
        from pyglet import gl
        for name, entry in sorted_array:
            self.label.text = '%s: %.2fms' % (name, entry.get_average() * 1000.0)
            gl.glPushMatrix()
            gl.glTranslatef(5 + entry.indent * 15, window.height - y, 0.0)
            self.label.draw_shadowed()
            gl.glPopMatrix()
            y += 18


if ENABLED:
    profiler = Profiler()
    start = profiler.start
    stop = profiler.stop
    print_status = profiler.print_status
    display_status = profiler.display_status
    new_frame = profiler.new_frame
else:

    def dummy(*arg, **kw):
        pass


    start = stop = print_status = display_status = new_frame = dummy
