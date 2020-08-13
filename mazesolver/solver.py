import threading
import time
from queue import Empty
from typing import Tuple

import numpy as np

from mazesolver.image import MazeImage
from mazesolver.pubsub import PUBLISHER, ProcessWorker


class Solver(ProcessWorker):
    VISITED_VALUE = 200
    VISITED_COLOR = (200, 200, 200)
    SOLUTION_COLOR = (0, 0, 255)

    def __init__(self):
        super().__init__(daemon=True)
        self.reset = False

    def get_adjacent_pixels(self, pixel: Tuple[int, int]):
        x, y = pixel
        return [(x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)]

    def mark_pixel_as_visited(self, pixel: Tuple[int, int], image: np.ndarray):
        image[pixel] = self.VISITED_VALUE

    def is_unvisited_pixel(self, pixel, image: np.ndarray) -> bool:
        p = image[pixel]
        return p != self.VISITED_VALUE

    def mark_solution(self, path, image: np.ndarray):
        for x in path:
            image[x] = self.VISITED_VALUE

    def run(self):
        while True:
            self.received.wait()
            while True:
                try:
                    kwargs = self.input_queue.get(block=False)
                except Empty:
                    break
                if kwargs.get("start", False):
                    data = kwargs["data"]
                    self.solve(**data)
            self.clear_queue()

    def send_pixels(self, array: np.ndarray, color: Tuple[int, int, int]):
        region = array.nonzero()
        self.output_queue.put_nowait(
            {"topic": "ImagePixelReplaceRequest", "region": region, "color": color,}
        )

    def wait_for_resume(self):
        self.received.clear()
        stop = False
        while not stop:
            self.received.wait()
            while True:
                try:
                    kwargs = self.input_queue.get(block=False)
                except Empty:
                    break
                if kwargs.get("resume", False):
                    stop = True
                elif kwargs.get("reset", False):
                    self.reset = True
                    stop = True
            self.received.clear()
        self.clear_queue()

    def process_messages(self):
        if not self.received.is_set():
            return
        while True:
            try:
                kwargs = self.input_queue.get(block=False)
            except Empty:
                break
            if kwargs.get("stop", False):
                self.wait_for_resume()
            elif kwargs.get("reset", False):
                self.reset = True
        self.clear_queue()

    def solve(
        self,
        image: MazeImage,
        start: Tuple[int, int],
        end: Tuple[int, int],
        framerate: int = 15,
    ):
        # start and end are inverted, since image indexes are in the
        # form (y, x), instead of (x, y)
        start = (start[1], start[0])
        end = (end[1], end[0])
        height, width, _ = image.pixels.shape
        queue = [[start]]
        visited = np.zeros(image.bw_pixels.shape, dtype=np.uint8)
        solution = np.zeros(image.bw_pixels.shape, dtype=np.uint8)
        start_time = time.time()
        while queue:
            path = queue.pop(0)
            pixel = path[-1]
            if pixel == end:
                self.mark_solution(path, solution)
                self.send_pixels(visited, self.VISITED_COLOR)
                self.send_pixels(solution, self.SOLUTION_COLOR)
                self.clear_queue()
                return path
            adjacent_pixels = self.get_adjacent_pixels(pixel)
            for p in adjacent_pixels:
                # Invert the pixels, to get the correct values
                y, x = p
                if x < 0 or y < 0 or x >= width or y >= height:
                    continue
                if image.bw_pixels[p] == 0:
                    continue
                elif self.is_unvisited_pixel(p, visited):
                    self.mark_pixel_as_visited(p, visited)
                    new_path = list(path)
                    new_path.append(p)
                    queue.append(new_path)
            end_time = time.time()
            if end_time - start_time > 1 / framerate:
                start_time = time.time()
                self.send_pixels(visited, self.VISITED_COLOR)
                self.process_messages()
                if self.reset:
                    self.reset = False
                    return
