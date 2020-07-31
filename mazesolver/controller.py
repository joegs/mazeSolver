from mazesolver.event import EventListener, EVENT_PROCESSOR
from mazesolver.solver import Solver
from mazesolver.gui import Application
from mazesolver.image import MazeImage


class Controller:
    def __init__(self):
        self.start_point = (0, 0)
        self.end_point = (0, 0)
        self.point_change = ""
        self.framerate = 20
        self.image = MazeImage()
        self.application = Application(self.image)
        self.solver = Solver()
        self.setup_listeners()

    def _point_change(self, kind: str):
        self.point_change = kind

    def _image_clicked(self, x: int, y: int):
        if self.point_change == "start":
            self.start_point = (x, y)
        if self.point_change == "end":
            self.end_point = (x, y)
        if self.point_change:
            self.image.reset_result()
            self.image.mark_point(self.start_point, color=(255, 0, 0), size=3)
            self.image.mark_point(self.end_point, color=(255, 255, 0), size=3)
            EVENT_PROCESSOR.emit_event("UpdateImage")
        self.point_change = ""

    def _solve_maze(self):
        self.image.reset_result()
        self.solver.solve(self.image, self.start_point, self.end_point, self.framerate)
        EVENT_PROCESSOR.emit_event("UpdateImage")

    def _reset_points(self, image_path):
        self.start_point = (0, 0)
        self.end_point = (0, 0)

    def _change_framerate(self, framerate: str):
        try:
            integer_framerate = int(framerate)
            if integer_framerate < 5 or integer_framerate > 30:
                return
        except ValueError:
            return
        self.framerate = integer_framerate

    def _change_resolution(self, resolution: str):
        try:
            integer_resolution = int(resolution)
            if integer_resolution < 50:
                return
        except ValueError:
            return
        self.image.scaled_resolution = integer_resolution

    def setup_listeners(self):
        listeners = [
            EventListener("PointChange", self._point_change),
            EventListener("ImageClicked", self._image_clicked),
            EventListener("SolveMaze", self._solve_maze),
            EventListener("ImageChanged", self._reset_points),
            EventListener("FramerateChanged", self._change_framerate),
            EventListener("ResolutionChanged", self._change_resolution),
        ]
        for listener in listeners:
            EVENT_PROCESSOR.register_listener(listener)

    def start(self):
        self.application.start()
