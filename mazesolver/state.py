from dataclasses import dataclass
from typing import Tuple

from mazesolver.image import MazeImage


@dataclass
class ApplicationState:
    image: MazeImage
    resolution: str = "300"
    framerate: str = "15"
    start_point: Tuple[int, int] = (0, 0)
    end_point: Tuple[int, int] = (0, 0)
    working: bool = False
