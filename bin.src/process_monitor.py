import sys
import time
import pickle
import subprocess
from collections import defaultdict
import psutil
import numpy as np

class RssHistory:
    def __init__(self):
        self.time = []
        self.rss = []
    def append(self, time, rss):
        self.time.append(time)
        self.rss.append(rss)

if __name__ == '__main__':
    try:
        process_string = sys.argv[1]
    except IndexError:
        process_string = 'run_sensors'

    process_memories = defaultdict(RssHistory)

    command = 'ps auxww | grep jchiang8 | grep {} | grep -v grep | grep -v process_monitor'\
        .format(process_string)

    while(True):
        try:
            lines = subprocess.check_output(command, shell=True).decode('utf-8')
        except subprocess.CalledProcessError as eobj:
            break
        lines = lines.strip().split('\n')
        pids = sorted([int(line.split()[1]) for line in lines])
        for pid in pids:
            proc = psutil.Process(pid)
            process_memories[pid].append(time.time(),
                                         proc.memory_info().rss/1024.**3)
        time.sleep(2.)
        pickle.dump(process_memories, open('process_info.pkl', 'wb'))
