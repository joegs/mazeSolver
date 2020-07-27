import tkinter as tk
from tkinter import filedialog, ttk
from typing import List

from mazesolver.event import EVENT_PROCESSOR, EventListener
from mazesolver.image import MazeImage


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

    def update_image(self):
        tk_image = self.image.get_tk_image(self.IMAGE_SIZE)
        self.label.configure(image=tk_image)
        self.label.image = tk_image

    def _image_clicked(self, event):
        x = event.x
        y = event.y
        width, height, _ = self.image.pixels.shape
        real_x = int(x * (width / self.IMAGE_SIZE[0]))
        real_y = int(y * (width / self.IMAGE_SIZE[1]))
        EVENT_PROCESSOR.emit_event("ImageClicked", x=real_x, y=real_y)

    def setup(self):
        self.frame.configure(padding=20)
        self.label.grid(column=0, row=0)
        self.label.bind("<Button-1>", self._image_clicked)
        self.update_image()
        self.setup_listeners()

    def setup_listeners(self):
        change_image_listener = EventListener("Image Changed")
        update_image_listener = EventListener("UpdateImage")
        EVENT_PROCESSOR.register_listener(change_image_listener)
        EVENT_PROCESSOR.register_listener(update_image_listener)
        change_image_listener.receive_event = self.change_image
        update_image_listener.receive_event = self.update_image


class ControlArea(GuiElement):
    def __init__(self, parent):
        super().__init__(parent)
        self.load_image_button = self._create_image_load_button()
        self.solve_button = self._create_solve_button()
        self.start_point_button = self._create_start_point_button()
        self.end_point_button = self._create_end_point_button()
        self.image_filename = ""

    def setup(self):
        self.frame.configure(padding=20)
        self.load_image_button.grid(column=0, row=0, sticky="NWE", pady=(0, 10))
        self.solve_button.grid(column=0, row=1, sticky="NWE", pady=(0, 10))
        self.start_point_button.grid(column=0, row=2, sticky="NWE", pady=(0, 10))
        self.end_point_button.grid(column=0, row=3, sticky="NWE")

    def _select_image_command(self):
        filename = filedialog.askopenfilename(title="Select an Image")
        self.image_filename = filename
        EVENT_PROCESSOR.emit_event("Image Changed", image_path=filename)

    def _create_image_load_button(self):
        button = ttk.Button(self.frame, text="Load Image", command=self._select_image_command)
        return button

    def _set_start_point_command(self):
        EVENT_PROCESSOR.emit_event("PointChange", kind="start")

    def _create_start_point_button(self):
        button = ttk.Button(
            self.frame, text="Set Start Point", command=self._set_start_point_command
        )
        return button

    def _set_end_point_command(self):
        EVENT_PROCESSOR.emit_event("PointChange", kind="end")

    def _create_end_point_button(self):
        button = ttk.Button(self.frame, text="Set End Point", command=self._set_end_point_command)
        return button

    def _solve_maze_command(self):
        EVENT_PROCESSOR.emit_event("SolveMaze")

    def _create_solve_button(self):
        button = ttk.Button(self.frame, text="Solve", command=self._solve_maze_command)
        return button


class Application:
    def __init__(self, image: MazeImage):
        self.root = tk.Tk()
        self.control_area = ControlArea(self.root)
        self.image_area = ImageArea(self.root, image)
        self.setup()

    def setup(self):
        # style = ttk.Style()
        # style.configure("TFrame", foreground="green", background="green")
        self.root.minsize(640, 480)
        self.root.rowconfigure(0, weight=1)
        self.control_area.grid(column=0, row=0, sticky="NSWE")
        self.image_area.grid(column=1, row=0)
        self.setup_listeners()

    def start(self):
        self.root.mainloop()

    def _update_gui(self):
        EVENT_PROCESSOR.emit_event("UpdateImage")
        self.root.update()

    def setup_listeners(self):
        update_gui_listener = EventListener("UpdateGui")
        EVENT_PROCESSOR.register_listener(update_gui_listener)
        update_gui_listener.receive_event = self._update_gui
