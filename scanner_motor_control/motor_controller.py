import logging
import time
from typing import Tuple
import serial
from .tmcl_interface import TMCL, TMCLPars, MotorMovement

log = logging.getLogger(__name__)


class Motor:
    def __init__(
        self, port: str, motor_number: int, baudrate: int, dist_per_rot: float, max_step: int
    ):
        self.motor_number = motor_number
        self.baudrate = baudrate
        self.port = port
        self._serial = None
        self.dist_per_rot = dist_per_rot
        self.STALL_THRESHOLD = 7
        self.DECAY_THRESHOLD = -1
        self.MAX_FREEZE_TIME = 10
        self.SET_MICROSTEP_RESO = 6
        self.MAX_STEP = max_step

    def connect(self) -> None:
        if self._serial is not None and self._serial.isOpen():
            log.info(
                f"Motor {self.motor_number} is already connected to {self._serial.port}"
            )
            return
        log.info(f"Connecting motor {self.motor_number} to {self.port}")
        self._serial = serial.Serial(self.port, self.baudrate, timeout=0.25)
        self.test_connection()

    def disconnect(self) -> None:
        if self._serial is not None and self._serial.isOpen():
            log.info(
                f"Closing connection to motor {self.motor_number} on port {self._serial.port}"
            )
            self._serial.close()

    def test_connection(self) -> None:
        """
        Test the connection to the motor by sending a stop command and checking for a reply.
        """
        try:
            self._write_to_serial(TMCL.stop_motor_movement())
            log.info(
                f"Successfully connected to motor {self.motor_number} on port {self._serial.port}"
            )
        except Exception as err:
            mssg = f"Failed to connect to motor {self.motor_number} on port {self._serial.port} with error: '{err}'. \n\t   ValueError starting with 'invalid literal ...' probably means that you have not started the motor :)"
            log.error(mssg)
            raise Exception(mssg)

    def _microsteps_to_mm(self, position: int) -> float:
        micsteps_per_rot = 200*(2 ** self.SET_MICROSTEP_RESO)
        distance = position * self.dist_per_rot / micsteps_per_rot
        return distance

    def _mm_to_microsteps(self, distance: float) -> int:
        micsteps_per_rot = 200 * (
            2 ** self.SET_MICROSTEP_RESO
        )
        position = int(distance / self.dist_per_rot * micsteps_per_rot)
        return position

    def _write_to_serial(self, byte_cmd: bytearray) -> int:
        self._serial.write(byte_cmd)
        time.sleep(0.1)
        return TMCL.decode_reply(self._serial.read(9))

    def _set_and_store(self, parameter: TMCLPars, value: int) -> None:
        self._write_to_serial(TMCL.set_axis_parameter(parameter, value))
        self._write_to_serial(TMCL.store_axis_parameter(parameter))

    def _get_parameter(self, parameter: TMCLPars) -> int:
        return self._write_to_serial(TMCL.get_axis_parameter(parameter=parameter))

    def set_speed_and_acceleration(
        self, max_speed: int = 5000, max_acceleration: int = 1500
    ) -> None:
        log.debug(
            f"Motor {self.motor_number}: setting max speed to {max_speed} and max acceleration to {max_acceleration}."
        )
        self._set_and_store(TMCLPars.MIN_SPEED, 1)
        self._set_and_store(TMCLPars.MAX_SPEED, max_speed)
        self._set_and_store(TMCLPars.MAX_ACCELERATION, max_acceleration)
        self._set_and_store(TMCLPars.MICROSTEP_RESOLUTION, self.SET_MICROSTEP_RESO)

    def activate_stall_guard(self) -> None:
        self._set_and_store(TMCLPars.MAX_SPEED, 1000)
        self._set_and_store(TMCLPars.MIXED_DECAY_THRESHOLD, 2048)
        self._set_and_store(TMCLPars.STALL_DETECTION_THRESHOLD, self.STALL_THRESHOLD)

    def deactivate_stall_guard(self) -> None:
        self._set_and_store(TMCLPars.MAX_SPEED, 1000)
        self._set_and_store(TMCLPars.MIXED_DECAY_THRESHOLD, self.DECAY_THRESHOLD)
        self._set_and_store(TMCLPars.STALL_DETECTION_THRESHOLD, 0)

    def _check_if_finished_moving(self) -> None:

        position_old = self._get_parameter(TMCLPars.ACTUAL_POSITION_MICROSTEPS)
        last_move_time = time.time()
        while self._get_parameter(TMCLPars.TARGET_POSITION_REACHED) == 0:
            time.sleep(0.5)
            new_position = self._get_parameter(TMCLPars.ACTUAL_POSITION_MICROSTEPS)
            if new_position != position_old:
                last_move_time = time.time()
            elif time.time() - last_move_time > self.MAX_FREEZE_TIME:
                log.error(
                    f"Motor {self.motor_number} cannot move from position {position_old} over {self.MAX_FREEZE_TIME} seconds, exiting..."
                )
                exit()

    def check_if_microstep_allowed(self, steps: int, relative : bool = False) -> Tuple[bool, str]:
        if relative:
            steps += self.get_current_position()[1]

        if steps > self.MAX_STEP:
            mssg = f"Motor {self.motor_number}: Requested position step {steps} larger than maximum allowed {self.MAX_STEP} ({self._microsteps_to_mm(self.MAX_STEP):.2f} mm)"
            return False, mssg
        elif steps < 0:
            mssg= f"Motor {self.motor_number}: Requested position step {steps} is negative."
            
            return False, mssg
        return True, "Valid"

    def check_if_position_in_mm_allowed(self, position: int, relative : bool = False) -> Tuple[bool, str]:
        return self.check_if_microstep_allowed(self._mm_to_microsteps(position), relative)

    def move_in_step(self, steps: int, mode: MotorMovement) -> None:
        """
        Move the motor using steps as unit.

        Args:
            steps (int): The target step position for the motor.
            mode (MotorMovement): move to absolute step position or relative to current step position
        """
        
        #TMCL has itsel a relative/absolute mode, but I will be working only in absolute, to be able to limit the min/max steps without the need of stallguard
        if mode == MotorMovement.RELATIVE:
            steps += self.get_current_position()[1]
        valid, mssg = self.check_if_microstep_allowed(steps)
        if not valid:
            log.error(mssg)
            raise ValueError(mssg)
        self._write_to_serial(TMCL.move_to_position(MotorMovement.ABSOLUTE, steps))
        self._check_if_finished_moving()

    def move_relative_distance_in_mm(self, distance_mm: float) -> None:
        """
        Move the motor a certain distance in mm.

        Args:
            distance_mm (float): The distance in mm to move the motor.
        """
        self.move_in_step(
            self._mm_to_microsteps(distance_mm), mode=MotorMovement.RELATIVE
        )

    def move_absolute_position_in_mm(self, position_mm: float) -> None:
        """
        Move the motor to the specified position in mm.

        Args:
            position_mm (float): The target position in mm.
        """
        self.move_in_step(
            self._mm_to_microsteps(position_mm), mode=MotorMovement.ABSOLUTE
        )

    def get_current_position(self) -> Tuple[float, int]:
        """
        Get the current position of the motor in both millimeters and microsteps.

        Returns:
            tuple[float, int]: A tuple containing the current position in millimeters (float) and
                           the current position in microsteps (int).
        """
        steps = self._get_parameter(TMCLPars.ACTUAL_POSITION_MICROSTEPS)
        return self._microsteps_to_mm(steps), steps

    def search_reference_position(self) -> None:
        self.activate_stall_guard()

        # Move motor left until speed = 0
        self._write_to_serial(TMCL.rotate_left_motor(900))

        while self._get_parameter(TMCLPars.ACTUAL_SPEED) != 0:
            time.sleep(0.5)
        # Set current position as reference 0
        self._write_to_serial(
            TMCL.set_axis_parameter(TMCLPars.ACTUAL_POSITION_MICROSTEPS, 0)
        )
        self.move_relative_distance_in_mm(0.5)

        self.deactivate_stall_guard()

    def print_maximum_step(self) -> None:
        # activate stall guard if not active
        self.activate_stall_guard()

        # Move motor left until speed = 0
        self._write_to_serial(TMCL.rotate_right_motor(900))

        while self._get_parameter(TMCLPars.ACTUAL_SPEED) != 0:
            time.sleep(0.5)

        self.move_relative_distance_in_mm(-0.5)
        self.deactivate_stall_guard()