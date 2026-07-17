from vision.camera import Camera


camera = Camera()

print("Starting camera...")
camera.start()

print("Capturing image...")
camera.capture_file("camera_test.jpg")

camera.stop()

print("Done.")
