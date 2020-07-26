from mazesolver.gui import Application
from mazesolver.controller import Controller
from mazesolver.image import MazeImage

if __name__ == "__main__":
    image = MazeImage("mazesolver/maze.png")
    a = Application(image)
    c = Controller(image)
    a.start()
