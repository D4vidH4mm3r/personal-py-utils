import concurrent.futures
import dataclasses
import heapq
import threading
import typing
import queue


@dataclasses.dataclass(order=True)
class PqEntry:
    priority: int
    data: typing.Any = dataclasses.field(compare=False)


@dataclasses.dataclass
class WorkEntry:
    future: concurrent.futures._base.Future
    fun: typing.Callable
    args: typing.Tuple
    kwargs: typing.Dict


class PriorityThreadpoolExecutor:
    def __init__(self, num_threads=None):
        if num_threads is None:
            import os

            num_threads = os.cpu_count()
        self._q = queue.PriorityQueue()
        self._threads = [
            threading.Thread(target=self._runner, daemon=True)
            for _ in range(num_threads)
        ]
        for t in self._threads:
            t.start()

    def _runner(self):
        while True:
            task = self._q.get()
            if task.data is None:
                return
            work = task.data
            if not work.future.set_running_or_notify_cancel():
                continue
            try:
                res = work.fun(*work.args, **work.kwargs)
            except BaseException as e:
                work.future.set_exception(e)
            else:
                work.future.set_result(res)

    def submit(self, priority, fun, args=None, kwargs=None):
        if args is None:
            args = tuple()
        if kwargs is None:
            kwargs = dict()
        future = concurrent.futures._base.Future()
        self._q.put(PqEntry(priority, WorkEntry(future, fun, args, kwargs)))
        return future

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        self.shutdown()

    def shutdown(self):
        import sys

        for _ in self._threads:
            self._q.put(PqEntry(sys.maxsize, None))

        for t in self._threads:
            t.join()
