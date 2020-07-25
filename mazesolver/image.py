from PIL import Image, ImageTk
import cv2
import numpy as np
from typing import Tuple, Optional


class MazeImage:
    def __init__(self, image_path: str):
        self.pixels: np.array
        self.load_image(image_path)

    def load_image(self, image_path: str):
        pixels = cv2.imread(image_path, cv2.IMREAD_COLOR)
        pixels = cv2.cvtColor(pixels, cv2.COLOR_BGR2RGB)
        self.pixels = pixels

    def get_tk_image(self, size: Optional[Tuple[int, int]] = None) -> ImageTk.PhotoImage:
        if size:
            pixels = cv2.resize(self.pixels, size)
        else:
            pixels = self.pixels
        image = Image.fromarray(pixels)
        tk_image = ImageTk.PhotoImage(image)
        return tk_image

    def get_resized_pixels(self, size: Tuple[int, int]) -> np.array:
        resized_pixels = cv2.resize(self.pixels, size)
        return resized_pixels

    def resize(self, size: Tuple[int, int]) -> np.array:
        self.pixels = cv2.resize(self.pixels, size)
