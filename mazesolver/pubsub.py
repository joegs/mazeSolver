import threading
import multiprocessing as mp
from queue import Empty, Queue, Full
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


class ProcessWorker(mp.Process):
    def __init__(self, input_size=0, output_size=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_queue = mp.Queue(input_size)
        self.output_queue = mp.Queue(output_size)
        self.received = mp.Event()
        self.response = mp.Event()

    def clear_queue(self):
        while True:
            try:
                self.input_queue.get_nowait()
            except Empty:
                break
        self.received.clear()


class ProcessSubscriber:
    def __init__(self, name: str, worker: ProcessWorker):
        self.name = name
        self.worker = worker
        self.worker.start()

    def queue_message_no_wait(self, kwargs):
        try:
            self.worker.input_queue.put_nowait(kwargs)
        except Full:
            return
        self.worker.received.set()

    def queue_message_wait(
        self, message_timeout: float, response_timeout: float, kwargs
    ) -> bool:
        self.worker.received.set()
        try:
            self.worker.input_queue.put(kwargs, block=True, timeout=message_timeout)
        except Full:
            return False
        response = self.worker.response.wait(timeout=response_timeout)
        self.worker.response.clear()
        return response


class Publisher:
    def __init__(self):
        self.subscribers: List[Subscriber] = []
        self.thread_subscribers: Dict[str, ThreadSubscriber] = {}
        self.process_subscribers: Dict[str, ProcessSubscriber] = {}

    def register_subscriber(
        self, subscriber: Union[Subscriber, ThreadSubscriber, ProcessSubscriber]
    ):
        if isinstance(subscriber, Subscriber):
            self.subscribers.append(subscriber)
        elif isinstance(subscriber, ThreadSubscriber):
            self.thread_subscribers[subscriber.name] = subscriber
        elif isinstance(subscriber, ProcessSubscriber):
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
        self,
        name: str,
        wait_for_response: bool = False,
        message_timeout: float = 1,
        response_timeout: float = 1,
        **kwargs,
    ) -> bool:
        subscriber = self.process_subscribers.get(name, None)
        if subscriber is None:
            return False
        if wait_for_response:
            response = subscriber.queue_message_wait(
                message_timeout, response_timeout, kwargs
            )
            return response
        else:
            subscriber.queue_message_no_wait(kwargs)
            return False

    def process_messages(self):
        for name, subscriber in self.process_subscribers.items():
            while True:
                try:
                    kwargs = subscriber.worker.output_queue.get_nowait()
                except Empty:
                    break
                self.send_message(**kwargs)
        for subscriber in self.subscribers:
            subscriber.process_messages()


PUBLISHER = Publisher()
