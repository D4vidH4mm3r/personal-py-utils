import dataclasses
import functools
import timeit


class ContextTimer:
    """Context manager measuring time spent in context.

    Keyword arguments:
    name: if not None, will appear in string representation
          also, if not None, will automatically print self when done
    timer: which timer class to use (defaults to timeit's default)
    """

    def __init__(self, name=None, timer=timeit.default_timer):
        self.timer = timer
        self.stop_time = None
        self.name = name

    def __enter__(self):
        self.start_time = self.timer()
        return self

    def __exit__(self, t, v, tb):  # type, value and traceback irrelevant
        self.stop_time = self.timer()
        if self.name is not None:
            print(repr(self))

    def elapsed(self):
        if self.stop_time is not None:
            return self.stop_time - self.start_time
        else:
            return self.timer() - self.start_time

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        if self.name is None:
            return f"{self.elapsed():.3f} s"
        else:
            return f"{self.name}: {self.elapsed():.3f} s"


@dataclasses.dataclass
class Checkpoint:
    name: str
    timestamp: float


class CheckpointTimer:
    def __init__(self, timer=timeit.default_timer, start_now=True):
        self.timer = timer
        self.checkpoints = []
        if start_now:
            self.start()

    def start(self):
        assert len(self.checkpoints) == 0, "Should only start once"
        self.checkpoint("start")

    def checkpoint(self, name="", include_total=True):
        self.checkpoints.append(Checkpoint(name, self.timer()))

    def checkpoint_and_print(self, name="", include_total=True):
        self.checkpoint(name)
        time_now = self.checkpoints[-1].timestamp
        time_last = time_now - self.checkpoints[-2].timestamp
        if include_total:
            time_total = time_now - self.checkpoints[0].timestamp
            print(f"{name} done in {time_last:.3f} s ({time_total:.3f} s total)")
        else:
            print(f"{name} done in {time_last:.3f} s")

    def get_as_lists(self):
        timestamps = [cp.timestamp for cp in self.checkpoints]
        labels = [cp.name for cp in self.checkpoints]
        return timestamps, labels


def timed(f):
    """Decorator wrapping function calls with the timer context manager"""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        with ContextTimer(name=f.__name__):
            f(*args, **kwargs)

    return wrapper
