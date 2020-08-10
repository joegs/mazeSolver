import threading
from queue import Empty, Queue
from typing import Any, Callable, Dict, List


class Subscriber:
    def __init__(self, topic: str, function: Callable[..., Any]):
        self.function = function
        self.topic = topic
        self.queue: List[Any] = []

    def queue_message(self, **kwargs):
        self.queue.append(kwargs)

    def process_messages(self):
        while self.queue:
            kwargs = self.queue.pop(0)
            self.function(**kwargs)


class Publisher:
    def __init__(self):
        self.subscribers: List[Subscriber] = []

    def register_subscriber(self, subscriber: Subscriber):
        self.subscribers.append(subscriber)

    def send_message(self, topic: str, **kwargs):
        for subscriber in self.subscribers:
            if topic == subscriber.topic:
                subscriber.queue_message(**kwargs)

    def process_messages(self):
        for subscriber in self.subscribers:
            subscriber.process_messages()


class Worker(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_queue: Queue = Queue()
        self.output_queue: Queue = Queue()
        self.received = threading.Event()

    def clear_queue(self):
        while True:
            try:
                self.input_queue.get_nowait()
            except Empty:
                return


class ThreadSubscriber:
    def __init__(self, name: str, worker: Worker):
        self.name = name
        self.worker = worker
        self.worker.start()

    def queue_message(self, wait_for_response: bool, timeout: float, **kwargs):
        self.worker.input_queue.put_nowait(kwargs)
        self.worker.received.set()
        if wait_for_response:
            self.worker.output_queue.get(block=True, timeout=timeout)


class ThreadPublisher:
    def __init__(self):
        self.subscribers: Dict[str, ThreadSubscriber] = {}

    def register_subscriber(self, subscriber: ThreadSubscriber):
        self.subscribers[subscriber.name] = subscriber

    def send_message(
        self, name: str, wait_for_response: bool = False, timeout: float = 2, **kwargs
    ):
        subscriber = self.subscribers.get(name, None)
        if subscriber is None:
            return
        subscriber.queue_message(wait_for_response, timeout, **kwargs)


PUBLISHER = Publisher()
THREAD_PUBLISHER = ThreadPublisher()
