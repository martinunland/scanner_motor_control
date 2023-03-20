from enum import Enum
import logging

log = logging.getLogger(__name__)


class TMCLCommands(Enum):
    ROTATE_RIGHT = 1
    ROTATE_LEFT = 2
    STOP_MOTOR_MOVEMENT = 3
    MOVE_TO_POSITION = 4
    SET_AXIS_PARAMETER = 5
    GET_AXIS_PARAMETER = 6
    STORE_AXIS_PARAMETER = 7
    RESTORE_AXIS_PARAMETER = 8


class DefaultParameter(Enum):
    default = 0


class MotorMovement(Enum):
    ABSOLUTE = 0
    RELATIVE = 1


class TMCLPars(Enum):
    TARGET_POSITION_MICROSTEPS = 0
    ACTUAL_POSITION_MICROSTEPS = 1
    TARGET_SPEED = 2
    ACTUAL_SPEED = 3
    MAX_SPEED = 4
    MAX_ACCELERATION = 5
    MAX_CURRENT_mA = 6
    STANDBY_CURRENT_mA = 7
    TARGET_POSITION_REACHED = 8
    REFERENCE_SWITCH_STATUS = 9
    RIGHT_LIMIT_SWITCH_STATUS = 10
    LEFT_LIMIT_SWITCH_STATUS = 11
    RIGHT_LIMIT_SWITCH_DISABLE = 12
    LEFT_LIMIT_SWITCH_DISABLE = 13
    MIN_SPEED = 130
    ACTUAL_ACCELERATION = 135
    RAMP_MODE = 138
    MICROSTEP_RESOLUTION = 140
    REFERENCE_SWITCH_TOLERANCE = 141
    SOFT_STOP_FLAG = 149
    RAMP_DIVISOR = 153
    PULSE_DIVISOR = 154
    REFERENCING_MODE = 193
    REFERENCING_SEARCH_SPEED = 194
    REFERENCING_SWITCH_SPEED = 195
    MIXED_DECAY_THRESHOLD = 203
    FREEWHEELING = 204
    STALL_DETECTION_THRESHOLD = 205
    ACTUAL_LOAD_VALUE = 206
    DRIVER_ERROR_FLAGS = 208
    FULLSTEP_THRESHOLD = 211
    POWER_DOWN_DELAY_10ms = 214


class StatusCodes(Enum):
    """
    Enum representing the status codes returned by the TMCL firmware.

    Each status code corresponds to a specific condition or error encountered
    during the execution of a TMCL command.
    """

    SUCCESS = 100
    COMMAND_LOADED = 101
    WRONG_CHECKSUM = 1
    INVALID_COMMAND = 2
    WRONG_TYPE = 3
    INVALID_VALUE = 4
    EEPROM_LOCKED = 5
    COMMAND_NOT_AVAILABLE = 6

    @property
    def description(self):
        descriptions = {
            self.SUCCESS: "Successfully executed, no error",
            self.COMMAND_LOADED: "Command loaded into TMCL program EEPROM",
            self.WRONG_CHECKSUM: "Wrong Checksum",
            self.INVALID_COMMAND: "Invalid command",
            self.WRONG_TYPE: "Wrong type",
            self.INVALID_VALUE: "Invalid value",
            self.EEPROM_LOCKED: "Configuration EEPROM locked",
            self.COMMAND_NOT_AVAILABLE: "Command not available",
        }
        return descriptions[self]

    def __str__(self):
        return self.description


