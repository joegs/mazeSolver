import time


class Timer:
    def __init__(self) -> None:
        self._start_time: float = 0
        self._end_time: float = 0
        self.elapsed_time: float = 0

    def start(self) -> None:
        self._start_time = time.time()

    def measure(self) -> None:
        self._end_time = time.time()
        self.elapsed_time = self._end_time - self._start_time
