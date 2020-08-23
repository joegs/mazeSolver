import time


class Timer:
    def __init__(self):
        self._start_time = 0
        self._end_time = 0
        self.elapsed_time = 0

    def start(self):
        self._start_time = time.time()

    def measure(self):
        self._end_time = time.time()
        self.elapsed_time = self._end_time - self._start_time
