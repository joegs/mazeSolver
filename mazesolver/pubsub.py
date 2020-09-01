import multiprocessing as mp
import threading
from queue import Empty, Full, Queue
from typing import Any, Callable, Dict, List, Tuple, Union


class Subscriber:
    def __init__(self, topic: str, function: Callable[..., Any]):
        self.topic = topic
        self.function = function

    def receive_message(self, **kwargs: Any) -> None:
        self.function(**kwargs)


class ThreadWorker(threading.Thread):
    def __init__(
        self, *args: Any, input_size: int = 0, output_size: int = 0, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.input_queue: "Queue[Any]" = mp.Queue(input_size)
        self.output_queue: "Queue[Any]" = mp.Queue(output_size)
        self.received = mp.Event()
        self.response = mp.Event()

    def clear_queue(self) -> None:
        while True:
            try:
                self.input_queue.get_nowait()
            except Empty:
                break
        self.received.clear()


class ThreadSubscriber:
    def __init__(self, name: str, worker: ThreadWorker):
        self.name = name
        self.worker = worker
        self.worker.start()

    def queue_message_no_wait(self, kwargs: Dict[str, Any]) -> None:
        try:
            self.worker.input_queue.put_nowait(kwargs)
        except Full:
            return
        self.worker.received.set()

    def queue_message_wait(
        self, message_timeout: float, response_timeout: float, kwargs: Dict[str, Any]
    ) -> bool:
        self.worker.received.set()
        try:
            self.worker.input_queue.put(kwargs, block=True, timeout=message_timeout)
        except Full:
            return False
        response = self.worker.response.wait(timeout=response_timeout)
        self.worker.response.clear()
        return response


class ProcessWorker(mp.Process):
    def __init__(
        self, *args: Any, input_size: int = 0, output_size: int = 0, **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        self.input_queue: "Queue[Any]" = mp.Queue(input_size)
        self.output_queue: "Queue[Any]" = mp.Queue(output_size)
        self.received = mp.Event()
        self.response = mp.Event()

    def clear_queue(self) -> None:
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

    def queue_message_no_wait(self, kwargs: Dict[str, Any]) -> None:
        try:
            self.worker.input_queue.put_nowait(kwargs)
        except Full:
            return
        self.worker.received.set()

    def queue_message_wait(
        self, message_timeout: float, response_timeout: float, kwargs: Dict[str, Any]
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
    def __init__(self) -> None:
        self._message_queue: List[Tuple[str, Dict[str, Any]]] = []
        self.subscribers: List[Subscriber] = []
        self.thread_subscribers: Dict[str, ThreadSubscriber] = {}
        self.process_subscribers: Dict[str, ProcessSubscriber] = {}

    def register_subscriber(
        self, subscriber: Union[Subscriber, ThreadSubscriber, ProcessSubscriber]
    ) -> None:
        if isinstance(subscriber, Subscriber):
            self.subscribers.append(subscriber)
        elif isinstance(subscriber, ThreadSubscriber):
            self.thread_subscribers[subscriber.name] = subscriber
        elif isinstance(subscriber, ProcessSubscriber):
            self.process_subscribers[subscriber.name] = subscriber

    def queue_message(self, topic: str, **kwargs: Any) -> None:
        self._message_queue.append((topic, kwargs))

    def queue_thread_message(
        self,
        name: str,
        wait_for_response: bool = False,
        message_timeout: float = 1,
        response_timeout: float = 1,
        **kwargs: Any,
    ) -> bool:
        subscriber = self.thread_subscribers.get(name, None)
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

    def queue_process_message(
        self,
        name: str,
        wait_for_response: bool = False,
        message_timeout: float = 1,
        response_timeout: float = 1,
        **kwargs: Any,
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

    def fetch_thread_messages(self) -> None:
        for name, thread_subscriber in self.thread_subscribers.items():
            while True:
                try:
                    kwargs = thread_subscriber.worker.output_queue.get_nowait()
                except Empty:
                    break
                self.queue_message(**kwargs)

    def fetch_process_messages(self) -> None:
        for name, process_subscriber in self.process_subscribers.items():
            while True:
                try:
                    kwargs = process_subscriber.worker.output_queue.get_nowait()
                except Empty:
                    break
                self.queue_message(**kwargs)

    def send_messages(self) -> None:
        self.fetch_thread_messages()
        self.fetch_process_messages()
        while self._message_queue:
            topic, kwargs = self._message_queue.pop(0)
            for subscriber in self.subscribers:
                if topic == subscriber.topic:
                    subscriber.receive_message(**kwargs)


PUBLISHER = Publisher()
