import os
import psutil

class ProcessTracker:
    def __init__(self, output, pid=None, mode='w'):
        if pid is None:
            pid = os.getpid()
        self.process = psutil.Process(pid)
        self.output = open(output, mode) if isinstance(output, str) else output

    def __del__(self):
        self.output.close()

    def start_timer(self):
        self.tstart = self.process.cpu_times().user

    def elapsed_time(self):
        return self.process.cpu_times().user - self.tstart

    def write(self, *args):
        cputime = self.process.cpu_times().user
        rss_mem = self.process.memory_info().rss/1024.**3
        template = '  '.join(['{}', '{}'] + len(args)*['{}']) + '\n'
        self.output.write(template.format(cputime, rss_mem, *args))
        self.output.flush()
