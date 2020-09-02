import os.path
from tkinter import messagebox

from mazesolver.config import (
    MAX_FRAMERATE,
    MAX_RESOLUTION,
    MIN_FRAMERATE,
    MIN_RESOLUTION,
)
from mazesolver.image import MazeImage
from mazesolver.pubsub import PUBLISHER
from mazesolver.state import ApplicationState


def isInRange(value: int, minimum: int, maximum: int) -> bool:
    return minimum <= value <= maximum


class FramerateValidator:
    def __init__(self, state: ApplicationState):
        self.state = state

    @property
    def framerate(self) -> str:
        return self.state.framerate

    def show_framerate_error(self) -> None:
        messagebox.showerror(
            title="Error",
            message=(
                f"Invalid Framerate: framerate must be an integer between "
                f"{MIN_FRAMERATE} and {MAX_FRAMERATE}"
            ),
        )

    def validate_framerate(self) -> None:
        try:
            integer_framerate = int(self.framerate)
        except ValueError:
            self.show_framerate_error()
            PUBLISHER.queue_message("FramerateResetRequest")
            raise ValueError(f"Invalid Framerate: {self.framerate}")
        if not isInRange(integer_framerate, MIN_FRAMERATE, MAX_FRAMERATE):
            PUBLISHER.queue_message("FramerateResetRequest")
            self.show_framerate_error()
            raise ValueError(f"Invalid Framerate: {self.framerate}")


class ResolutionValidator:
    def __init__(self, state: ApplicationState) -> None:
        self.state = state

    @property
    def resolution(self) -> str:
        return self.state.resolution

    def show_resolution_error(self) -> None:
        messagebox.showerror(
            title="Error",
            message=(
                f"Invalid Resolution: resolution must be an integer between "
                f"{MIN_RESOLUTION} and {MAX_RESOLUTION}"
            ),
        )

    def validate_resolution(self) -> None:
        try:
            integer_resolution = int(self.resolution)
        except ValueError:
            PUBLISHER.queue_message("ResolutionResetRequest")
            self.show_resolution_error()
            raise ValueError(f"Invalid Resolution: {self.resolution}")
        if not isInRange(integer_resolution, MIN_RESOLUTION, MAX_RESOLUTION):
            PUBLISHER.queue_message("ResolutionResetRequest")
            self.show_resolution_error()
            raise ValueError(f"Invalid Resolution: {self.resolution}")


class ImageValidator:
    SAVE_FORMATS = ["PNG", "JPG", "JPEG"]

    def __init__(self, state: ApplicationState) -> None:
        self.state = state

    @property
    def image(self) -> MazeImage:
        return self.state.image

    def show_image_not_loaded_error(self) -> None:
        messagebox.showerror(
            title="Error", message="Invalid Operation: an image must be loaded first",
        )

    def show_save_format_error(self) -> None:
        messagebox.showerror(
            title="Error",
            message=f"Invalid Save Format: must be one of {self.SAVE_FORMATS}",
        )

    def validate_image(self) -> None:
        if not self.image.loaded:
            self.show_image_not_loaded_error()
            raise ValueError("Image not loaded")

    def validate_save_format(self, image_path: str) -> None:
        save_format = os.path.splitext(image_path)[1]
        save_format = save_format.replace(".", "")
        if save_format.upper() not in self.SAVE_FORMATS:
            self.show_save_format_error()
            raise ValueError(f"Invalid save format: {save_format}")


class Validator:
    def __init__(self, state: ApplicationState):
        self.state = state
        self.framerate_validator = FramerateValidator(self.state)
        self.resolution_validator = ResolutionValidator(self.state)
        self.image_validator = ImageValidator(self.state)

    def validate_framerate(self) -> None:
        self.framerate_validator.validate_framerate()

    def validate_resolution(self) -> None:
        self.resolution_validator.validate_resolution()

    def validate_image(self) -> None:
        self.image_validator.validate_image()

    def validate_save_format(self, image_path: str) -> None:
        self.image_validator.validate_save_format(image_path)
