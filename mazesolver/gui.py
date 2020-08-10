import tkinter as tk
from tkinter import filedialog, ttk
from typing import List

from mazesolver.image import MazeImage
from mazesolver.pubsub import PUBLISHER, THREAD_PUBLISHER, Subscriber, Worker


class GuiElement:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)

    def setup(self):
        pass

    def grid(self, *args, **kwargs):
        self.frame.grid(*args, **kwargs)
        self.setup()


class ImageArea(GuiElement):
    IMAGE_SIZE = (600, 600)

    def __init__(self, parent, image: MazeImage):
        super().__init__(parent)
        self.label = ttk.Label(self.frame)
        self.image = image

    def change_image(self, image_path: str):
        self.image.load_image(image_path)
        self.update_image()

    def get_scaled_size(self):
        height, width, _ = self.image.pixels.shape
        ratio = width / height
        if width > height:
            scaled_width = self.IMAGE_SIZE[0]
            scaled_height = int(scaled_width / ratio)
        else:
            scaled_height = self.IMAGE_SIZE[1]
            scaled_width = int(scaled_height * ratio)
        size = (scaled_width, scaled_height)
        return size

    def update_image(self):
        if self.image.pixels is None:
            return
        size = self.get_scaled_size()
        tk_image = self.image.get_tk_image(size)
        self.label.configure(image=tk_image)
        self.label.image = tk_image

    def _image_clicked(self, event):
        x = event.x
        y = event.y
        size = self.get_scaled_size()
        height, width, _ = self.image.pixels.shape
        real_x = int(x * (width / size[0]))
        real_y = int(y * (height / size[1]))
        PUBLISHER.send_message("ImageClicked", x=real_x, y=real_y)

    def setup(self):
        self.frame.configure(padding=20)
        self.label.grid(column=0, row=0)
        self.label.bind("<Button-1>", self._image_clicked)
        self.setup_subscribers()

    def setup_subscribers(self):
        subscribers = [
            Subscriber("ImageChangeRequest", function=self.change_image),
            Subscriber("UpdateImage", function=self.update_image),
        ]
        for subscriber in subscribers:
            PUBLISHER.register_subscriber(subscriber)


class ImageControl(GuiElement):
    def __init__(self, parent):
        super().__init__(parent)
        self.button = ttk.Button(self.frame, text="Load Image")

    def _select_image_command(self):
        filename = filedialog.askopenfilename(title="Select an Image")
        if not filename:
            return
        PUBLISHER.send_message("ImageChangeRequest", image_path=filename)

    def setup(self):
        self.frame.columnconfigure(0, weight=1)
        self.button.grid(column=0, row=0, sticky="WE")
        self.button.configure(command=self._select_image_command)


class SolveControl(GuiElement):
    def __init__(self, parent):
        super().__init__(parent)
        self.solve_button = ttk.Button(self.frame, text="Solve")
        self.stop_button = ttk.Button(self.frame, text="Stop")
        self.resume_button = ttk.Button(self.frame, text="Resume")

    def _solve_command(self):
        PUBLISHER.send_message("SolveMaze")

    def _stop_command(self):
        PUBLISHER.send_message("StopSolve")

    def _resume_command(self):
        PUBLISHER.send_message("ResumeMaze")

    def setup(self):
        self.frame.columnconfigure(0, weight=1)
        self.solve_button.grid(column=0, row=0, sticky="WE", pady=(0, 10))
        self.stop_button.grid(column=0, row=1, sticky="WE", pady=(0, 10))
        self.resume_button.grid(column=0, row=2, sticky="WE", pady=(0, 10))
        self.solve_button.configure(command=self._solve_command)
        self.stop_button.configure(command=self._stop_command)
        self.resume_button.configure(command=self._resume_command)


class PointsControl(GuiElement):
    def __init__(self, parent):
        super().__init__(parent)
        self.start_button = ttk.Button(self.frame, text="Set Start Point")
        self.end_button = ttk.Button(self.frame, text="Set End Point")

    def _start_point_command(self):
        PUBLISHER.send_message("PointChangeRequest", kind="start")

    def _end_point_command(self):
        PUBLISHER.send_message("PointChangeRequest", kind="end")

    def setup(self):
        self.frame.columnconfigure(0, weight=1)
        self.start_button.grid(column=0, row=0, sticky="WE", pady=(0, 10))
        self.end_button.grid(column=0, row=1, sticky="WE", pady=(0, 10))
        self.start_button.configure(command=self._start_point_command)
        self.end_button.configure(command=self._end_point_command)


class ResolutionControl(GuiElement):
    def __init__(self, parent):
        super().__init__(parent)
        self.label = ttk.Label(self.frame, text="Scale Resolution")
        self.entry = ttk.Entry(self.frame, width=10)
        self.string_var = tk.StringVar(value="300")

    def reset(self):
        self.string_var.set("300")

    def _entry_changed(self, *args):
        resolution = self.string_var.get()
        PUBLISHER.send_message("ResolutionChangeRequest", resolution=resolution)

    def setup(self):
        self.frame.columnconfigure(0, minsize=100)
        self.frame.columnconfigure(1, weight=1)
        self.label.grid(column=0, row=0, padx=(0, 10), sticky="W")
        self.entry.grid(column=1, row=0, sticky="WE")
        self.entry.configure(textvariable=self.string_var)
        self.string_var.trace_add("write", self._entry_changed)


class ControlArea(GuiElement):
    def __init__(self, parent):
        super().__init__(parent)
        self.image_control = ImageControl(self.frame)
        self.solve_control = SolveControl(self.frame)
        self.points_control = PointsControl(self.frame)
        self.resolution_control = ResolutionControl(self.frame)

    def setup(self):
        self.frame.configure(padding=20)
        self.image_control.grid(column=0, row=0, sticky="NWE", pady=(0, 10))
        self.points_control.grid(column=0, row=1, sticky="NWE", pady=(10, 10))
        self.solve_control.grid(column=0, row=2, sticky="NWE", pady=(10, 10))
        self.resolution_control.grid(column=0, row=3, sticky="NWE", pady=(0, 10))


class Application:
    def __init__(self, image: MazeImage):
        self.root = tk.Tk()
        self.control_area = ControlArea(self.root)
        self.image_area = ImageArea(self.root, image)
        self.setup()

    def setup(self):
        self.root.minsize(640, 480)
        self.root.rowconfigure(0, weight=1)
        self.control_area.grid(column=0, row=0, sticky="NSWE")
        self.image_area.grid(column=1, row=0, sticky="NW")

    def periodic_refresh(self):
        PUBLISHER.process_messages()
        THREAD_PUBLISHER.send_message("Maze", advance=True)
        self.root.after(1000 // 120, self.periodic_refresh)

    def start(self):
        self.periodic_refresh()
        self.root.mainloop()
