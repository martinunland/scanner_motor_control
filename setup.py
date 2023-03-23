from setuptools import setup, find_packages

setup(
    name='scanner_motor_control',  # Replace with your desired library name
    version='0.2.0',
    description='A library for controlling the 3D scanner',
    author='Martin Unland | Raffaela Busse',  
    author_email='martin.e@unland.eu',  
    url='https://github.com/martinunland/scanner_motor_control',  
    packages=find_packages(),
    install_requires=[
        # List the packages required for your library here, e.g.
         'pyserial',
    ],
    python_requires='>=3.6',
)
