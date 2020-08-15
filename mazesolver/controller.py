import os.path
from enum import Enum
from tkinter import messagebox
from typing import Tuple

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


class ResolutionController:
    DEFAULT_RESOLUTION = 300
    MIN_RESOLUTION = 50
    MAX_RESOLUTION = 1200

    def __init__(self, image: MazeImage):
        self.image = image
        self.resolution = f"{self.DEFAULT_RESOLUTION}"
        self.setup_subscribers()

    def show_resolution_error(self):
        messagebox.showerror(
            title="Error",
            message=f"Invalid Resolution: resolution must be an integer between {self.MIN_RESOLUTION} and {self.MAX_RESOLUTION}",
        )

    def validate_resolution(self):
        try:
            integer_resolution = int(self.resolution)
        except ValueError:
            PUBLISHER.send_message("ResolutionResetRequest")
            self.show_resolution_error()
            raise ValueError(f"Invalid Resolution: {self.resolution}")
        if (
            integer_resolution < self.MIN_RESOLUTION
            or integer_resolution > self.MAX_RESOLUTION
        ):
            PUBLISHER.send_message("ResolutionResetRequest")
            self.show_resolution_error()
            raise ValueError(f"Invalid Resolution: {self.resolution}")

    def _set_resolution(self, resolution: str):
        self.resolution = resolution

    def change_resolution(self):
        self.validate_resolution()
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

    def show_framerate_error(self):
        messagebox.showerror(
            title="Error",
            message=f"Invalid Framerate: framerate must be an integer between {self.MIN_FRAMERATE} and {self.MAX_FRAMERATE}",
        )

    def validate_framerate(self):
        try:
            integer_framerate = int(self.framerate)
        except ValueError:
            self.show_framerate_error()
            PUBLISHER.send_message("FramerateResetRequest")
            raise ValueError(f"Invalid Framerate: {self.framerate}")
        if (
            integer_framerate < self.MIN_FRAMERATE
            or integer_framerate > self.MAX_FRAMERATE
        ):
            PUBLISHER.send_message("FramerateResetRequest")
            self.show_framerate_error()
            raise ValueError(f"Invalid Framerate: {self.framerate}")

    def _set_framerate(self, framerate: str):
        self.framerate = framerate

    def setup_subscribers(self):
        subscribers = [
            Subscriber("FramerateChangeRequest", function=self._set_framerate),
        ]
        for subscriber in subscribers:
            PUBLISHER.register_subscriber(subscriber)


class ImageController:
    SAVE_FORMATS = ["PNG", "JPG", "JPEG"]

    def __init__(self, image: MazeImage, resolution_controller: ResolutionController):
        self.image = image
        self.resolution_controller = resolution_controller
        self.setup_subscribers()

    def show_image_not_loaded_error(self):
        messagebox.showerror(
            title="Error", message="Invalid Operation: an image must be loaded first",
        )

    def show_save_format_error(self):
        messagebox.showerror(
            title="Error",
            message=f"Invalid Save Format: must be one of {self.SAVE_FORMATS}",
        )

    def validate_image(self):
        if not self.image.loaded:
            self.show_image_not_loaded_error()
            raise ValueError("Image not loaded")

    def validate_save_format(self, image_path: str):
        save_format = os.path.splitext(image_path)[1]
        save_format = save_format.replace(".", "")
        if save_format.upper() not in self.SAVE_FORMATS:
            self.show_save_format_error()
            raise ValueError(f"Invalid save format: {save_format}")

    def image_selection(self, image_path: str):
        try:
            self.resolution_controller.change_resolution()
        except ValueError:
            return
        self.image.overlay.clear()
        PUBLISHER.send_message("ImageChangeRequest", image_path=image_path)

    def image_reset(self):
        self.image.reset_result()
        PUBLISHER.send_message("ImageUpdateRequest")

    def image_save(self, image_path: str):
        try:
            self.validate_image()
            self.validate_save_format(image_path)
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
        self,
        image: MazeImage,
        image_controller: ImageController,
        framerate_controller: FramerateController,
        point_controller: PointController,
    ):
        self.image = image
        self.image_controller = image_controller
        self.framerate_controller = framerate_controller
        self.point_controller = point_controller
        self.setup_subscribers()

    def maze_solve(self):
        try:
            self.image_controller.validate_image()
            self.framerate_controller.validate_framerate()
        except ValueError:
            return
        self.image.reset_result()
        PUBLISHER.send_process_message(
            "Maze",
            data={
                "image": self.image,
                "start": self.point_controller.start_point,
                "end": self.point_controller.end_point,
                "framerate": int(self.framerate_controller.framerate),
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
        self._point_controller = PointController(self.image)
        self._resolution_controller = ResolutionController(self.image)
        self._framerate_controller = FramerateController()
        self._image_controller = ImageController(
            self.image, self._resolution_controller
        )
        self._maze_controller = MazeController(
            self.image,
            self._image_controller,
            self._framerate_controller,
            self._point_controller,
        )
        self.application = Application(self.image)
        self.solver = Solver()
        self.setup_subscribers()

    def setup_subscribers(self):
        subscribers = [ProcessSubscriber("Maze", worker=self.solver)]
        for subscriber in subscribers:
            PUBLISHER.register_subscriber(subscriber)

    def start(self):
        self.application.start()
