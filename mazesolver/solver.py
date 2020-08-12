import time
import threading
from queue import Queue, Empty
from typing import Tuple
from json import dumps

import numpy as np

from mazesolver.image import MazeImage
from mazesolver.pubsub import PUBLISHER, ProcessWorker
import multiprocessing.queues


class Solver(ProcessWorker):
    VISITED_COLOR = (200, 200, 200)
    SOLUTION_COLOR = (0, 0, 255)

    def __init__(self):
        super().__init__(daemon=True)

    def get_adjacent_pixels(self, pixel: Tuple[int, int]):
        x, y = pixel
        return [(x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)]

    def mark_pixel_as_visited(self, pixel: Tuple[int, int], image):
        image[pixel] = 200

    def is_unvisited_pixel(self, pixel, image) -> bool:
        p = image[pixel]
        return p != 200  # and p != self.SOLUTION_COLOR

    def mark_solution(self, path, image):
        for x in path:
            image.result[x] = self.SOLUTION_COLOR

    def run(self):
        while True:
            self.received.wait()
            while True:
                try:
                    kwargs = self.input_queue.get(block=True, timeout=1)
                except multiprocessing.queues.Empty:
                    break
                if kwargs.get("start", False):
                    self.solve(*kwargs["data"])
            self.received.clear()

    def solve(self, image: MazeImage, start: Tuple[int, int], end: Tuple[int, int]):
        start = (start[1], start[0])
        end = (end[1], end[0])
        height, width, _ = image.pixels.shape
        queue = [[start]]
        iterations = 1
        start_time = time.time()
        visited_array = np.zeros(image.bw_pixels.shape, dtype=np.uint8)
        while queue:
            path = queue.pop(0)
            pixel = path[-1]
            if pixel == end:
                self.mark_solution(path, image)
                x = visited_array.nonzero()
                self.output_queue.put_nowait(
                    {"topic": "ImagePixelReplaceRequest", "pixels": x}
                )
                return path
            adjacent_pixels = self.get_adjacent_pixels(pixel)
            for p in adjacent_pixels:
                y, x = p
                if x < 0 or y < 0 or x >= width or y >= height:
                    continue
                if image.bw_pixels[p] == 0:
                    continue
                elif self.is_unvisited_pixel(p, visited_array):
                    self.mark_pixel_as_visited(p, visited_array)
                    new_path = list(path)
                    new_path.append(p)
                    queue.append(new_path)
                    iterations += 1
            end_time = time.time()
            if end_time - start_time > 1 / 40:
                start_time = time.time()
                x = visited_array.nonzero()
                self.output_queue.put_nowait(
                    {"topic": "ImagePixelReplaceRequest", "pixels": x}
                )
