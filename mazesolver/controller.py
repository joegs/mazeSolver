from mazesolver.event import EVENT_PROCESSOR, EventListener
from mazesolver.gui import Application
from mazesolver.image import MazeImage
from mazesolver.pubsub import (
    PUBLISHER,
    THREAD_PUBLISHER,
    Subscriber,
    ThreadSubscriber,
    Worker,
)
from mazesolver.solver import Solver


class Controller:
    def __init__(self):
        self.start_point = (0, 0)
        self.end_point = (0, 0)
        self.point_change = ""
        self.image = MazeImage()
        self.application = Application(self.image)
        self.solver = Solver()
        self.setup_listeners()

    def _point_change(self, kind: str):
        self.point_change = kind

    def _image_clicked(self, x: int, y: int):
        if self.point_change == "start":
            self.start_point = (x, y)
        if self.point_change == "end":
            self.end_point = (x, y)
        if self.point_change:
            self.image.reset_result()
            self.image.mark_point(self.start_point, color=(255, 0, 0), size=3)
            self.image.mark_point(self.end_point, color=(255, 0, 255), size=3)
            PUBLISHER.send_message("UpdateImage")
        self.point_change = ""

    def _solve_maze(self):
        if self.image.result is None:
            return
        self.image.reset_result()
        THREAD_PUBLISHER.send_message(
            "Maze", data=(self.image, self.start_point, self.end_point), start=True
        )

    def _reset_points(self, image_path):
        self.start_point = (0, 0)
        self.end_point = (0, 0)

    def _change_resolution(self, resolution: str):
        try:
            integer_resolution = int(resolution)
            if integer_resolution < 50:
                return
        except ValueError:
            return
        self.image.scaled_resolution = integer_resolution

    def _stop_solve(self):
        PUBLISHER.send_message("Maze", stop=True)
        # self.solver.output_queue.get(block=True, timeout=2)

    def setup_listeners(self):
        listeners = [
            EventListener("ResolutionChanged", self._change_resolution),
        ]
        for listener in listeners:
            EVENT_PROCESSOR.register_listener(listener)

        subscribers = [
            Subscriber("SolveMaze", function=self._solve_maze),
            Subscriber("PointChange", function=self._point_change),
            Subscriber("ImageClicked", function=self._image_clicked),
            Subscriber("ImageChanged", function=self._reset_points),
            Subscriber("ResolutionChanged", function=self._change_resolution),
            Subscriber("StopSolve", function=self._stop_solve),
        ]
        for subscriber in subscribers:
            PUBLISHER.register_subscriber(subscriber)
        thread_subscriber = ThreadSubscriber("Maze", worker=self.solver)
        THREAD_PUBLISHER.register_subscriber(thread_subscriber)

    def start(self):
        self.application.start()
