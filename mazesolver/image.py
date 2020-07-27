from PIL import Image, ImageTk
import cv2
import numpy as np
from typing import Tuple, Optional
import time


class MazeImage:
    DEFAULT_SIZE = (300, 300)

    def __init__(self, image_path: str):
        self.pixels: np.ndarray
        self.bw_pixels: np.ndarray
        self.result: np.ndarray
        self.load_image(image_path)

    def get_scaled_size(self):
        height, width, _ = self.pixels.shape
        ratio = width / height
        if width > height:
            scaled_width = self.DEFAULT_SIZE[0]
            scaled_height = int(scaled_width / ratio)
        else:
            scaled_height = self.DEFAULT_SIZE[1]
            scaled_width = int(scaled_height * ratio)
        size = (scaled_width, scaled_height)
        return size

    def load_image(self, image_path: str):
        self.pixels = cv2.imread(image_path, cv2.IMREAD_COLOR)
        scaled_size = self.get_scaled_size()
        self.pixels = cv2.resize(self.pixels, scaled_size)
        bw_pixels = cv2.cvtColor(self.pixels, cv2.COLOR_BGR2GRAY)
        _, bw_pixels = cv2.threshold(bw_pixels, 150, 255, cv2.THRESH_BINARY)
        self.bw_pixels = bw_pixels
        self.result = np.copy(self.pixels)

    def get_tk_image(self, size: Optional[Tuple[int, int]] = None) -> ImageTk.PhotoImage:
        pixels = self.result
        if size:
            pixels = cv2.resize(pixels, size)
        image = Image.fromarray(pixels)
        tk_image = ImageTk.PhotoImage(image)
        return tk_image

    def get_resized_pixels(self, size: Tuple[int, int]) -> np.ndarray:
        resized_pixels = cv2.resize(self.pixels, size)
        return resized_pixels

    def resize(self, size: Tuple[int, int]) -> np.ndarray:
        self.pixels = cv2.resize(self.pixels, size)

    def reset_result(self):
        self.result = np.copy(self.pixels)

    def mark_point(
        self, point: Tuple[int, int], color: Tuple[int, int, int] = (0, 255, 0), size: int = 2,
    ):
        x, y = point
        self.result[y : y + size, x : x + size] = color
