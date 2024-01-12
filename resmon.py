import enum
import multiprocessing
import psutil
import time
import timeit
import numpy as np


class TrackerState(enum.Enum):
    INITIALIZED = enum.auto()
    RUNNING = enum.auto()
    STOPPED = enum.auto()


class ResourceTracker:
    def __init__(self, interval=1, timer=timeit.default_timer):
        """An instance of this class will log system memory and cpu usage in the
        background start() until stop()."""

        self.state = TrackerState.INITIALIZED
        self.parent_conn, child_conn = multiprocessing.Pipe()
        self.timestamps = None
        self.memory = None
        self.cpu = None

        def runner(pipe_conn):
            timestamp_l, memory_l, cpu_l = [], [], []
            while True:
                if pipe_conn.poll():
                    break
                ts, mem, cpu = (
                    timer(),
                    psutil.virtual_memory().percent,
                    psutil.cpu_percent(),
                )
                timestamp_l.append(ts)
                memory_l.append(mem)
                cpu_l.append(cpu)
                time.sleep(interval)
            pipe_conn.send((timestamp_l, memory_l, cpu_l))

        self.proc = multiprocessing.Process(target=runner, args=(child_conn,))

    def start(self):
        """Spawn background process to gather data.

        Note: Can only do this once for a given ResourceTracker; just make more
        if needed (they're cheap)."""

        assert (
            self.state is TrackerState.INITIALIZED
        ), "Can only start once"
        self.proc.start()
        self.state = TrackerState.RUNNING

    def stop(self):
        """Stop tracking (may wait up to interval), capture results."""

        assert (
            self.state is TrackerState.RUNNING
        ), "Can only stop if already running"
        self.parent_conn.send("Stop it right there!")
        self.proc.join()
        self.state = TrackerState.STOPPED
        ts_l, mem_l, cpu_l = self.parent_conn.recv()

        self.timestamps = np.array(ts_l)
        self.memory = np.array(mem_l)
        self.cpu = np.array(cpu_l)

    def get_results(self):
        """Returns list of (timestamp, memory consumption in bytes)."""

        assert (
            self.state is TrackerState.STOPPED
        ), "Can only get results after stopping"

        return self.timestamps, self.memory, self.cpu
