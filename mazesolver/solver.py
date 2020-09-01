from queue import Empty, Full
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from mazesolver.pubsub import ProcessWorker
from mazesolver.state import ApplicationState
from mazesolver.timer import Timer


class Solver(ProcessWorker):
    VISITED_VALUE = 200
    VISITED_COLOR = (200, 200, 200)
    SOLUTION_COLOR = (0, 0, 255)

    def __init__(self) -> None:
        super().__init__(input_size=1, output_size=1, daemon=True)
        self.reset = False
        self.waiting = False
        self.image: np.ndarray = np.zeros(0)
        self.visited: np.ndarray = np.zeros(0)
        self.solution: np.ndarray = np.zeros(0)
        self.start_point = (0, 0)
        self.end_point = (0, 0)
        self.frametime = 1 / 15
        self.timer = Timer()

    def load_state(self, state: ApplicationState) -> None:
        # start and end points are inverted, since image indexes are in the
        # form (y, x), instead of (x, y)
        self.image = state.image
        self.start_point = state.start_point[::-1]
        self.end_point = state.end_point[::-1]
        self.frametime = 1 / int(state.framerate)
        self.visited = np.zeros(self.image.bw_pixels.shape, dtype=np.uint8)
        self.solution = np.zeros(self.image.bw_pixels.shape, dtype=np.uint8)

    def get_adjacent_pixels(self, pixel: Tuple[int, int]) -> List[Tuple[int, int]]:
        x, y = pixel
        return [(x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)]

    def mark_solution(self, path: List[Tuple[int, int]]) -> None:
        for x in path:
            self.solution[x] = self.VISITED_VALUE

    def send_visited_pixels(self, block: bool = False) -> None:
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

    def send_solution(self) -> None:
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

    def send_image_reset_request(self) -> None:
        try:
            self.output_queue.put(
                {"topic": "ImageResetRequest"}, block=True, timeout=0.5,
            )
        except Full:
            pass

    def send_done_message(self) -> None:
        try:
            self.output_queue.put(
                {"topic": "MazeSolveDone"}, block=True, timeout=0.5,
            )
        except Full:
            pass

    def process_run_message(self, kwargs: Any) -> None:
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
                self.process_run_message(kwargs)
            if message_received:
                self.clear_queue()

    def process_solving_message(self, kwargs: Dict[str, bool]) -> None:
        if kwargs.get("stop", False):
            self.wait_for_resume()
        elif kwargs.get("reset", False):
            self.reset = True

    def check_messages(self) -> None:
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
                self.process_solving_message(kwargs)
            if message_received:
                self.clear_queue()
                break

    def process_waiting_message(self, kwargs: Any) -> None:
        if kwargs.get("resume", False):
            self.waiting = False
            self.clear_queue()
        elif kwargs.get("reset", False):
            self.waiting = False
            self.reset = True
            self.clear_queue()

    def wait_for_resume(self) -> None:
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
                self.process_waiting_message(kwargs)
            if message_received:
                self.clear_queue()

    def solve(self, state: ApplicationState) -> Optional[List[Tuple[int, int]]]:
        self.clear_queue()
        self.load_state(state)
        queue = [[self.start_point]]
        height, width, _ = self.image.pixels.shape
        self.timer.start()
        while queue:
            path = queue.pop(0)
            current_pixel = path[-1]
            if current_pixel == self.end_point:
                self.mark_solution(path)
                self.send_visited_pixels(block=True)
                self.send_solution()
                self.clear_queue()
                self.send_done_message()
                return path
            adjacent_pixels = self.get_adjacent_pixels(current_pixel)
            for pixel in adjacent_pixels:
                y, x = pixel
                if (
                    x < 0 or y < 0 or x >= width or y >= height
                ) or self.image.bw_pixels[pixel] == 0:
                    continue
                elif self.visited[pixel] != self.VISITED_VALUE:
                    self.visited[pixel] = self.VISITED_VALUE
                    new_path = list(path) + [pixel]
                    queue.append(new_path)
            self.timer.measure()
            if self.timer.elapsed_time > self.frametime:
                self.timer.start()
                self.send_visited_pixels()
                self.check_messages()
                if self.reset:
                    self.reset = False
                    self.send_image_reset_request()
                    self.response.set()
                    return None
        self.send_done_message()
        return None
