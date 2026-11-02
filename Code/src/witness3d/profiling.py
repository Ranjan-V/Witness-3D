"""Future-run resource instrumentation, never invoked during authoring."""
from __future__ import annotations

import os
import threading
from time import perf_counter, process_time


class Profile:
    def __enter__(self):
        self.wall, self.cpu = perf_counter(), process_time()
        self.peak_rss = None
        self.stop = threading.Event()
        try:
            import psutil
            process = psutil.Process(os.getpid())
            self.peak_rss = process.memory_info().rss

            def sample():
                while not self.stop.wait(0.02):
                    self.peak_rss = max(self.peak_rss, process.memory_info().rss)
            self.thread = threading.Thread(target=sample, daemon=True)
            self.thread.start()
        except ImportError:
            self.thread = None
        return self

    def __exit__(self, *args):
        self.stop.set()
        if self.thread is not None:
            self.thread.join()
        self.wall_seconds = perf_counter() - self.wall
        self.cpu_seconds = process_time() - self.cpu

    def as_dict(self):
        return {"wall_seconds": self.wall_seconds, "cpu_seconds": self.cpu_seconds,
                "peak_rss_bytes_sampled": self.peak_rss,
                "rss_sampling_period_seconds": 0.02 if self.peak_rss is not None else None}

