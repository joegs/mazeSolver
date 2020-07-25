from mazesolver.event import EventListener, EVENT_PROCESSOR


class Controller:
    def __init__(self):
        self.start_point = (0, 0)
        self.end_point = (0, 0)
        self.point_change = ""
        self.setup_listeners()

    def _point_change(self, kind: str):
        self.point_change = kind

    def _image_clicked(self, x: int, y: int):
        if self.point_change == "start":
            self.start_point = (x, y)
        if self.point_change == "end":
            self.end_point = (x, y)
        self.point_change = ""

    def setup_listeners(self):
        position_listener = EventListener("PointChange")
        image_listener = EventListener("ImageClicked")
        EVENT_PROCESSOR.register_listener(position_listener)
        EVENT_PROCESSOR.register_listener(image_listener)
        position_listener.receive_event = self._point_change
        image_listener.receive_event = self._image_clicked
