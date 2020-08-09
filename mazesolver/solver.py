import time
import threading
from queue import Queue, Empty
from typing import Tuple

import numpy as np

from mazesolver.event import EVENT_PROCESSOR
from mazesolver.image import MazeImage
from mazesolver.pubsub import PUBLISHER, Subscriber, Worker


class Solver(Worker):
    VISITED_COLOR = (200, 200, 200)
    SOLUTION_COLOR = (0, 0, 255)

    def __init__(self):
        super().__init__(None)
        self.terminate = threading.Event()

    def get_adjacent_pixels(self, pixel: Tuple[int, int]):
        x, y = pixel
        return [(x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)]

    def mark_pixel_as_visited(self, pixel: Tuple[int, int], image: MazeImage):
        image.result[pixel] = self.VISITED_COLOR

    def is_unvisited_pixel(self, pixel, image) -> bool:
        p = tuple(image.result[pixel])
        return p != self.VISITED_COLOR and p != self.SOLUTION_COLOR

    def mark_solution(self, path, image):
        for x in path:
            image.result[x] = self.SOLUTION_COLOR

    def run(self):
        while True:
            self.receive.wait()
            try:
                args, kwargs = self.queue.get(block=True, timeout=1)
                self.solve(*args, **kwargs)
            except Empty:
                return
            self.receive.clear()

    def solve(self, image: MazeImage, start: Tuple[int, int], end: Tuple[int, int]):
        start = (start[1], start[0])
        end = (end[1], end[0])
        height, width, _ = image.pixels.shape
        queue = [[start]]
        iterations = 1
        start_time = time.time()
        while queue:
            if self.stop.is_set():
                # return
                self._stop()
            path = queue.pop(0)
            pixel = path[-1]
            if pixel == end:
                self.mark_solution(path, image)
                PUBLISHER.emit_event("UpdateImage")
                return path
            adjacent_pixels = self.get_adjacent_pixels(pixel)
            for p in adjacent_pixels:
                y, x = p
                if x < 0 or y < 0 or x >= width or y >= height:
                    continue
                if image.bw_pixels[p] == 0:
                    continue
                elif self.is_unvisited_pixel(p, image):
                    self.mark_pixel_as_visited(p, image)
                    new_path = list(path)
                    new_path.append(p)
                    queue.append(new_path)
                    iterations += 1
            end_time = time.time()
            if end_time - start_time > 1 / 20:
                start_time = time.time()
                PUBLISHER.emit_event("UpdateImage")
                time.sleep(0.0001)
