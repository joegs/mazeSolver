from typing import NamedTuple


class Point(NamedTuple):
    x: int
    y: int


class Size(NamedTuple):
    width: int
    height: int


class Color(NamedTuple):
    r: int
    g: int
    b: int


class RegionOfInterest(NamedTuple):
    x1: int
    y1: int
    x2: int
    y2: int
