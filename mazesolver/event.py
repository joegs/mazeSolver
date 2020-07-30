class EventListener:
    def __init__(self, topic: str, function=None):
        self.function = function
        self.topic = topic

    def receive_event(self, *args, **kwargs):
        self.function(*args, **kwargs)


class EventProcessor:
    def __init__(self):
        self.listeners: List[EventListener] = []

    def register_listener(self, listener: EventListener):
        self.listeners.append(listener)

    def emit_event(self, topic: str, *args, **kwargs):
        for listener in self.listeners:
            if topic == listener.topic:
                listener.receive_event(*args, **kwargs)


EVENT_PROCESSOR = EventProcessor()
