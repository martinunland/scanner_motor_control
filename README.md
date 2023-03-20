# 3D scanner control library

This repository contains a Python library to control TMCL-based stepper motors, specifically designed for use with a 3D scanner system using three TRINAMIC PDx-110-42 motors. The library consists of three main files:

1. `tmcl_interface.py`: Provides an interface to the TMCL protocol for communication with stepper motor controllers.
2. `motor_controller.py`: Defines the Motor class that represents a single motor and its functions, utilizing the TMCL interface.
3. `scanner_motor_manager.py`: Manages multiple motor controllers by implementing the ScannerControl class.

## Installation
You can install the library using pip:

```bash
pip install git+https://github.com/martinunland/scanner_motor_control.git
```
Or download the wheel in repositories and pip:
```bash
pip install scan_motion_control-0.1.0-py3-none-any.whl
```

## Dependencies

This library requires Python 3.6+ and the `pyserial` package for serial communication with the motor controllers.

You can install `pyserial` using pip:

```bash
pip install pyserial
```

## Usage

To use the library, you need to first create an instance of the ScannerControl class, which will manage the motors. You can then connect the motors, set their speed and acceleration, find reference positions, activate/deactivate stall guards, and perform various motor movements.

Here's a simple example:

```python
from scanner_motor_manager import ScannerControl

# Create an instance of the ScannerControl class
scanner = ScannerControl()

# Connect the motors to their respective serial ports
ports = ['/dev/ttyS0', '/dev/ttyS1', '/dev/ttyS2']
scanner.connect(ports)
scanner.configure_motors()

# Find the reference position (0,0,0) of the system, moving all motors as far left as possible
scanner.find_reference_position()

# Move each motor to an absolute position in millimeters
scanner.move_to_absolute_position_in_mm([10, 20, 30])

# Move each motor -5mm relative to the current position
scanner.move_relative_distance_in_mm([-5, -5, -5])

# Disconnect the motors
scanner.disconnect()
```

You can also work in a with block as in this example:
```python
with ScannerControl() as scanner:
    scanner.connect(['/dev/ttyS0', '/dev/ttyS1', '/dev/ttyS2'])
    scanner.find_reference_position()
    scanner.configure_motors()
    scanner.move_relative_distance_in_mm([-15, -15, -15])
    print(scanner.get_current_position())
```
In this case, the motors are automatically disconnected if an exception occurs.

If you request a position outside the available volume, an exception will be risen. You can check the position as follows:
```python
valid = scanner.check_position_in_mm_allowed([-15, -15, -15], relative = True)
```
