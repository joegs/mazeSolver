from mazesolver.event import EventListener, EVENT_PROCESSOR
from mazesolver.solver import Solver
from mazesolver.image import MazeImage


class Controller:
    def __init__(self, image):
        self.image = image
        self.start_point = (0, 0)
        self.end_point = (0, 0)
        self.point_change = ""
        self.solver = Solver()
        self.setup_listeners()

    def _point_change(self, kind: str):
        self.point_change = kind

    def _image_clicked(self, x: int, y: int):
        if self.point_change == "start":
            self.start_point = (x, y)
        if self.point_change == "end":
            self.end_point = (x, y)
        self.point_change = ""

    def _solve_maze(self):
        x = self.solver.solve(self.image, self.start_point, self.end_point)
        EVENT_PROCESSOR.emit_event("UpdateImage")

    def setup_listeners(self):
        position_listener = EventListener("PointChange")
        image_listener = EventListener("ImageClicked")
        solve_listener = EventListener("SolveMaze")
        EVENT_PROCESSOR.register_listener(position_listener)
        EVENT_PROCESSOR.register_listener(image_listener)
        EVENT_PROCESSOR.register_listener(solve_listener)
        position_listener.receive_event = self._point_change
        image_listener.receive_event = self._image_clicked
        solve_listener.receive_event = self._solve_maze
