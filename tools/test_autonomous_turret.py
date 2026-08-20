import time

import cv2
import pigpio

from config import HALL_SENSORS, TURRET
from control.aiming import AimingController
from control.turret_aim import apply_aiming_command
from hardware.continuous_servo import ContinuousRotationServo
from hardware.hall_sensor import HallSensor
from hardware.turret import Turret
from vision.camera import Camera
from vision.detector import FaceDetector
from vision.template_reacquirer import TemplateReacquirer
from vision.tracker import TargetTracker


# ---------------------------------------------------------
# Camera
# ---------------------------------------------------------

WIDTH = 320
HEIGHT = 180
ROTATION = 270

# Temporarily disabled while we recalibrate against the
# ACTUAL frame dimensions after camera rotation.
CAMERA_X_OFFSET = 0


# ---------------------------------------------------------
# Aiming
# ---------------------------------------------------------

DEADZONE = 12
MAX_ERROR = 120
CONFIRM_FRAMES = 1


# ---------------------------------------------------------
# Homing
# ---------------------------------------------------------

HOMING_SPEED = 0.25
HOMING_TIMEOUT = 3.0


# ---------------------------------------------------------
# Template recovery
# ---------------------------------------------------------

RECOVERY_THRESHOLD = 0.55
RECOVERY_SEARCH_SCALE = 3.0

# Only used after MOSSE has actually lost the target.
# This allows the turret/camera assembly to settle before
# we attempt local reacquisition.
RECOVERY_SETTLE_TIME = 0.05


def create_turret(
    pi: pigpio.pi,
) -> Turret:
    """
    Create the Hall-protected turret.

    LEFT and RIGHT are always from the tank's perspective
    while driving forwards.
    """

    left_sensor = HallSensor(
        pi=pi,
        gpio=HALL_SENSORS["left"],
    )

    home_sensor = HallSensor(
        pi=pi,
        gpio=HALL_SENSORS["home"],
    )

    right_sensor = HallSensor(
        pi=pi,
        gpio=HALL_SENSORS["right"],
    )

    servo = ContinuousRotationServo(
        pi=pi,
        gpio=TURRET["gpio"],
        stop=TURRET["stop"],
        forward=TURRET["forward"],
        reverse=TURRET["reverse"],
    )

    return Turret(
        servo=servo,
        left_direction=TURRET["tank_left_direction"],
        left_limit=left_sensor,
        home_sensor=home_sensor,
        right_limit=right_sensor,
    )


def create_mosse_tracker():
    """
    Create a new MOSSE tracker.
    """

    return cv2.legacy.TrackerMOSSE_create()


def target_to_bbox(
    target,
) -> tuple[int, int, int, int]:
    """
    Convert our Target object into an OpenCV bounding box.
    """

    return (
        int(target.x),
        int(target.y),
        int(target.width),
        int(target.height),
    )


def acquire_initial_target(
    camera: Camera,
    detector: FaceDetector,
    target_selector: TargetTracker,
):
    """
    Use YuNet to acquire the initial face.

    The turret remains stationary during acquisition.
    """

    print()
    print("==============================")
    print("YUNET FACE ACQUISITION")
    print("==============================")
    print()
    print("Searching for face...")
    print("Try to remain fairly still during acquisition.")
    print()

    while True:
        frame = camera.capture_array()

        detection_start = time.perf_counter()

        targets = detector.detect(
            frame
        )

        detection_time = (
            time.perf_counter()
            - detection_start
        )

        target = target_selector.select_target(
            targets
        )

        if target is None:
            print(
                f"No face found  "
                f"detect={detection_time:.2f}s"
            )

            continue

        bbox = target_to_bbox(
            target
        )

        print()
        print(
            f"FACE ACQUIRED  "
            f"x={target.x}  "
            f"y={target.y}  "
            f"w={target.width}  "
            f"h={target.height}  "
            f"detect={detection_time:.2f}s"
        )

        # Save the exact frame used for the initial
        # YuNet acquisition and MOSSE initialisation.
        #
        # Camera.capture_array() returns RGB while
        # cv2.imwrite() expects BGR.
        debug_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_RGB2BGR,
        )

        cv2.imwrite(
            "autonomous_start_frame.jpg",
            debug_frame,
        )

        print()
        print(
            "Saved initial camera frame to:"
        )
        print(
            "autonomous_start_frame.jpg"
        )
        print(
            f"Frame shape: {frame.shape}"
        )

        return (
            frame,
            bbox,
        )


