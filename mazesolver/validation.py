import os.path
from tkinter import messagebox

from mazesolver.pubsub import PUBLISHER
from mazesolver.state import ApplicationState


class FramerateValidator:
    DEFAULT_FRAMERATE = 15
    MIN_FRAMERATE = 5
    MAX_FRAMERATE = 60

    def __init__(self, state: ApplicationState):
        self.state = state

    @property
    def framerate(self):
        return self.state.framerate

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


class ResolutionValidator:
    DEFAULT_RESOLUTION = 300
    MIN_RESOLUTION = 50
    MAX_RESOLUTION = 1200

    def __init__(self, state):
        self.state = state

    @property
    def resolution(self):
        return self.state.resolution

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
