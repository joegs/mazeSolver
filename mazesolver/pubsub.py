import threading
import multiprocessing as mp
from multiprocessing.connection import Connection
from queue import Empty, Queue
from typing import Any, Callable, Dict, List, Union


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


class ThreadWorker(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_queue: Queue = Queue()
        self.received = threading.Event()
        self.response = threading.Event()

    def clear_queue(self):
        while True:
            try:
                self.input_queue.get_nowait()
            except Empty:
                return


class ThreadSubscriber:
    def __init__(self, name: str, worker: ThreadWorker):
        self.name = name
        self.worker = worker
        self.worker.start()

    def queue_message(self, wait_for_response: bool, timeout: float, **kwargs):
        self.worker.input_queue.put_nowait(kwargs)
        self.worker.received.set()
        if wait_for_response:
            self.worker.response.wait(timeout=timeout)
            self.worker.response.clear()


class MultiprocessWorker(mp.Process):
    def __init__(self, child_pipe: Connection, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.child_pipe = child_pipe
        self.received = mp.Event()
        self.response = mp.Event()

    def clear_queue(self):
        while self.child_pipe.poll():
            self.child_pipe.recv()


class MultiprocessSubscriber:
    def __init__(self, name: str, worker: MultiprocessWorker, parent_pipe: Connection):
        self.name = name
        self.parent_pipe = parent_pipe
        self.worker = worker
        self.worker.start()

    def queue_message(self, wait_for_response: bool, timeout: float, **kwargs):
        self.parent_pipe.send(kwargs)
        self.worker.received.set()
        if wait_for_response:
            self.worker.response.wait(timeout=timeout)
            self.worker.response.clear()


class Publisher:
    def __init__(self):
        self.subscribers: List[Subscriber] = []
        self.thread_subscribers: Dict[str, ThreadSubscriber] = {}
        self.process_subscribers: Dict[str, MultiprocessSubscriber] = {}

    def register_subscriber(
        self, subscriber: Union[Subscriber, ThreadSubscriber, MultiprocessSubscriber]
    ):
        if isinstance(subscriber, Subscriber):
            self.subscribers.append(subscriber)
        elif isinstance(subscriber, ThreadSubscriber):
            self.thread_subscribers[subscriber.name] = subscriber
        elif isinstance(subscriber, MultiprocessSubscriber):
            self.process_subscribers[subscriber.name] = subscriber

    def send_message(self, topic: str, **kwargs):
        for subscriber in self.subscribers:
            if topic == subscriber.topic:
                subscriber.queue_message(**kwargs)

    def send_thread_message(
        self, name: str, wait_for_response: bool = False, timeout: float = 2, **kwargs
    ):
        subscriber = self.thread_subscribers.get(name, None)
        if subscriber is None:
            return
        subscriber.queue_message(wait_for_response, timeout, **kwargs)

    def send_process_message(
        self, name: str, wait_for_response: bool = False, timeout: float = 2, **kwargs
    ):
        subscriber = self.process_subscribers.get(name, None)
        if subscriber is None:
            return
        subscriber.queue_message(wait_for_response, timeout, **kwargs)

    def process_messages(self):
        for name, subscriber in self.process_subscribers:
            while subscriber.parent_pipe.poll():
                kwargs = subscriber.parent_pipe.recv()
                self.send_message(**kwargs)
        for subscriber in self.subscribers:
            subscriber.process_messages()


PUBLISHER = Publisher()
