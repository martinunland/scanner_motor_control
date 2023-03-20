import logging
from multiprocessing.pool import ThreadPool
from PDx_110_42_motor import Motor

log = logging.getLogger(__name__)

class ScannerControl:

    def __init__(self):
        self.motors = {}

    def connect(self, ports: list, baudrate=9600) -> None:
        """
        Connect to each motor on the provided ports with the specified baudrate.

        Args:
            ports (list): A list of ports to connect to the motors.
            baudrate (int, optional): Baudrate for the serial connection. Defaults to 9600.
        """
        for i, port in enumerate(ports):
            self.motors[i] = Motor(port, i, baudrate)
        
        with ThreadPool(processes=len(self.motors)) as pool:
            pool.map(lambda motor: motor.connect(), self.motors.values())

    def disconnect(self):
        with ThreadPool(processes=len(self.motors)) as pool:
            pool.map(lambda motor: motor.disconnect(), self.motors.values())

    def set_motors_speed(self, max_speed: int = 5000, max_acceleration: int = 1500):
        """
        Set the maximum speed and acceleration for all motors.

        Args:
            max_speed (int, optional): Maximum speed for the motors. Defaults to 5000.
            max_acceleration (int, optional): Maximum acceleration for the motors. Defaults to 1500.
        """
        for motor in self.motors.values():
            motor.set_speed_and_acceleration(max_speed=max_speed, max_acceleration=max_acceleration)

    def find_reference_position(self):
        with ThreadPool(processes=len(self.motors)) as pool:
            pool.map(lambda motor: motor.search_reference_position(), self.motors.values())

    def activate_stall_guard(self):
        with ThreadPool(processes=len(self.motors)) as pool:
            pool.map(lambda motor: motor.activate_stall_guard(), self.motors.values())

    def deactivate_stall_guard(self):
        with ThreadPool(processes=len(self.motors)) as pool:
            pool.map(lambda motor: motor.deactivate_stall_guard(), self.motors.values())

    def move_motors_to_position(self, positions: list) -> None:
        """
        Move each motor to its respective position in the given list of positions in parallel.

        Args:
            positions (list): A list of positions for each motor, [pos_motor_0, pos_motor_1, pos_motor_2].
        """
        with ThreadPool(processes=len(self.motors)) as pool:
            pool.starmap(lambda motor, position: motor.move_to_step(position), zip(self.motors.values(), positions))


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
