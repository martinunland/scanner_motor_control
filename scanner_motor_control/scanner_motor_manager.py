import logging
from multiprocessing.pool import ThreadPool
from typing import List
from .motor_controller import Motor

log = logging.getLogger(__name__)


class ScannerControl:
    def __init__(self):
        self.motors = {}
        self.DIST_PER_ROTS = [1.9983, 1.9983, 1.9959]  # measured by Raffi
        self.MAX_STEPs = [1303641, 1425174, 1342922] #maximal microstep of each axis
    def connect(self, ports: list, baudrate=9600) -> None:
        """
        Connect to each motor on the provided ports with the specified baudrate.

        Args:
            ports (list): A list of ports to connect to the motors.
            baudrate (int, optional): Baudrate for the serial connection. Defaults to 9600.
        """
        for i, (port, dist_per_rot, max_step) in enumerate(zip(ports, self.DIST_PER_ROTS, self.MAX_STEPs)):
            self.motors[i] = Motor(port, i, baudrate, dist_per_rot, max_step)

        with ThreadPool(processes=len(self.motors)) as pool:
            pool.map(lambda motor: motor.connect(), self.motors.values())

    def disconnect(self) -> None:
        with ThreadPool(processes=len(self.motors)) as pool:
            pool.map(lambda motor: motor.disconnect(), self.motors.values())

    def configure_motors(
        self, max_speed: int = 5000, max_acceleration: int = 1500
    ) -> None:
        """
        Set the maximum speed and acceleration for all motors.

        Args:
            max_speed (int, optional): Maximum speed for the motors. Defaults to 5000.
            max_acceleration (int, optional): Maximum acceleration for the motors. Defaults to 1500.
        """
        with ThreadPool(processes=len(self.motors)) as pool:
            pool.map(
                lambda motor: motor.set_speed_and_acceleration(
                    max_speed=max_speed, max_acceleration=max_acceleration
                ),
                self.motors.values(),
            )
        self.deactivate_stall_guard()
    def find_reference_position(self) -> None:
        with ThreadPool(processes=len(self.motors)) as pool:
            pool.map(
                lambda motor: motor.search_reference_position(), self.motors.values()
            )

    def activate_stall_guard(self) -> None:
        with ThreadPool(processes=len(self.motors)) as pool:
            pool.map(lambda motor: motor.activate_stall_guard(), self.motors.values())

    def deactivate_stall_guard(self) -> None:
        with ThreadPool(processes=len(self.motors)) as pool:
            pool.map(lambda motor: motor.deactivate_stall_guard(), self.motors.values())

    def get_current_position(self) -> None:
        position = []
        position_mm = []
        for motor in self.motors.values():
            pos_mm, pos_step = motor.get_current_position()
            position.append(pos_step)
            position_mm.append(pos_mm)
        return position_mm, position

    def move_to_absolute_position_in_mm(self, positions: list) -> None:
        """
        Move each motor to its respective position in the given list of positions in parallel.

        Args:
            positions (list): A list of positions for each motor, [pos_motor_0, pos_motor_1, pos_motor_2].
        """
        with ThreadPool(processes=len(self.motors)) as pool:
            pool.starmap(
                lambda motor, position: motor.move_absolute_position_in_mm(position),
                zip(self.motors.values(), positions),
            )

    def move_relative_distance_in_mm(self, distances: list) -> None:
        """
        Move each motor a distance in mm relative to current position

        Args:
            distances (list): A list of distance for each motor, [dis_motor_0, dis_motor_1, dis_motor_2].
        """
        with ThreadPool(processes=len(self.motors)) as pool:
            pool.starmap(
                lambda motor, distance: motor.move_relative_distance_in_mm(distance),
                zip(self.motors.values(), distances),
            )

    def check_position_in_mm_allowed(self, positions: list, relative: bool = False) -> List[bool]:
        valid = []
        for motor, position in zip(self.motors.values(), positions):
            bl, _ = motor.check_if_position_in_mm_allowed(position)
            valid.append(bl)
        return valid
    # I don't know if we will ever use it, but the following two methods allow use to write:
    # "with ScannerControl() as scanner:
    #   scanner.connect(ports, baudrate)
    #   scanner.set_motors_speed()
    #   ..."
    # And when we get out the with block, the scanner will automatically disconnect.
    # It is good to manage resources more effectively, but I don't know if we really need it in this case...
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
