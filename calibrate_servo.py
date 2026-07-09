import pigpio
import time

GPIO = 23

pi = pigpio.pi()

if not pi.connected:
    print("Could not connect to pigpiod")
    exit()

print("Moving forward...")
pi.set_servo_pulsewidth(GPIO, 1800)

time.sleep(3)

print("Stopping...")
pi.set_servo_pulsewidth(GPIO, 1500)

time.sleep(3)

print("Reverse...")
pi.set_servo_pulsewidth(GPIO, 1200)

time.sleep(3)

print("Done.")

pi.set_servo_pulsewidth(GPIO, 0)
pi.stop()
