# Author:  Barrett Baumgartner
# 
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#  Official datasheet available from :
#  https://www.bosch-sensortec.com/bst/products/all_products/bme280


import smbus
import time
import logging
import os
import sys
from ctypes import c_short
from ctypes import c_byte
from ctypes import c_ubyte

REG_ADDR = 0x76     # Default device I2C address
REG_CHIPID = 0xD0   # Default chip ID

REG_DATA = 0xF7
REG_CONTROL = 0xF4
REG_CONFIG  = 0xF5

REG_CONTROL_HUM = 0xF2
REG_HUM_MSB = 0xFD
REG_HUM_LSB = 0xFE

# Oversample setting - page 22 - 27
OVERSAMPLE_TEMP = 2
OVERSAMPLE_PRES = 2
OVERSAMPLE_HUM = 2
MODE = 1


class bme280(object):
  def __init__(self, address=REG_ADDR, chipID=REG_CHIPID):
    logging.info("Instantiating a bme280 object")
    if(os.path.exists("/dev/i2c-1") or os.path.exists("/dev/i2c/1")):
      logging.info("i2c is enabled... OK to proceed")
    else:
      logging.critical("ERROR i2c is NOT enabled")
      sys.exit("ERROR:  i2c is NOT enabled.  Use 'sudo raspi-config' to enable it")
    self.bus = smbus.SMBus(1)
    self.address = address
    self.chipID = chipID
    logging.debug("Address = " + str(hex(self.address)) 
      + ", ChipID = " + str(hex(self.chipID)))

    # Calibrate the device

  def getShort(self, data, index):
    # return two bytes from data as a signed 16-bit value
    return c_short((data[index+1] << 8) + data[index]).value

  def getUShort(self, data, index):
    # return two bytes from data as an unsigned 16-bit value
    return (data[index+1] << 8) + data[index]

  def getChar(self, data,index):
    # return one byte from data as a signed char
    result = data[index]
    if result > 127:
      result -= 256
    return result

  def getUChar(self, data,index):
    # return one byte from data as an unsigned char
    result =  data[index] & 0xFF
    return result

  def readBME280ID(self):
    logging.info("Reading the BME280s chip version")
    deviceData = self.bus.read_i2c_block_data(self.address, self.chipID, 2)
    deviceInfo = dict()
    deviceInfo['ChipID'] = deviceData[0]
    deviceInfo['ChipVeresion'] = deviceData[1]
    logging.info("Chip ID = " + str(deviceInfo['ChipID']) + ", Chip Version = " + str(deviceInfo['ChipVeresion']))
    return deviceInfo

  def readBME280Data(self):
    logging.info("Starting...  Read BME280's data")
    self.bus.write_byte_data(self.address, REG_CONTROL_HUM, OVERSAMPLE_HUM)

    control = OVERSAMPLE_TEMP<<5 | OVERSAMPLE_PRES<<2 | MODE
    self.bus.write_byte_data(self.address, REG_CONTROL, control)

    # Read blocks of calibration data from EEPROM
    # See Page 22 data sheet
    cal1 = self.bus.read_i2c_block_data(self.address, 0x88, 24)
    cal2 = self.bus.read_i2c_block_data(self.address, 0xA1, 1)
    cal3 = self.bus.read_i2c_block_data(self.address, 0xE1, 7)

    # Convert byte data to word values
    dig_T1 = self.getUShort(cal1, 0)
    dig_T2 = self.getShort(cal1, 2)
    dig_T3 = self.getShort(cal1, 4)

    dig_P1 = self.getUShort(cal1, 6)
    dig_P2 = self.getShort(cal1, 8)
    dig_P3 = self.getShort(cal1, 10)
    dig_P4 = self.getShort(cal1, 12)
    dig_P5 = self.getShort(cal1, 14)
    dig_P6 = self.getShort(cal1, 16)
    dig_P7 = self.getShort(cal1, 18)
    dig_P8 = self.getShort(cal1, 20)
    dig_P9 = self.getShort(cal1, 22)

    dig_H1 = self.getUChar(cal2, 0)
    dig_H2 = self.getShort(cal3, 0)
    dig_H3 = self.getUChar(cal3, 2)
    dig_H4 = ((self.getChar(cal3, 3) << 24) >> 20) | (self.getChar(cal3, 4) & 0x0F)
    dig_H5 = ((self.getChar(cal3, 5) << 24) >> 20) | (self.getUChar(cal3, 4) >> 4 & 0x0F)
    dig_H6 = self.getChar(cal3, 6)

    # Wait in ms (Datasheet Appendix B: Measurement time and current calculation)
    wait_time = 1.25 + (2.3 * OVERSAMPLE_TEMP) + ((2.3 * OVERSAMPLE_PRES) + 0.575) + ((2.3 * OVERSAMPLE_HUM)+0.575)
    time.sleep(wait_time/1000)  # Wait the required time  

    # Read temperature/pressure/humidity
    data = self.bus.read_i2c_block_data(self.address, REG_DATA, 8)
    pres_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
    temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
    hum_raw = (data[6] << 8) | data[7]
    logging.debug("Raw Data:  Pressure = " + str(pres_raw) + 
      ", Temp = " + str(temp_raw) + 
      ", Humid = " + str(hum_raw))
    #Refine temperature
    var1 = ((((temp_raw>>3)-(dig_T1<<1)))*(dig_T2)) >> 11
    var2 = (((((temp_raw>>4) - (dig_T1)) * ((temp_raw>>4) - (dig_T1))) >> 12) * (dig_T3)) >> 14
    t_fine = var1+var2
    temperature = float(((t_fine * 5) + 128) >> 8);

    # Refine pressure and adjust for temperature
    var1 = t_fine / 2.0 - 64000.0
    var2 = var1 * var1 * dig_P6 / 32768.0
    var2 = var2 + var1 * dig_P5 * 2.0
    var2 = var2 / 4.0 + dig_P4 * 65536.0
    var1 = (dig_P3 * var1 * var1 / 524288.0 + dig_P2 * var1) / 524288.0
    var1 = (1.0 + var1 / 32768.0) * dig_P1
    if var1 == 0:
      pressure=0
    else:
      pressure = 1048576.0 - pres_raw
      pressure = ((pressure - var2 / 4096.0) * 6250.0) / var1
      var1 = dig_P9 * pressure * pressure / 2147483648.0
      var2 = pressure * dig_P8 / 32768.0
      pressure = pressure + (var1 + var2 + dig_P7) / 16.0

    # Refine humidity
    humidity = t_fine - 76800.0
    humidity = (hum_raw - (dig_H4 * 64.0 + dig_H5 / 16384.0 * humidity)) * (dig_H2 / 65536.0 * (1.0 + dig_H6 / 67108864.0 * humidity * (1.0 + dig_H3 / 67108864.0 * humidity)))
    humidity = humidity * (1.0 - dig_H1 * humidity / 524288.0)
    if humidity > 100:
      humidity = 100
    elif humidity < 0:
      humidity = 0

    results = dict()
    results['TempC'] = temperature/100.0
    results['TempF'] = round(results["TempC"]*1.8+32, 1)
    results['Pressure'] = round(pressure/100.0, 1)
    results['Humidity'] = round(humidity, 1)
    logging.info("Readings:  Temp C = " + str(results['TempC']) + 
      ", Temp F = " + str(results['TempF']) + 
      ", Pressure = " + str(results['Pressure']) + 
      ", Humid = " + str(results['Humidity']))
    logging.debug(results)
    return results
