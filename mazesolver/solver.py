from mazesolver.image import MazeImage
from typing import Tuple
import numpy as np


class Solver:
    VISITED_COLOR = (200, 200, 200)
    SOLUTION_COLOR = (0, 0, 255)

    def get_adjacent_pixels(self, pixel: Tuple[int, int]):
        x, y = pixel
        return [(x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)]

    def mark_pixel_as_visited(self, pixel: Tuple[int, int], image: MazeImage):
        image.overlay[pixel] = self.VISITED_COLOR

    def is_unvisited_pixel(self, pixel, image) -> bool:
        r, g, b = image.overlay[pixel]
        return (r, g, b) != self.VISITED_COLOR

    def mark_solution(self, path, image):
        for x in path:
            image.overlay[x] = self.SOLUTION_COLOR

    def solve(self, image: MazeImage, start: Tuple[int, int], end: Tuple[int, int]):
        width, height, _ = image.pixels.shape
        queue = [[start]]
        while queue:
            path = queue.pop(0)
            pixel = path[-1]
            if pixel == end:
                self.mark_solution(path, image)
                return path
            adjacent_pixels = self.get_adjacent_pixels(pixel)
            for p in adjacent_pixels:
                x, y = p
                if x < 0 or y < 0 or x >= width or y >= height:
                    continue
                if image.bw_pixels[p] == 0:
                    continue
                elif self.is_unvisited_pixel(p, image):
                    self.mark_pixel_as_visited(p, image)
                    new_path = list(path)
                    new_path.append(p)
                    queue.append(new_path)
