import os.path
from tkinter import messagebox

from mazesolver.pubsub import PUBLISHER
from mazesolver.config import (
    DEFAULT_FRAMERATE,
    DEFAULT_RESOLUTION,
    MIN_FRAMERATE,
    MAX_FRAMERATE,
    MIN_RESOLUTION,
    MAX_RESOLUTION,
)
from mazesolver.state import ApplicationState


class FramerateValidator:
    def __init__(self, state: ApplicationState):
        self.state = state

    @property
    def framerate(self):
        return self.state.framerate

    def show_framerate_error(self):
        messagebox.showerror(
            title="Error",
            message=f"Invalid Framerate: framerate must be an integer between {MIN_FRAMERATE} and {MAX_FRAMERATE}",
        )

    def validate_framerate(self):
        try:
            integer_framerate = int(self.framerate)
        except ValueError:
            self.show_framerate_error()
            PUBLISHER.queue_message("FramerateResetRequest")
            raise ValueError(f"Invalid Framerate: {self.framerate}")
        if integer_framerate < MIN_FRAMERATE or integer_framerate > MAX_FRAMERATE:
            PUBLISHER.queue_message("FramerateResetRequest")
            self.show_framerate_error()
            raise ValueError(f"Invalid Framerate: {self.framerate}")


class ResolutionValidator:
    def __init__(self, state):
        self.state = state

    @property
    def resolution(self):
        return self.state.resolution

    def show_resolution_error(self):
        messagebox.showerror(
            title="Error",
            message=f"Invalid Resolution: resolution must be an integer between {MIN_RESOLUTION} and {MAX_RESOLUTION}",
        )

    def validate_resolution(self):
        try:
            integer_resolution = int(self.resolution)
        except ValueError:
            PUBLISHER.queue_message("ResolutionResetRequest")
            self.show_resolution_error()
            raise ValueError(f"Invalid Resolution: {self.resolution}")
        if integer_resolution < MIN_RESOLUTION or integer_resolution > MAX_RESOLUTION:
            PUBLISHER.queue_message("ResolutionResetRequest")
            self.show_resolution_error()
            raise ValueError(f"Invalid Resolution: {self.resolution}")


class ImageValidator:
    SAVE_FORMATS = ["PNG", "JPG", "JPEG"]

    def __init__(self, state: ApplicationState):
        self.state = state

    @property
    def image(self):
        return self.state.image

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


class Validator:
    def __init__(self, state: ApplicationState):
        self.state = state
        self.framerate_validator = FramerateValidator(self.state)
        self.resolution_validator = ResolutionValidator(self.state)
        self.image_validator = ImageValidator(self.state)

    def validate_framerate(self):
        self.framerate_validator.validate_framerate()

    def validate_resolution(self):
        self.resolution_validator.validate_resolution()

    def validate_image(self):
        self.image_validator.validate_image()

    def validate_save_format(self, image_path: str):
        self.image_validator.validate_save_format(image_path)
