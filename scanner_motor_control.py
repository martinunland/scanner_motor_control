import logging
import serial
from TMCL_firmware_control import TMCL, AxisParameters


log = logging.getLogger(__name__)

class ScannerControl:
    def connect(self, ports: list, baudrate=9600) -> None:
        port0, port1, port2 = ports
        self.motors = {
            0: serial.Serial(port0, baudrate, timeout=0.25),  # x-axis (level 0)
            1: serial.Serial(port1, baudrate, timeout=0.25),  # y-axis (level 1)
            2: serial.Serial(port2, baudrate, timeout=0.25),
        }  # z-axis (level 2)
        self.test_connection()

    def test_connection(self):
        for key, motor in self.motors.items():
            try:
                motor.write(TMCL.stop_motor_movement(0))
                motor.read(9)
                log.info(f"Successfully connected to motor {key} on port {motor.port}")
            except serial.SerialException as err:
                log.error(f"Failed to connect to motor {key} on port {motor.port}: {err}")
                raise
