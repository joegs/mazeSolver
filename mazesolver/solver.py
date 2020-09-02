from queue import Empty, Full
from typing import Any, Dict, List, Optional

import numpy as np

from mazesolver.pubsub import ProcessWorker
from mazesolver.state import ApplicationState
from mazesolver.timer import Timer
from mazesolver.types import Color, Point



class Solver(ProcessWorker):
    VISITED_VALUE = 200
    VISITED_COLOR = Color(200, 200, 200)
    SOLUTION_COLOR = Color(0, 0, 255)

    def __init__(self) -> None:
        super().__init__(input_size=1, output_size=1, daemon=True)
        self.reset = False
        self.waiting = False
        self.image: np.ndarray = np.zeros(0)
        self.visited: np.ndarray = np.zeros(0)
        self.solution: np.ndarray = np.zeros(0)
        self.start_point = Point(0, 0)
        self.end_point = Point(0, 0)
        self.frametime = 1 / 15
        self.timer = Timer()

    def _load_state(self, state: ApplicationState) -> None:
        # start and end points are inverted, since image indexes are in the
        # form (y, x), instead of (x, y)
        self.image = state.image
        self.start_point = state.start_point[::-1]
        self.end_point = state.end_point[::-1]
        self.frametime = 1 / int(state.framerate)
        self.visited = np.zeros(self.image.bw_pixels.shape, dtype=np.uint8)
        self.solution = np.zeros(self.image.bw_pixels.shape, dtype=np.uint8)

    def _get_adjacent_pixels(self, pixel: Point) -> List[Point]:
        x, y = pixel
        return [Point(x + 1, y), Point(x, y + 1), Point(x - 1, y), Point(x, y - 1)]

    def _mark_solution(self, path: List[Point]) -> None:
        for x in path:
            self.solution[x] = self.VISITED_VALUE

    def _send_visited_pixels(self, block: bool = False) -> None:
        region = self.visited.nonzero()
        try:
            self.output_queue.put(
                {
                    "topic": "ImagePixelReplaceRequest",
                    "region": region,
                    "color": self.VISITED_COLOR,
                },
                block=block,
                timeout=0.5,
            )
        except Full:
            pass

    def _send_solution(self) -> None:
        region = self.solution.nonzero()
        try:
            self.output_queue.put(
                {
                    "topic": "ImagePixelReplaceRequest",
                    "region": region,
                    "color": self.SOLUTION_COLOR,
                },
                block=True,
                timeout=0.5,
            )
        except Full:
            pass

    def _send_image_reset_request(self) -> None:
        try:
            self.output_queue.put(
                {"topic": "ImageResetRequest"}, block=True, timeout=0.5,
            )
        except Full:
            pass

    def _send_done_message(self) -> None:
        try:
            self.output_queue.put(
                {"topic": "MazeSolveDone"}, block=True, timeout=0.5,
            )
        except Full:
            pass

    def _process_run_message(self, kwargs: Any) -> None:
        if kwargs.get("start", False):
            state = kwargs["state"]
            self.solve(state)
        elif kwargs.get("reset", False):
            self.response.set()

    def run(self) -> None:
        while True:
            message_received = False
            self.received.wait()
            while True:
                try:
                    kwargs = self.input_queue.get_nowait()
                except Empty:
                    break
                message_received = True
                self._process_run_message(kwargs)
            if message_received:
                self.clear_queue()

    def _process_solving_message(self, kwargs: Dict[str, bool]) -> None:
        if kwargs.get("stop", False):
            self._wait_for_resume()
        elif kwargs.get("reset", False):
            self.reset = True

    def _check_messages(self) -> None:
        if not self.received.is_set():
            return
        while True:
            message_received = False
            while True:
                try:
                    kwargs = self.input_queue.get(block=False)
                except Empty:
                    break
                message_received = True
                self._process_solving_message(kwargs)
            if message_received:
                self.clear_queue()
                break

    def _process_waiting_message(self, kwargs: Any) -> None:
        if kwargs.get("resume", False):
            self.waiting = False
            self.clear_queue()
        elif kwargs.get("reset", False):
            self.waiting = False
            self.reset = True
            self.clear_queue()

    def _wait_for_resume(self) -> None:
        self.waiting = True
        self.received.clear()
        while self.waiting:
            message_received = False
            self.received.wait()
            while True:
                try:
                    kwargs = self.input_queue.get_nowait()
                except Empty:
                    break
                message_received = True
                self._process_waiting_message(kwargs)
            if message_received:
                self.clear_queue()

    def solve(self, state: ApplicationState) -> Optional[List[Point]]:
        self.clear_queue()
        self._load_state(state)
        queue = [[self.start_point]]
        height, width, _ = self.image.pixels.shape
        self.timer.start()
        while queue:
            path = queue.pop(0)
            current_pixel = path[-1]
            if current_pixel == self.end_point:
                self._mark_solution(path)
                self._send_visited_pixels(block=True)
                self._send_solution()
                self.clear_queue()
                self._send_done_message()
                return path
            adjacent_pixels = self._get_adjacent_pixels(current_pixel)
            for pixel in adjacent_pixels:
                y, x = pixel
                if (
                    x < 0 or y < 0 or x >= width or y >= height
                ) or self.image.bw_pixels[pixel] == 0:
                    continue
                if self.visited[pixel] != self.VISITED_VALUE:
                    self.visited[pixel] = self.VISITED_VALUE
                    new_path = list(path) + [pixel]
                    queue.append(new_path)
            self.timer.measure()
            if self.timer.elapsed_time > self.frametime:
                self.timer.start()
                self._send_visited_pixels()
                self._check_messages()
                if self.reset:
                    self.reset = False
                    self._send_image_reset_request()
                    self.response.set()
                    return None
        self._send_done_message()
        return None
