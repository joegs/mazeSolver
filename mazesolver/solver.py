import threading
import time
from queue import Empty, Full
from typing import Tuple

import numpy as np

from mazesolver.image import MazeImage
from mazesolver.pubsub import PUBLISHER, ProcessWorker


class Solver(ProcessWorker):
    VISITED_VALUE = 200
    VISITED_COLOR = (200, 200, 200)
    SOLUTION_COLOR = (0, 0, 255)

    def __init__(self):
        super().__init__(input_size=1, output_size=1, daemon=True)
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
            message_received = False
            self.received.wait()
            while True:
                try:
                    kwargs = self.input_queue.get_nowait()
                except Empty:
                    break
                message_received = True
                if kwargs.get("start", False):
                    data = kwargs["data"]
                    self.solve(**data)
                elif kwargs.get("reset", False):
                    self.response.set()
            if message_received:
                self.clear_queue()

    def send_pixels(self, array: np.ndarray, color: Tuple[int, int, int], block=False):
        region = array.nonzero()
        try:
            self.output_queue.put(
                {"topic": "ImagePixelReplaceRequest", "region": region, "color": color},
                block=block,
                timeout=0.5,
            )
        except Full:
            pass

    def send_image_reset_request(self):
        try:
            self.output_queue.put(
                {"topic": "ImageResetRequest"}, block=True, timeout=0.5,
            )
        except Full:
            pass

    def wait_for_resume(self):
        self.received.clear()
        stop = False
        while not stop:
            message_received = False
            self.received.wait()
            while True:
                try:
                    kwargs = self.input_queue.get_nowait()
                except Empty:
                    break
                message_received = True
                if kwargs.get("resume", False):
                    stop = True
                    break
                elif kwargs.get("reset", False):
                    self.reset = True
                    stop = True
                    break
            if message_received:
                self.clear_queue()

    def process_messages(self):
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
                if kwargs.get("stop", False):
                    self.wait_for_resume()
                elif kwargs.get("reset", False):
                    self.reset = True
            if message_received:
                self.clear_queue()
                break

    def solve(
        self,
        image: MazeImage,
        start: Tuple[int, int],
        end: Tuple[int, int],
        framerate: int = 15,
    ):
        self.clear_queue()
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
                self.send_pixels(solution, self.SOLUTION_COLOR, block=True)
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
                    self.send_image_reset_request()
                    self.response.set()
                    return
