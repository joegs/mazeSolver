from mazesolver.controller import ApplicationController
from mazesolver.gui import ApplicationGui
from mazesolver.solver import Solver
from mazesolver.pubsub import PUBLISHER, ProcessSubscriber
from mazesolver.image import MazeImage

if __name__ == "__main__":
    image = MazeImage()
    controller = ApplicationController(image)
    gui = ApplicationGui(image)
    solver = Solver()
    subscriber = ProcessSubscriber("Maze", worker=solver)
    PUBLISHER.register_subscriber(subscriber)
    gui.start()
