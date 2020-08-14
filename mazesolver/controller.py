from enum import Enum
from tkinter import messagebox

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


class ResolutionController:
    DEFAULT_RESOLUTION = 300
    MIN_RESOLUTION = 50
    MAX_RESOLUTION = 1200

    def __init__(self, image: MazeImage):
        self.image = image
        self.resolution = f"{self.DEFAULT_RESOLUTION}"
        self.setup_subscribers()

    def _show_resolution_error(self):
        PUBLISHER.send_message("ResolutionResetRequest")
        messagebox.showerror(
            title="Error",
            message=f"Invalid Resolution: resolution must be an integer between {self.MIN_RESOLUTION} and {self.MAX_RESOLUTION}",
        )
        raise ValueError(f"Invalid Resolution: {self.resolution}")

    def _validate_resolution(self):
        try:
            integer_resolution = int(self.resolution)
        except ValueError:
            self._show_resolution_error()
            return
        if (
            integer_resolution < self.MIN_RESOLUTION
            or integer_resolution > self.MAX_RESOLUTION
        ):
            self._show_resolution_error()

    def _set_resolution(self, resolution: str):
        self.resolution = resolution

    def change_resolution(self):
        self._validate_resolution()
        self.image.scaled_resolution = int(self.resolution)

    def setup_subscribers(self):
        subscribers = [
            Subscriber("ResolutionChangeRequest", function=self._set_resolution),
        ]
        for subscriber in subscribers:
            PUBLISHER.register_subscriber(subscriber)


class FramerateController:
    DEFAULT_FRAMERATE = 15
    MIN_FRAMERATE = 5
    MAX_FRAMERATE = 60

    def __init__(self):
        self.framerate = f"{self.DEFAULT_FRAMERATE}"
        self.setup_subscribers()

    def _show_framerate_error(self):
        PUBLISHER.send_message("FramerateResetRequest")
        messagebox.showerror(
            title="Error",
            message=f"Invalid Framerate: framerate must be an integer between {self.MIN_FRAMERATE} and {self.MAX_FRAMERATE}",
        )
        raise ValueError(f"Invalid Framerate: {self.framerate}")

    def validate_framerate(self):
        try:
            integer_framerate = int(self.framerate)
        except ValueError:
            self._show_framerate_error()
            return
        if (
            integer_framerate < self.MIN_FRAMERATE
            or integer_framerate > self.MAX_FRAMERATE
        ):
            self._show_framerate_error()

    def _set_framerate(self, framerate: str):
        self.framerate = framerate

    def setup_subscribers(self):
        subscribers = [
            Subscriber("FramerateChangeRequest", function=self._set_framerate),
        ]
        for subscriber in subscribers:
            PUBLISHER.register_subscriber(subscriber)


class Controller:
    def __init__(self):
        self.image = MazeImage()
        self._point_controller = PointController(self.image)
        self._resolution_controller = ResolutionController(self.image)
        self._framerate_controller = FramerateController()
        self.application = Application(self.image)
        self.solver = Solver()
        self.setup_subscribers()

    def _validate_image(self):
        if not self.image.loaded:
            messagebox.showerror(
                title="Error",
                message="Invalid Operation: an image must be loaded first",
            )
            raise ValueError("Image not loaded")

    def _maze_solve(self):
        try:
            self._validate_image()
            self._framerate_controller.validate_framerate()
        except ValueError:
            return
        self.image.reset_result()
        PUBLISHER.send_process_message(
            "Maze",
            data={
                "image": self.image,
                "start": self._point_controller.start_point,
                "end": self._point_controller.end_point,
                "framerate": int(self._framerate_controller.framerate),
            },
            start=True,
        )

    def _maze_stop(self):
        PUBLISHER.send_process_message("Maze", stop=True)

    def _maze_resume(self):
        PUBLISHER.send_process_message("Maze", resume=True)

    def _maze_reset(self):
        PUBLISHER.send_process_message(
            "Maze",
            reset=True,
            wait_for_response=True,
            message_timeout=0.2,
            response_timeout=0.2,
        )

    def _image_selection(self, image_path: str):
        try:
            self._resolution_controller.change_resolution()
        except ValueError:
            return
        PUBLISHER.send_message("ImageChangeRequest", image_path=image_path)

    def _image_reset(self):
        self.image.reset_result()
        PUBLISHER.send_message("ImageUpdateRequest")

    def setup_subscribers(self):
        subscribers = [
            ProcessSubscriber("Maze", worker=self.solver),
            Subscriber("ImageSelectionRequest", function=self._image_selection),
            Subscriber("MazeSolveRequest", function=self._maze_solve),
            Subscriber("MazeStopRequest", function=self._maze_stop),
            Subscriber("MazeResumeRequest", function=self._maze_resume),
            Subscriber("MazeCancelRequest", function=self._maze_reset),
            Subscriber("ImageResetRequest", function=self._image_reset),
        ]
        for subscriber in subscribers:
            PUBLISHER.register_subscriber(subscriber)

    def start(self):
        self.application.start()
