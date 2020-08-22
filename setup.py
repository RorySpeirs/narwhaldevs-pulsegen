
from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='ndpulsegen',
    version='0.1.0',
    description='A package to interface with the Narwhal Devices Pulse Generator',
    long_description=readme,
    author='Rory Speirs',
    author_email='rory@narwhaldevices.com',
    url='https://github.com/roryspeirs/narwhaldevs-pulsegen',
    license=license,
    packages=find_packages(exclude=('tests', 'docs', 'pulse_dev'))
)