def main() -> None:
    pi = None
    turret = None
    camera = None

    try:
        # -------------------------------------------------
        # pigpio
        # -------------------------------------------------

        pi = pigpio.pi()

        if not pi.connected:
            raise RuntimeError(
                "Could not connect to pigpio."
            )

        # -------------------------------------------------
        # Turret hardware
        # -------------------------------------------------

        turret = create_turret(
            pi
        )

        # -------------------------------------------------
        # Camera
        # -------------------------------------------------

        camera = Camera(
            width=WIDTH,
            height=HEIGHT,
            rotation=ROTATION,
        )

        camera.start()

        # -------------------------------------------------
        # Vision
        # -------------------------------------------------

        detector = FaceDetector(
            score_threshold=0.5,
        )

        target_selector = TargetTracker()

        reacquirer = TemplateReacquirer(
            threshold=RECOVERY_THRESHOLD,
            search_scale=RECOVERY_SEARCH_SCALE,
        )

        # -------------------------------------------------
        # Aiming controller
        # -------------------------------------------------

        aiming = AimingController(
            deadzone=DEADZONE,
            max_error=MAX_ERROR,
            confirm_frames=CONFIRM_FRAMES,
        )

        # -------------------------------------------------
        # Startup
        # -------------------------------------------------

        print()
        print("======================================")
        print("AUTONOMOUS TURRET TRACKING TEST")
        print("======================================")
        print()
        print(
            "LEFT and RIGHT are tank-relative."
        )
        print(
            "Hall limit protection remains active."
        )
        print()

        # -------------------------------------------------
        # Safety gate 1: Hall sensors / homing
        # -------------------------------------------------

        print("STAGE 1: HALL SENSOR / HOMING TEST")
        print("----------------------------------")
        print()
        print(
            "Make sure the turret has room to rotate "
            "safely."
        )
        print()
        print(
            "The turret will automatically search for "
            "the HOME Hall sensor."
        )
        print()

        input(
            "Press Enter to start the Hall sensor / "
            "homing test..."
        )

        print()
        print("Homing turret...")

        turret.home(
            speed=HOMING_SPEED,
            timeout=HOMING_TIMEOUT,
        )

        if not turret.at_home:
            raise RuntimeError(
                "Turret failed to reach HOME."
            )

        print()
        print("HOME FOUND")
        print("Hall sensor / homing test complete.")
        print()

        # Make sure we're definitely stationary while
        # waiting for the next stage.
        turret.stop()

        # -------------------------------------------------
        # Safety gate 2: vision / autonomous movement
        # -------------------------------------------------

        print("STAGE 2: FACE TRACKING")
        print("----------------------")
        print()
        print(
            "YuNet will first acquire your face."
        )
        print(
            "MOSSE will then take over for fast tracking."
        )
        print()
        print(
            "Once tracking starts, the turret will move "
            "automatically."
        )
        print()

        input(
            "Press Enter to start face acquisition "
            "and tracking..."
        )

        # -------------------------------------------------
        # Initial YuNet acquisition
        # -------------------------------------------------

        frame, bbox = acquire_initial_target(
            camera=camera,
            detector=detector,
            target_selector=target_selector,
        )

        # -------------------------------------------------
        # Initialise MOSSE
        # -------------------------------------------------

        tracker = create_mosse_tracker()

        tracker.init(
            frame,
            bbox,
        )

        # Store the initial face appearance for local
        # recovery later.
        reacquirer.remember(
            frame,
            bbox,
        )

        aiming.reset()

        print()
        print("==============================")
        print("MOSSE TRACKING STARTED")
        print("==============================")
        print()
        print("Press Ctrl+C to stop.")
        print()

        previous_loop_time = (
            time.perf_counter()
        )

        # -------------------------------------------------
        # Main autonomous loop
        # -------------------------------------------------

        while True:
            # ---------------------------------------------
            # Capture next frame
            # ---------------------------------------------

            capture_start = (
                time.perf_counter()
            )

            frame = camera.capture_array()

            capture_time = (
                time.perf_counter()
                - capture_start
            )

            # ---------------------------------------------
            # Update MOSSE
            # ---------------------------------------------

            track_start = (
                time.perf_counter()
            )

            success, bbox = tracker.update(
                frame
            )

            track_time = (
                time.perf_counter()
                - track_start
            )

            # ---------------------------------------------
            # Tracking lost
            # ---------------------------------------------

            if not success:
                turret.stop()
                aiming.reset()

                print()
                print("==============================")
                print("MOSSE LOST")
                print("==============================")
                print()
                print(
                    "Attempting local template recovery..."
                )

                # Allow any remaining mechanical movement
                # in the turret/camera mount to settle.
                time.sleep(
                    RECOVERY_SETTLE_TIME
                )

                # Take a fresh frame after settling.
                recovery_capture_start = (
                    time.perf_counter()
                )

                recovery_frame = (
                    camera.capture_array()
                )

                recovery_capture_time = (
                    time.perf_counter()
                    - recovery_capture_start
                )

                # Search locally around the last known
                # target position.
                recovery_start = (
                    time.perf_counter()
                )

                recovery = reacquirer.reacquire(
                    recovery_frame
                )

                recovery_time = (
                    time.perf_counter()
                    - recovery_start
                )

                # -----------------------------------------
                # Local recovery failed
                # -----------------------------------------

                if recovery is None:
                    print()
                    print("LOCAL RECOVERY FAILED")

                    print(
                        f"capture="
                        f"{recovery_capture_time * 1000:.0f}ms  "
                        f"search="
                        f"{recovery_time * 1000:.0f}ms"
                    )

                    print()
                    print(
                        "No YuNet fallback is enabled in "
                        "this test yet."
                    )
                    print(
                        "Stopping autonomous tracking."
                    )

                    break

                # -----------------------------------------
                # Local recovery successful
                # -----------------------------------------

                (
                    recovered_bbox,
                    recovery_score,
                ) = recovery

                recovered_x = int(
                    recovered_bbox[0]
                )

                recovered_y = int(
                    recovered_bbox[1]
                )

                recovered_width = int(
                    recovered_bbox[2]
                )

                recovered_height = int(
                    recovered_bbox[3]
                )

                print()
                print(
                    f"LOCAL RECOVERY FOUND  "
                    f"score={recovery_score:.2f}"
                )

                print(
                    f"bbox="
                    f"({recovered_x}, "
                    f"{recovered_y}, "
                    f"{recovered_width}, "
                    f"{recovered_height})"
                )

                print(
                    f"capture="
                    f"{recovery_capture_time * 1000:.0f}ms  "
                    f"search="
                    f"{recovery_time * 1000:.0f}ms"
                )

                # -----------------------------------------
                # Create fresh MOSSE tracker
                # -----------------------------------------

                tracker = create_mosse_tracker()

                tracker.init(
                    recovery_frame,
                    recovered_bbox,
                )

                # The recovered target now becomes our
                # latest remembered appearance.
                reacquirer.remember(
                    recovery_frame,
                    recovered_bbox,
                )

                aiming.reset()

                print()
                print("MOSSE REINITIALISED")
                print("Resuming tracking...")
                print()

                # Do not issue a turret correction from the
                # template match itself.
                #
                # Let MOSSE confirm the target position on
                # the next loop iteration.
                continue

            # ---------------------------------------------
            # MOSSE successfully tracked target
            # ---------------------------------------------

            (
                x,
                y,
                width,
                height,
            ) = (
                int(value)
                for value in bbox
            )

            # Store this last good target BEFORE moving the
            # turret.
            reacquirer.remember(
                frame,
                bbox,
            )

            # ---------------------------------------------
            # Actual frame dimensions
            # ---------------------------------------------

            # IMPORTANT:
            #
            # After camera rotation, the actual captured
            # frame may not have the same width/height
            # orientation as WIDTH and HEIGHT above.
            #
            # Always calculate the image centre from the
            # frame that MOSSE is actually seeing.
            frame_height, frame_width = (
                frame.shape[:2]
            )

            # ---------------------------------------------
            # Target centre
            # ---------------------------------------------

            target_centre_x = (
                x
                + width / 2
            )

            target_centre_y = (
                y
                + height / 2
            )

            # ---------------------------------------------
            # Image error
            # ---------------------------------------------

            raw_error_x = int(
                target_centre_x
                - frame_width / 2
            )

            # Currently zero while we establish the true
            # physical camera-centre calibration.
            error_x = (
                raw_error_x
                - CAMERA_X_OFFSET
            )

            error_y = int(
                target_centre_y
                - frame_height / 2
            )

            # ---------------------------------------------
            # Aiming decision
            # ---------------------------------------------

            command = aiming.calculate(
                error_x
            )

            # ---------------------------------------------
            # Apply one short turret correction
            # ---------------------------------------------

            (
                physical_speed,
                pulse_duration,
            ) = apply_aiming_command(
                turret=turret,
                command=command,
            )

            # ---------------------------------------------
            # Loop timing / FPS
            # ---------------------------------------------

            now = time.perf_counter()

            loop_time = (
                now
                - previous_loop_time
            )

            previous_loop_time = now

            if loop_time > 0:
                fps = (
                    1.0
                    / loop_time
                )
            else:
                fps = 0.0

            # ---------------------------------------------
            # Diagnostics
            # ---------------------------------------------

            print(
                f"RAW={raw_error_x:+4d}  "
                f"X={error_x:+4d}  "
                f"Y={error_y:+4d}  "
                f"AIM="
                f"{command.direction.value.upper():8s}  "
                f"STRENGTH="
                f"{command.strength:.2f}  "
                f"SERVO="
                f"{physical_speed:.2f}  "
                f"PULSE="
                f"{pulse_duration * 1000:3.0f}ms  "
                f"ACTIVE="
                f"{aiming.active_direction.value.upper():8s}  "
                f"FPS="
                f"{fps:4.1f}  "
                f"capture="
                f"{capture_time * 1000:3.0f}ms  "
                f"track="
                f"{track_time * 1000:3.0f}ms"
            )

    except KeyboardInterrupt:
        print()
        print("Test cancelled.")

    except (RuntimeError, TimeoutError) as error:
        print()
        print(
            f"TEST FAILED: {error}"
        )

    finally:
        # -------------------------------------------------
        # Safe shutdown
        # -------------------------------------------------

        if turret is not None:
            turret.stop()

        if camera is not None:
            camera.close()

        if turret is not None:
            turret.close()

        if pi is not None:
            pi.stop()

        print()
        print("==============================")
        print("TEST FINISHED")
        print("==============================")
        print()
        print("Turret stopped.")
        print("Camera closed.")


if __name__ == "__main__":
    main()
