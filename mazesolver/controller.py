from enum import Enum

from mazesolver.gui import Application
from mazesolver.image import MazeImage
from mazesolver.pubsub import PUBLISHER, ProcessSubscriber, Subscriber
from mazesolver.solver import Solver


class PointStatus(Enum):
    NONE = ""
    START = "start"
    END = "end"

    @classmethod
    def from_value(cls, value: str):
        for member in PointStatus:
            if member.value == value:
                return member
        raise ValueError(f"No such member with value: {value}")


class PointController:
    START_COLOR = (255, 0, 0)
    END_COLOR = (255, 0, 255)

    def __init__(self, image: MazeImage):
        self.start_point = (0, 0)
        self.end_point = (0, 0)
        self.status = PointStatus.NONE
        self.image = image
        self.setup_subscribers()

    def reset_points(self):
        self.start_point = (0, 0)
        self.end_point = (0, 0)

    def set_status(self, kind: str):
        self.status = PointStatus.from_value(kind)

    def set_point(self, x: int, y: int):
        if self.status == PointStatus.START:
            self.start_point = (x, y)
        elif self.status == PointStatus.END:
            self.end_point = (x, y)
        if self.status != PointStatus.NONE:
            self.image.reset_result()
            self.image.mark_point(self.start_point, color=self.START_COLOR, size=3)
            self.image.mark_point(self.end_point, color=self.END_COLOR, size=3)
            PUBLISHER.send_message("ImageUpdateRequest")
        self.status = PointStatus.NONE

    def setup_subscribers(self):
        subscribers = [
            Subscriber("PointChangeRequest", function=self.set_status),
            Subscriber("ImageClicked", function=self.set_point),
            Subscriber(
                "ImageChangeRequest",
                function=lambda *args, **kwargs: self.reset_points(),
            ),
        ]
        for subscriber in subscribers:
            PUBLISHER.register_subscriber(subscriber)


class Controller:
    def __init__(self):
        self.image = MazeImage()
        self.framerate = 15
        self._point_controller = PointController(self.image)
        self.application = Application(self.image)
        self.solver = Solver()
        self.setup_subscribers()

    def _change_resolution(self, resolution: str):
        try:
            integer_resolution = int(resolution)
            if integer_resolution < 50:
                return
        except ValueError:
            return
        self.image.scaled_resolution = integer_resolution

    def _change_framerate(self, framerate: str):
        try:
            integer_framerate = int(framerate)
            if integer_framerate < 5 or integer_framerate > 60:
                return
        except ValueError:
            return
        self.framerate = integer_framerate

    def _maze_solve(self):
        if self.image.result is None:
            return
        self.image.reset_result()
        PUBLISHER.send_process_message(
            "Maze",
            data={
                "image": self.image,
                "start": self._point_controller.start_point,
                "end": self._point_controller.end_point,
                "framerate": self.framerate,
            },
            start=True,
        )

    def _maze_stop(self):
        PUBLISHER.send_process_message("Maze", stop=True)

    def _maze_resume(self):
        PUBLISHER.send_process_message("Maze", resume=True)

    def _maze_reset(self):
        PUBLISHER.send_process_message("Maze", reset=True)

    def setup_subscribers(self):
        subscribers = [
            ProcessSubscriber("Maze", worker=self.solver),
            Subscriber("ResolutionChangeRequest", function=self._change_resolution),
            Subscriber("FramerateChangeRequest", function=self._change_framerate),
            Subscriber(
                "ImageChangeRequest",
                function=lambda *args, **kwargs: self._maze_reset(),
            ),
            Subscriber("MazeSolveRequest", function=self._maze_solve),
            Subscriber("MazeStopRequest", function=self._maze_stop),
            Subscriber("MazeResumeRequest", function=self._maze_resume),
        ]
        for subscriber in subscribers:
            PUBLISHER.register_subscriber(subscriber)

    def start(self):
        self.application.start()
