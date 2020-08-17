from enum import Enum
from typing import Tuple

from mazesolver.gui import Application
from mazesolver.image import MazeImage
from mazesolver.pubsub import PUBLISHER, ProcessSubscriber, Subscriber
from mazesolver.solver import Solver
from mazesolver.state import ApplicationState
from mazesolver.validation import Validator


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


class StateController:
    def __init__(self, state: ApplicationState):
        self.state = state
        self.setup_subscribers()

    def _set_resolution(self, resolution: str):
        self.state.resolution = resolution

    def _set_framerate(self, framerate: str):
        self.state.framerate = framerate

    def setup_subscribers(self):
        subscribers = [
            Subscriber("FramerateChangeRequest", function=self._set_framerate),
            Subscriber("ResolutionChangeRequest", function=self._set_resolution),
        ]
        for subscriber in subscribers:
            PUBLISHER.register_subscriber(subscriber)


class PointController:
    START_COLOR = (255, 0, 0)
    END_COLOR = (255, 0, 255)

    def __init__(self, state: ApplicationState):
        self.state = state
        self.image = self.state.image
        self.status = PointStatus.NONE
        self.setup_subscribers()

    @property
    def start_point(self):
        return self.state.start_point

    @start_point.setter
    def start_point(self, value):
        self.state.start_point = value

    @property
    def end_point(self):
        return self.state.end_point

    @end_point.setter
    def end_point(self, value):
        self.state.end_point = value

    def reset_points(self):
        self.start_point = (0, 0)
        self.end_point = (0, 0)

    def set_status(self, kind: str):
        self.status = PointStatus.from_value(kind)

    def get_area(self, point: Tuple[int, int]) -> Tuple[int, int, int, int]:
        size = round(self.image.scaled_resolution / 100)
        x1, y1 = point
        x2 = x1 + size
        y2 = y1 + size
        return (x1, y1, x2, y2)

    def set_start_point(self):
        start_area = self.get_area(self.start_point)
        self.image.overlay.append((start_area, self.START_COLOR))

    def set_end_point(self):
        end_area = self.get_area(self.end_point)
        self.image.overlay.append((end_area, self.END_COLOR))

    def set_point(self, x: int, y: int):
        if self.status == PointStatus.START:
            self.start_point = (x, y)
        elif self.status == PointStatus.END:
            self.end_point = (x, y)
        if self.status != PointStatus.NONE:
            self.image.reset_result()
            self.image.overlay.clear()
            self.set_start_point()
            self.set_end_point()
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


class ImageController:
    SAVE_FORMATS = ["PNG", "JPG", "JPEG"]

    def __init__(self, state: ApplicationState, validator: Validator):
        self.state = state
        self.validator = validator
        self.image = self.state.image
        self.setup_subscribers()

    def image_selection(self, image_path: str):
        try:
            self.validator.validate_resolution()
            self.image.scaled_resolution = int(self.state.resolution)
        except ValueError:
            return
        self.image.overlay.clear()
        PUBLISHER.send_message("ImageChangeRequest", image_path=image_path)

    def image_reset(self):
        self.image.reset_result()
        PUBLISHER.send_message("ImageUpdateRequest")

    def image_save(self, image_path: str):
        try:
            self.validator.validate_image()
            self.validator.validate_save_format(image_path)
        except ValueError:
            return
        self.image.save_result(image_path)

    def setup_subscribers(self):
        subscribers = [
            Subscriber("ImageSelectionRequest", function=self.image_selection),
            Subscriber("ImageResetRequest", function=self.image_reset),
            Subscriber("ImageSaveRequest", function=self.image_save),
        ]
        for subscriber in subscribers:
            PUBLISHER.register_subscriber(subscriber)


class MazeController:
    def __init__(
        self, state: ApplicationState, validator: Validator,
    ):
        self.state = state
        self.validator = validator
        self.image = self.state.image
        self.setup_subscribers()

    def maze_solve(self):
        try:
            self.validator.validate_image()
            self.validator.validate_framerate()
        except ValueError:
            return
        self.image.reset_result()
        PUBLISHER.send_process_message(
            "Maze",
            data={
                "image": self.image,
                "start": self.state.start_point,
                "end": self.state.end_point,
                "framerate": int(self.state.framerate),
            },
            start=True,
        )

    def maze_stop(self):
        PUBLISHER.send_process_message("Maze", stop=True)

    def maze_resume(self):
        PUBLISHER.send_process_message("Maze", resume=True)

    def maze_reset(self):
        PUBLISHER.send_process_message(
            "Maze",
            reset=True,
            wait_for_response=True,
            message_timeout=0.2,
            response_timeout=0.2,
        )

    def setup_subscribers(self):
        subscribers = [
            Subscriber("MazeSolveRequest", function=self.maze_solve),
            Subscriber("MazeStopRequest", function=self.maze_stop),
            Subscriber("MazeResumeRequest", function=self.maze_resume),
            Subscriber("MazeCancelRequest", function=self.maze_reset),
        ]
        for subscriber in subscribers:
            PUBLISHER.register_subscriber(subscriber)


class ApplicationController:
    def __init__(self):
        self.image = MazeImage()
        self.state = ApplicationState(self.image)
        self.validator = Validator(self.state)
        self.create_controllers()
        self.application = Application(self.image)
        self.solver = Solver()
        self.setup_subscribers()

    def create_controllers(self):
        state_controller = StateController(self.state)
        point_controller = PointController(self.state)
        image_controller = ImageController(self.state, self.validator)
        maze_controller = MazeController(self.state, self.validator)

    def setup_subscribers(self):
        subscribers = [ProcessSubscriber("Maze", worker=self.solver)]
        for subscriber in subscribers:
            PUBLISHER.register_subscriber(subscriber)

    def start(self):
        self.application.start()
