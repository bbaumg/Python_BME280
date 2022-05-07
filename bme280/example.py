import logging
from bme280 import bme280


# Setup logging
#logLevel = logging.CRITICAL
#logLevel = logging.ERROR
#logLevel = logging.WARNING
#logLevel = logging.INFO
logLevel = logging.DEBUG
logFormat = '%(asctime)s - %(module)s %(funcName)s - %(levelname)s - %(message)s'
logDateFormat = '%Y-%m-%d %H:%M:%S'
logFilename = 'garagepi.log'
#logHandlers = [logging.FileHandler(logFilename)]
logHandlers = [logging.StreamHandler()]
#logHandlers = [logging.FileHandler(logFilename), logging.StreamHandler()]
logging.basicConfig(level = logLevel, format = logFormat, datefmt = logDateFormat, handlers = logHandlers)
logger = logging.getLogger(__name__)

sensor = bme280()
print(sensor.readBME280ID())
print(sensor.readBME280Data())
