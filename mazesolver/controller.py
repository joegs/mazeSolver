from mazesolver.event import EventListener, EVENT_PROCESSOR
from mazesolver.solver import Solver
from mazesolver.image import MazeImage


class Controller:
    def __init__(self, image: MazeImage):
        self.image = image
        self.start_point = (0, 0)
        self.end_point = (0, 0)
        self.point_change = ""
        self.framerate = 20
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

    def setup_listeners(self):
        position_listener = EventListener("PointChange")
        image_listener = EventListener("ImageClicked")
        solve_listener = EventListener("SolveMaze")
        image_changed_listener = EventListener("ImageChanged")
        framerate_listener = EventListener("FramerateChanged")
        EVENT_PROCESSOR.register_listener(position_listener)
        EVENT_PROCESSOR.register_listener(image_listener)
        EVENT_PROCESSOR.register_listener(solve_listener)
        EVENT_PROCESSOR.register_listener(image_changed_listener)
        EVENT_PROCESSOR.register_listener(framerate_listener)
        position_listener.receive_event = self._point_change
        image_listener.receive_event = self._image_clicked
        solve_listener.receive_event = self._solve_maze
        image_changed_listener.receive_event = self._reset_points
        framerate_listener.receive_event = self._change_framerate
