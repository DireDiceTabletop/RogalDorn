from picamera2 import Picamera2
import time


class Camera:
    def __init__(self, width=1280, height=720):
        self.picam2 = Picamera2()

        config = self.picam2.create_preview_configuration(
            main={"size": (width, height)}
        )

        self.picam2.configure(config)

    def start(self):
        self.picam2.start()
        time.sleep(2)

    def stop(self):
        self.picam2.stop()

    def capture_array(self):
        return self.picam2.capture_array()

    def capture_file(self, filename):
        self.picam2.capture_file(filename)
