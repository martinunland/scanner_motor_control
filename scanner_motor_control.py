import logging
from multiprocessing.pool import ThreadPool
from PDx_110_42_motor import Motor

log = logging.getLogger(__name__)

class ScannerControl:

    def __init__(self):
        self.motors = {}

    def connect(self, ports: list, baudrate=9600) -> None:
        for i, port in enumerate(ports):
            self.motors[i] = Motor(port, i, baudrate)
        
        with ThreadPool(processes=len(self.motors)) as pool:
            pool.map(lambda motor: motor.connect(), self.motors.values())

    def disconnect(self):
        with ThreadPool(processes=len(self.motors)) as pool:
            pool.map(lambda motor: motor.disconnect(), self.motors.values())

    def set_motors_speed(self, max_speed: int = 5000, max_acceleration: int = 1500):
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

    def move_motors_to_position(self, positions: list):
        with ThreadPool(processes=len(self.motors)) as pool:
            pool.starmap(lambda motor, position: motor.move_to_position(position), zip(self.motors.values(), positions))

    def configure_motors(self, config: dict):
        for motor in self.motors.values():
            motor.configure(config)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
