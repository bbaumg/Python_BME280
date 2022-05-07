import setuptools 
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
	name='bme280',
	version='1.0.0',
	description='Driver for sending Thingspeak data',
	url='https://github.com/bbaumg/Python_BME280',
	author='bbaumg',
	license='MIT',
	packages=['bme280'],
	install_requires=['smbus']
)
