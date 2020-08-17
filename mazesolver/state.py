from mazesolver.image import MazeImage


class ApplicationState:
    def __init__(self, image: MazeImage):
        self.image = image
        self.resolution = "300"
        self.framerate = "15"
        self.start_point = (0, 0)
        self.end_point = (0, 0)
