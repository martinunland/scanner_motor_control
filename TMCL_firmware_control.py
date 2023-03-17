from enum import Enum

class TMCLCommands(Enum):
    ROTATE_RIGHT = 1
    ROTATE_LEFT = 2
    STOP_MOTOR_MOVEMENT = 3
    MOVE_TO_POSITION = 4
    SET_AXIS_PARAMETER = 5
    GET_AXIS_PARAMETER = 6
    STORE_AXIS_PARAMETER = 7
    RESTORE_AXIS_PARAMETER = 8

class AxisParameters(Enum):
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

class TMCL:
    @classmethod
    def _encode(self, cmd: TMCLCommands, target_address: int = 1, parameter: int = 0, motor_number: int = 0, value: int = 0) -> bytearray:
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
        binary_msg = bytearray([target_address, cmd.value, parameter, motor_number])
        binary_msg += value.to_bytes(4, byteorder="big")
        checksum = sum(binary_msg).to_bytes(1, byteorder="big")
        binary_msg += checksum
        return binary_msg
    
    @classmethod
    def rotate_right_motor(self, value: int) -> bytearray:
        """
        The motor will be instructed to rotate with a specified velocity in right direction (increasing the position counter). 

        Args:
            motor_number (int): The motor number.
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
            motor_number (int): The motor number.
            value (int): The velocity value.

        Returns:
            bytearray: The encoded message.
        """
        return self._encode(TMCLCommands.ROTATE_LEFT, value=value)
    @classmethod
    def stop_motor_movement(self) -> bytearray:
        """
        The motor will be instructed to stop with deceleration ramp (soft stop).

        Args:
            motor_number (int): The motor number.

        Returns:
            bytearray: The encoded message.
        """
        return self._encode(TMCLCommands.STOP_MOTOR_MOVEMENT)
    @classmethod
    def move_to_position(self, parameter: int, value: int) -> bytearray:
        """
        The motor will be instructed to move to a specified relative or absolute position or a
        pre-programmed coordinate. It will use the acceleration/deceleration ramp and the positioning speed
        programmed into the unit. This command is non-blocking – that is, a reply will be sent immediately after
        command interpretation and initialization of the motion controller. Further commands may follow without
        waiting for the motor reaching its end position.

        Args:
            parameter (int): The parameter to use. Use 0 for absolute position and 1 for relative position.
            motor_number (int): The motor number.
            value (int): The position to move to.

        Returns:
            bytearray: The encoded message.
        """
        return self._encode(TMCLCommands.MOVE_TO_POSITION, parameter=parameter, value=value)

    @classmethod
    def set_axis_parameter(self, parameter: int, value: int) -> bytearray:
        """
        Most of the motion control parameters of the module can be specified. The settings will
        be stored in SRAM and therefore are volatile. That is, information will be lost after power off. Please use
        command store_axis_parameter in order to store any setting permanently.

        Args:
            parameter (int): The parameter to set. Refer to AxisParameters.
            motor_number (int): The motor number.
            value (int): The value to set the parameter to.

        Returns:
            bytearray: The encoded message.
        """
        return self._encode(TMCLCommands.SET_AXIS_PARAMETER, parameter=parameter, value=value)
    @classmethod
    def get_axis_parameter(self, parameter: int) -> bytearray:
        """
        Gets the specified parameter for the specified motor.

        Args:
            parameter (int): The parameter to get. Refer to AxisParameters
            motor_number (int): The motor number.

        Returns:
            bytearray: The encoded message.
        """
        return self._encode(TMCLCommands.GET_AXIS_PARAMETER, parameter=parameter)
    @classmethod
    def store_axis_parameter(self, parameter: int) -> bytearray:
        """
        Stores the specified parameter for the specified motor axis in non-volatile memory.

        Args:
            parameter (int): The parameter to store. Refer to AxisParameters.
            motor_number (int): The motor number.

        Returns:
            bytearray: The encoded message.
        """
        return self._encode(TMCLCommands.STORE_AXIS_PARAMETER, parameter=parameter)
    @classmethod
    def restore_axis_parameter(self, parameter: int) -> bytearray:
        """
        Restores the specified parameter for the specified motor axis from non-volatile memory.

        Args:
            parameter (int): The parameter to restore. Refer to AxisParameters.
            motor_number (int): The motor number.

        Returns:
            bytearray: The encoded message.
        """
        return self._encode(TMCLCommands.RESTORE_AXIS_PARAMETER, parameter=parameter)


