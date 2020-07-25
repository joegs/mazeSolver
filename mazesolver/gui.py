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
        self.listener = EventListener("Image Changed")

    def change_image(self, image_path: str):
        self.image.load_image(image_path)
        self.update_image()

    def update_image(self):
        tk_image = self.image.get_tk_image(self.IMAGE_SIZE)
        self.label.configure(image=tk_image)
        self.label.image = tk_image

    def setup(self):
        self.frame.configure(padding=20)
        self.label.grid(column=0, row=0)
        EVENT_PROCESSOR.register_listener(self.listener)
        self.listener.receive_event = self.change_image
        self.update_image()


class ControlArea(GuiElement):
    def __init__(self, parent):
        super().__init__(parent)
        self.load_image_button = self._create_image_load_button()
        self.solve_button = self._create_solve_button()
        self.image_filename = ""

    def setup(self):
        self.frame.configure(padding=20)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=0)
        self.frame.rowconfigure(1, weight=1)
        self.load_image_button.grid(column=0, row=0, sticky="NW", pady=(0, 10))
        self.solve_button.grid(column=0, row=1, sticky="NE")

    def _select_image_command(self):
        filename = filedialog.askopenfilename(title="Select an Image")
        self.image_filename = filename
        EVENT_PROCESSOR.emit_event("Image Changed", image_path=filename)

    def _create_image_load_button(self):
        button = ttk.Button(self.frame, text="Load Image", command=self._select_image_command)
        return button

    def _solve_maze_command(self):
        pass

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

    def start(self):
        self.root.mainloop()