class TMCL:
    @classmethod
    def _encode(
        self,
        cmd: TMCLCommands,
        target_address: int = 1,
        parameter: DefaultParameter = DefaultParameter.default,
        motor_number: int = 0,
        value: int = 0,
    ) -> bytearray:
        """
        Encodes a message according to the TMCL firmware manual.

        Args:
            cmd (TMCLCommands): The TMCL command to be sent.
            target_address (int, optional): The address of the target device. Defaults to 1.
            parameter (int, optional): The command parameter. Defaults to 0.
            motor_number (int, optional): The motor number. Always 0.
            value (int, optional): The command value. Defaults to 0.

        Returns:
            bytearray: The encoded message.
        """
        binary_msg = bytearray(
            [target_address, cmd.value, parameter.value, motor_number]
        )
        binary_msg += value.to_bytes(4, byteorder="big", signed=True)
        checksum = (sum(binary_msg) % 256).to_bytes(1, byteorder="big")
        binary_msg += checksum
        return binary_msg

    @classmethod
    def rotate_right_motor(self, value: int) -> bytearray:
        """
        The motor will be instructed to rotate with a specified velocity in right direction (increasing the position counter).

        Args:
            value (int): The velocity value.

        Returns:
            bytearray: The encoded message.
        """
        return self._encode(TMCLCommands.ROTATE_RIGHT, value=value)

    @classmethod
    def rotate_left_motor(self, value: int) -> bytearray:
        """
        The motor will be instructed to rotate with a specified velocity (opposite direction compared to ROR, decreasing the position counter).

        Args:
            value (int): The velocity value.

        Returns:
            bytearray: The encoded message.
        """
        return self._encode(TMCLCommands.ROTATE_LEFT, value=value)

    @classmethod
    def stop_motor_movement(self) -> bytearray:
        """
        The motor will be instructed to stop with deceleration ramp (soft stop).

        Returns:
            bytearray: The encoded message.
        """
        return self._encode(TMCLCommands.STOP_MOTOR_MOVEMENT)

    @classmethod
    def move_to_position(self, parameter: MotorMovement, value: int) -> bytearray:
        """
        The motor will be instructed to move to a specified relative or absolute position or a
        pre-programmed coordinate. It will use the acceleration/deceleration ramp and the positioning speed
        programmed into the unit. This command is non-blocking – that is, a reply will be sent immediately after
        command interpretation and initialization of the motion controller. Further commands may follow without
        waiting for the motor reaching its end position.

        Args:
            parameter (MotorMovement): The parameter to use. Use MotorMovement.ABSOLUTE for absolute position and MotorMovement.RELATIVE for relative position.
            value (int): The position to move to.

        Returns:
            bytearray: The encoded message.
        """
        return self._encode(
            TMCLCommands.MOVE_TO_POSITION, parameter=parameter, value=value
        )

    @classmethod
    def set_axis_parameter(self, parameter: TMCLPars, value: int) -> bytearray:
        """
        Most of the motion control parameters of the module can be specified. The settings will
        be stored in SRAM and therefore are volatile. That is, information will be lost after power off. Please use
        command store_axis_parameter in order to store any setting permanently.

        Args:
            parameter (TMCLPars): The parameter to set. Refer to TMCLPars enum
            value (int): The value to set the parameter to.

        Returns:
            bytearray: The encoded message.
        """
        return self._encode(
            TMCLCommands.SET_AXIS_PARAMETER, parameter=parameter, value=value
        )

    @classmethod
    def get_axis_parameter(self, parameter: TMCLPars) -> bytearray:
        """
        Gets the specified parameter for the specified motor.

        Args:
            parameter (TMCLPars): The parameter to get. Refer to TMCLPars enum

        Returns:
            bytearray: The encoded message.
        """
        return self._encode(TMCLCommands.GET_AXIS_PARAMETER, parameter=parameter)

    @classmethod
    def store_axis_parameter(self, parameter: TMCLPars) -> bytearray:
        """
        Stores the specified parameter for the specified motor axis in non-volatile memory.

        Args:
            parameter (TMCLPars): The parameter to store. Refer to TMCLPars enum

        Returns:
            bytearray: The encoded message.
        """
        return self._encode(TMCLCommands.STORE_AXIS_PARAMETER, parameter=parameter)

    @classmethod
    def restore_axis_parameter(self, parameter: TMCLPars) -> bytearray:
        """
        Restores the specified parameter for the specified motor axis from non-volatile memory.

        Args:
            parameter (TMCLPars): The parameter to restore. Refer to TMCLPars enum

        Returns:
            bytearray: The encoded message.
        """
        return self._encode(TMCLCommands.RESTORE_AXIS_PARAMETER, parameter=parameter)

    @classmethod
    def decode_reply(self, reply: bytes, spam: bool = False) -> int:
        """
        Decodes the reply from the motor and puts it into a list where each element represents one byte.

        Args:
            reply (bytes): The raw reply from the motor.
            spam (bool, optional): Enables debugging information. Defaults to False. Warning, you will get a lot of info!

        Returns:
            int: decoded value field.
        """
        dec_reply = list(reply)

        hex_value = "".join([f"{byte:02x}" for byte in dec_reply[4:8]])

        int_value = int(hex_value, 16)
        checksum = dec_reply[8]
        status = StatusCodes(dec_reply[2])

        if 1 <= status.value <= 6:
            log.warning(f"Error status received: {status}")
        if spam:
            log.debug(
                "\n----- Reply ----------------------------------------\n"
                f"Value, hex:\t{int_value}, {hex_value}\n"
                f"Cecksum, hex:\t{checksum}, {hex(checksum)}\n"
                f"Reply:\t\t{dec_reply}\n"
                f"Status:\t\t{status}\n"
            )

        return int_value
