from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageTk

from mazesolver.config import DEFAULT_SCALE_RESOLUTION
from mazesolver.types import Color, Size, RegionOfInterest


class MazeImage:
    def __init__(self) -> None:
        self.scaled_resolution = DEFAULT_SCALE_RESOLUTION
        self.pixels: np.ndarray = np.zeros(0)
        self.bw_pixels: np.ndarray = np.zeros(0)
        self.result: np.ndarray = np.zeros(0)
        self.overlay: List[Tuple[RegionOfInterest, Color]] = []
        self.loaded = False

    def _get_scaled_size(self) -> Size:
        height, width, _ = self.pixels.shape
        ratio = width / height
        if width > height:
            scaled_width = self.scaled_resolution
            scaled_height = int(scaled_width / ratio)
        else:
            scaled_height = self.scaled_resolution
            scaled_width = int(scaled_height * ratio)
        size = Size(scaled_width, scaled_height)
        return size

    def _load_pixels(self, image_path: str) -> None:
        self.pixels = cv2.imread(image_path, cv2.IMREAD_COLOR)
        self.pixels = cv2.cvtColor(self.pixels, cv2.COLOR_BGR2RGB)
        scaled_size = self._get_scaled_size()
        self.pixels = cv2.resize(self.pixels, scaled_size)

    def _load_bw_pixels(self) -> None:
        bw_pixels = cv2.cvtColor(self.pixels, cv2.COLOR_RGB2GRAY)
        _, bw_pixels = cv2.threshold(bw_pixels, 200, 255, cv2.THRESH_BINARY)
        self.bw_pixels = bw_pixels

    def load_image(self, image_path: str) -> None:
        if not image_path:
            return
        self._load_pixels(image_path)
        self._load_bw_pixels()
        self.result = np.copy(self.pixels)
        self.loaded = True

    def apply_overlay(self) -> None:
        for area, color in self.overlay:
            x1, y1, x2, y2 = area
            self.result[y1:y2, x1:x2] = color

    def get_tk_image(self, size: Optional[Size] = None) -> ImageTk.PhotoImage:
        self.apply_overlay()
        pixels = self.result
        if size:
            pixels = cv2.resize(pixels, size)
        image = Image.fromarray(pixels)
        tk_image = ImageTk.PhotoImage(image)
        return tk_image

    def save_result(self, image_path: str) -> None:
        image = Image.fromarray(self.result)
        image.save(image_path)

    def reset_result(self) -> None:
        self.result = np.copy(self.pixels)
