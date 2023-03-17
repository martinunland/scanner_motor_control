import logging
from multiprocessing.pool import ThreadPool
from PDx_110_42_motor import Motor

log = logging.getLogger(__name__)

class ScannerControl:

    def connect(self, ports: list, baudrate=9600) -> None:
        port0, port1, port2 = ports
        self.motors = {
            0: Motor(port0, baudrate),
            1: Motor(port1, baudrate),
            2: Motor(port2, baudrate),
        }
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
    
    


