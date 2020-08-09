import threading
from queue import Empty, Queue
from typing import Any, Callable, List, Optional


class Worker(threading.Thread):
    def __init__(self, queue: "Queue[Any]", function: Optional[Callable[..., Any]]):
        self.queue = queue
        self.receive = threading.Event()
        self.stop = threading.Event()
        self.function = function

    def run(self):
        while True:
            self.receive.wait()
            while True:
                if self.stop.is_set():
                    self._stop()
                try:
                    args, kwargs = self.queue.get(block=True, timeout=1)
                    self.function(*args, **kwargs)
                except Empty:
                    return
            self.receive.clear()

    def clear_queue(self):
        while True:
            try:
                self.queue.get_nowait()
            except Empty:
                pass

    def _stop(self):
        self.clear_queue()
        self.stop.clear()
        self.receive.clear()
        self.receive.wait()


class Subscriber:
    def __init__(
        self,
        topic: str,
        function: Optional[Callable[..., Any]] = None,
        worker: Optional[Worker] = None,
    ):
        self.topic = topic
        self.function = function
        self.worker = worker
        self.queue: "Queue[Any]" = Queue()
        if self.worker is not None:
            self.worker.start()

    def queue_event(self, *args, **kwargs):
        self.queue.put((args, kwargs), block=False)

    def _process_function(self):
        while True:
            try:
                args, kwargs = self.queue.get(block=False)
                self.function(*args, **kwargs)
            except Empty:
                return

    def _process_worker(self):
        self.worker.receive.set()

    def process_events(self):
        if self.function is not None:
            self._process_function()
        elif self.worker is not None:
            self._process_worker()


class Publisher:
    def __init__(self):
        self.subscribers: List[Subscriber] = []

    def register_subscriber(self, subscriber: Subscriber):
        self.subscribers.append(subscriber)

    def emit_event(self, topic, *args, **kwargs):
        for subscriber in self.subscribers:
            if topic == subscriber.topic:
                subscriber.queue_event(*args, **kwargs)
