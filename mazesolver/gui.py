import importlib.resources
import tkinter as tk
from tkinter import filedialog, ttk
from typing import Any, Union

from mazesolver.config import DEFAULT_FRAMERATE, DEFAULT_RESOLUTION
from mazesolver.image import MazeImage
from mazesolver.pubsub import PUBLISHER, Subscriber
from mazesolver.types import Color, Size


class GuiElement:
    def __init__(self, parent: Union[tk.Widget, tk.Tk]) -> None:
        self.frame = ttk.Frame(parent)

    def _setup(self) -> None:
        pass

    def grid(self, *args: Any, **kwargs: Any) -> None:
        self.frame.grid(*args, **kwargs)
        self._setup()


class ImageArea(GuiElement):
    MAX_WIDTH = 600
    MAX_HEIGHT = 600

    def __init__(self, parent: Union[tk.Widget, tk.Tk], image: MazeImage) -> None:
        super().__init__(parent)
        self.label = ttk.Label(self.frame)
        self.image = image

    def _get_scaled_size(self) -> Size:
        height, width, _ = self.image.pixels.shape
        ratio = width / height
        if width > height:
            scaled_width = self.MAX_WIDTH
            scaled_height = int(scaled_width / ratio)
        else:
            scaled_height = self.MAX_HEIGHT
            scaled_width = int(scaled_height * ratio)
        size = Size(scaled_width, scaled_height)
        return size

    def _image_clicked(self, event: tk.Event) -> None:
        if not self.image.loaded:
            return
        x: int = event.x  # type: ignore[attr-defined]
        y: int = event.y  # type: ignore[attr-defined]
        scaled_width, scaled_height = self._get_scaled_size()
        height, width, _ = self.image.pixels.shape
        real_x = int(x * (width / scaled_width))
        real_y = int(y * (height / scaled_height))
        PUBLISHER.queue_message("ImageClicked", x=real_x, y=real_y)

    def update_image(self) -> None:
        if not self.image.loaded:
            return
        size = self._get_scaled_size()
        tk_image = self.image.get_tk_image(size)
        self.label.configure(image=tk_image)
        self.label.image = tk_image  # type: ignore[attr-defined]

    def clear_image(self) -> None:
        self.label.configure(image="")
        self.label.image = None  # type: ignore[attr-defined]

    def change_image(self, image_path: str) -> None:
        try:
            self.image.load_image(image_path)
        except ValueError:
            self.clear_image()
            PUBLISHER.queue_message("ImageLoadingError")
        self.update_image()

    def replace_pixels(self, region: Any, color: Color) -> None:
        self.image.result[region] = color
        self.update_image()

    def _setup(self) -> None:
        self.frame.configure(padding=20)
        self.label.grid(column=0, row=0)
        self.label.bind("<Button-1>", self._image_clicked)
        self._setup_subscribers()

    def _setup_subscribers(self) -> None:
        subscribers = [
            Subscriber("ImageChangeRequest", function=self.change_image),
            Subscriber("ImageUpdateRequest", function=self.update_image),
            Subscriber("ImagePixelReplaceRequest", function=self.replace_pixels),
        ]
        for subscriber in subscribers:
            PUBLISHER.register_subscriber(subscriber)


class ImageControl(GuiElement):
    def __init__(self, parent: Union[tk.Widget, tk.Tk]) -> None:
        super().__init__(parent)
        self.load_image_button = ttk.Button(self.frame, text="Load Image")

    def select_image(self) -> None:
        filename = filedialog.askopenfilename(title="Select an Image")
        if not filename:
            return
        PUBLISHER.queue_message("MazeCancelRequest")
        PUBLISHER.queue_message("ImageSelectionRequest", image_path=filename)

    def _setup(self) -> None:
        self.frame.columnconfigure(0, weight=1)
        self.load_image_button.grid(column=0, row=0, sticky="WE")
        self.load_image_button.configure(command=self.select_image)


class SolveControl(GuiElement):
    def __init__(self, parent: Union[tk.Widget, tk.Tk]):
        super().__init__(parent)
        self.solve_button = ttk.Button(self.frame, text="Solve")
        self.stop_button = ttk.Button(self.frame, text="Stop")
        self.resume_button = ttk.Button(self.frame, text="Resume")
        self.cancel_button = ttk.Button(self.frame, text="Cancel")

    def solve_command(self) -> None:
        PUBLISHER.queue_message("MazeSolveRequest")

    def stop_command(self) -> None:
        PUBLISHER.queue_message("MazeStopRequest")

    def resume_command(self) -> None:
        PUBLISHER.queue_message("MazeResumeRequest")

    def cancel_command(self) -> None:
        PUBLISHER.queue_message("MazeCancelRequest")

    def _setup(self) -> None:
        self.frame.columnconfigure(0, weight=1)
        self.solve_button.grid(column=0, row=0, sticky="WE", pady=(0, 10))
        self.stop_button.grid(column=0, row=1, sticky="WE", pady=(0, 10))
        self.resume_button.grid(column=0, row=2, sticky="WE", pady=(0, 10))
        self.cancel_button.grid(column=0, row=3, sticky="WE")
        self.solve_button.configure(command=self.solve_command)
        self.stop_button.configure(command=self.stop_command)
        self.resume_button.configure(command=self.resume_command)
        self.cancel_button.configure(command=self.cancel_command)


class SaveControl(GuiElement):
    def __init__(self, parent: Union[tk.Widget, tk.Tk]):
        super().__init__(parent)
        self.save_button = ttk.Button(self.frame, text="Save Image")

    def save_command(self) -> None:
        filename = filedialog.asksaveasfilename(
            title="Save Image",
            defaultextension="png",
            filetypes=[("PNG", ".png"), ("JPG", ".jpg"), ("JPEG", ".jpeg")],
        )
        if not filename:
            return
        PUBLISHER.queue_message("ImageSaveRequest", image_path=filename)

    def _setup(self) -> None:
        self.frame.columnconfigure(0, weight=1)
        self.save_button.grid(column=0, row=0, sticky="WE")
        self.save_button.configure(command=self.save_command)


