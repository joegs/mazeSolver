from dataclasses import dataclass

from mazesolver.image import MazeImage
from mazesolver.types import Point


@dataclass
class ApplicationState:
    image: MazeImage
    resolution: str = "300"
    framerate: str = "15"
    start_point: Point = Point(0, 0)
    end_point: Point = Point(0, 0)
    working: bool = False
