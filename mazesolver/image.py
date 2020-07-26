from PIL import Image, ImageTk
import cv2
import numpy as np
from typing import Tuple, Optional


class MazeImage:
    def __init__(self, image_path: str):
        self.pixels: np.ndarray
        self.bw_pixels: np.ndarray
        self.overlay: np.ndarray
        self.load_image(image_path)

    def load_image(self, image_path: str):
        pixels = cv2.imread(image_path, cv2.IMREAD_COLOR)
        bw_pixels = cv2.cvtColor(pixels, cv2.COLOR_BGR2GRAY)
        _, bw_pixels = cv2.threshold(bw_pixels, 150, 255, cv2.THRESH_BINARY)
        rgb_pixels = cv2.cvtColor(pixels, cv2.COLOR_BGR2RGB)
        self.pixels = rgb_pixels
        self.bw_pixels = bw_pixels
        self.overlay = np.zeros_like(self.pixels)

    def get_tk_image(self, size: Optional[Tuple[int, int]] = None) -> ImageTk.PhotoImage:
        x = np.array([0, 0, 0])
        p = np.copy(self.pixels)
        for i, _ in enumerate(self.overlay):
            for j, pixel in enumerate(self.overlay[i]):
                if (pixel == x).all():
                    continue
                p[i, j] = pixel
        if size:
            pixels = cv2.resize(p, size)
        else:
            pixels = p
        image = Image.fromarray(pixels)
        tk_image = ImageTk.PhotoImage(image)
        return tk_image

    def get_resized_pixels(self, size: Tuple[int, int]) -> np.ndarray:
        resized_pixels = cv2.resize(self.pixels, size)
        return resized_pixels

    def resize(self, size: Tuple[int, int]) -> np.ndarray:
        self.pixels = cv2.resize(self.pixels, size)