class PointsControl(GuiElement):
    def __init__(self, parent: Union[tk.Widget, tk.Tk]) -> None:
        super().__init__(parent)
        self.start_button = ttk.Button(self.frame, text="Set Start Point")
        self.end_button = ttk.Button(self.frame, text="Set End Point")

    def start_point_command(self) -> None:
        PUBLISHER.queue_message("PointChangeRequest", kind="start")

    def end_point_command(self) -> None:
        PUBLISHER.queue_message("PointChangeRequest", kind="end")

    def _setup(self) -> None:
        self.frame.columnconfigure(0, weight=1)
        self.start_button.grid(column=0, row=0, sticky="WE", pady=(0, 10))
        self.end_button.grid(column=0, row=1, sticky="WE")
        self.start_button.configure(command=self.start_point_command)
        self.end_button.configure(command=self.end_point_command)


class ResolutionControl(GuiElement):
    def __init__(self, parent: Union[tk.Widget, tk.Tk]) -> None:
        super().__init__(parent)
        self.label = ttk.Label(self.frame, text="Scale Resolution")
        self.entry = ttk.Entry(self.frame, width=10)
        self.string_var = tk.StringVar(value=f"{DEFAULT_RESOLUTION}")
        self._setup_subscribers()

    def reset(self) -> None:
        self.string_var.set(f"{DEFAULT_RESOLUTION}")

    def _entry_changed(self, *_: Any) -> None:
        resolution = self.string_var.get()
        PUBLISHER.queue_message("ResolutionChangeRequest", resolution=resolution)

    def _setup(self) -> None:
        self.frame.columnconfigure(0, minsize=100)
        self.frame.columnconfigure(1, weight=1)
        self.label.grid(column=0, row=0, padx=(0, 10), sticky="W")
        self.entry.grid(column=1, row=0, sticky="WE")
        self.entry.configure(textvariable=self.string_var)
        self.string_var.trace_add("write", self._entry_changed)

    def _setup_subscribers(self) -> None:
        subscribers = [Subscriber("ResolutionResetRequest", function=self.reset)]
        for subscriber in subscribers:
            PUBLISHER.register_subscriber(subscriber)


class FramerateControl(GuiElement):
    def __init__(self, parent: Union[tk.Widget, tk.Tk]) -> None:
        super().__init__(parent)
        self.label = ttk.Label(self.frame, text="Framerate")
        self.entry = ttk.Entry(self.frame, width=10)
        self.string_var = tk.StringVar(value=f"{DEFAULT_FRAMERATE}")
        self._setup_subscribers()

    def reset(self) -> None:
        self.string_var.set(f"{DEFAULT_FRAMERATE}")

    def _entry_changed(self, *_: Any) -> None:
        framerate = self.string_var.get()
        PUBLISHER.queue_message("FramerateChangeRequest", framerate=framerate)

    def _setup(self) -> None:
        self.frame.columnconfigure(0, minsize=100)
        self.frame.columnconfigure(1, weight=1)
        self.label.grid(column=0, row=0, padx=(0, 10), sticky="W")
        self.entry.grid(column=1, row=0, sticky="WE")
        self.entry.configure(textvariable=self.string_var)
        self.string_var.trace_add("write", self._entry_changed)

    def _setup_subscribers(self) -> None:
        subscribers = [Subscriber("FramerateResetRequest", function=self.reset)]
        for subscriber in subscribers:
            PUBLISHER.register_subscriber(subscriber)


class ControlArea(GuiElement):
    def __init__(self, parent: Union[tk.Widget, tk.Tk]) -> None:
        super().__init__(parent)
        self.image_control = ImageControl(self.frame)
        self.points_control = PointsControl(self.frame)
        self.solve_control = SolveControl(self.frame)
        self.save_control = SaveControl(self.frame)
        self.resolution_control = ResolutionControl(self.frame)
        self.framerate_control = FramerateControl(self.frame)

    def _setup(self) -> None:
        self.frame.configure(padding=20)
        self.image_control.grid(column=0, row=0, sticky="NWE", pady=(0, 10))
        self.points_control.grid(column=0, row=1, sticky="NWE", pady=(10, 10))
        self.solve_control.grid(column=0, row=2, sticky="NWE", pady=(10, 10))
        self.save_control.grid(column=0, row=3, sticky="NWE", pady=(10, 10))
        self.resolution_control.grid(column=0, row=4, sticky="NWE", pady=(10, 10))
        self.framerate_control.grid(column=0, row=5, sticky="NWE", pady=(0, 10))


class ApplicationGui:
    def __init__(self, image: MazeImage):
        self.root = tk.Tk()
        self.root.title("Maze Solver")
        self.control_area = ControlArea(self.root)
        self.image_area = ImageArea(self.root, image)
        self._setup()

    def _setup(self) -> None:
        self.root.minsize(640, 480)
        self.root.rowconfigure(0, weight=1)
        self.control_area.grid(column=0, row=0, sticky="NSWE")
        self.image_area.grid(column=1, row=0, sticky="NW")
        self._load_icon()

    def _load_icon(self) -> None:
        path = importlib.resources.path("mazesolver", "icon.ico")
        with path as file:
            self.root.iconbitmap(file)

    def _periodic_refresh(self) -> None:
        PUBLISHER.send_messages()
        self.root.after(1000 // 60, self._periodic_refresh)

    def start(self) -> None:
        self._periodic_refresh()
        self.root.mainloop()
