import logging
import time
import serial
from TMCL_firmware_control import TMCL, AxisParameters

log = logging.getLogger(__name__)

class Motor:
    def __init__(self, port, motor_number, baudrate):
        self.motor_number = motor_number
        self.baudrate = baudrate
        self.port = port
        self.ser = None
        self.STALL_THRESHOLD = 3
        self.DECAY_THRESHOLD = 2048

    def connect(self):
        if self.ser is not None and self.ser.isOpen():
            log.info(f"Motor {self.motor_number} is already connected to {self.ser.port}")
            return

        self.ser = serial.Serial(self.port, self.baudrate, timeout=0.25)
        self.test_connection()

    def disconnect(self):
        if self.ser is not None and self.ser.isOpen():
            log.info(f"Closing connection to motor {self.motor_number} on port {self.ser.port}")
            self.ser.close()

    def test_connection(self):
        try:
            self.ser.write(TMCL.stop_motor_movement(0))
            self.ser.read(9)
            log.info(
                f"Successfully connected to motor {self.motor_number} on port {self.ser.port}"
            )
        except serial.SerialException as err:
            log.error(
                f"Failed to connect to motor {self.motor_number} on port {self.ser.port}: {err}"
            )
            raise

    def _write_to_serial(self, byte_cmd: bytearray):
        self.ser.write(byte_cmd)
        reply = self.ser.read(9)

    def _set_and_store(self, parameter: AxisParameters, value: int):
        self._write_to_serial(TMCL.set_axis_parameter(parameter, value))
        self._write_to_serial(TMCL.store_axis_parameter(parameter))

    def _get_parameter(self, parameter: AxisParameters):
        self._write_to_serial(TMCL.get_axis_parameter(parameter=parameter))

    def set_speed_and_acceleration(
        self, max_speed: int = 5000, max_acceleration: int = 1500
    ):
        log.debug(f"Motor {self.motor_number}: setting max speed to {max_speed} and max acceleration to {max_acceleration}.")
        self._set_and_store(AxisParameters.MIN_SPEED, 1)
        self._set_and_store(AxisParameters.MAX_SPEED, max_speed)
        self._set_and_store(AxisParameters.MAX_ACCELERATION, max_acceleration)
        self._set_and_store(AxisParameters.MICROSTEP_RESOLUTION, 6)

    def _stallguard_is_active(self)->bool:
        mixed_decay = self._get_parameter(AxisParameters.MIXED_DECAY_THRESHOLD)
        stallguard = self._get_parameter(AxisParameters.STALL_DETECTION_THRESHOLD)
        if (mixed_decay==self.DECAY_THRESHOLD) and (stallguard==self.STALL_THRESHOLD):
            return True
        return False

    def activate_stall_guard(self)->None:
        self._set_and_store(AxisParameters.MAX_SPEED, 1000)
        self._set_and_store(AxisParameters.MIXED_DECAY_THRESHOLD, self.DECAY_THRESHOLD)
        self._set_and_store(AxisParameters.STALL_DETECTION_THRESHOLD, self.STALL_THRESHOLD)

    def deactivate_stall_guard(self):
        self._set_and_store(AxisParameters.MAX_SPEED, 1000)
        self._set_and_store(AxisParameters.MIXED_DECAY_THRESHOLD, 100)
        self._set_and_store(AxisParameters.STALL_DETECTION_THRESHOLD, 0)

    def _check_if_finished_moving(self):
        MAX_FREEZE_TIME = 10
        position_old = self._get_parameter(AxisParameters.ACTUAL_POSITION_MICROSTEPS)
        last_move_time = time.time()
        while self._get_parameter(AxisParameters.TARGET_POSITION_REACHED) == 0:
            time.sleep(0.5)
            new_position = self._get_parameter(AxisParameters.ACTUAL_POSITION_MICROSTEPS)
            if new_position != position_old:
                last_move_time = time.time()
            elif time.time()-last_move_time>MAX_FREEZE_TIME:
                log.error(f"Motor {self.motor_number} cannot move from position {position_old} over {MAX_FREEZE_TIME} seconds, exiting...")
                raise

    def move_to_step(self, step_position):
        self._write_to_serial(TMCL.move_to_position(0, step_position))
        self._check_if_finished_moving()

    def search_reference_position(self):
        #activate stall guard if not active
        if not self._stallguard_is_active():
            self.activate_stall_guard()

        #Move motor left until speed = 0
        self._write_to_serial(TMCL.rotate_left_motor(900))

        while self._get_parameter(AxisParameters.ACTUAL_SPEED) != 0:
            time.sleep(0.25)

        #Set current position as reference 0
        self._write_to_serial(TMCL.set_axis_parameter(AxisParameters.ACTUAL_POSITION_MICROSTEPS, 0))

