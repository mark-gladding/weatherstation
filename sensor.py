# AtmosphericSensor class
#
# Copyright (C) Mark Gladding 2023.
#
# MIT License (see the accompanying license file)
#
# https://github.com/mark-gladding/weatherstation
#

from PiicoDev_BME280 import PiicoDev_BME280
import time

class AtmosphericSensor:
    """Class providing functions to read the PiicoDev_BME280 atmospheric sensor.
    """    
    def __init__(self):
        self._sensor = None

    def read_sensor(self):
        if not self._sensor:
            self._sensor = PiicoDev_BME280() # initialize the sensor

        current_time = f'{time.time()}'
        tempC, presPa, humRH = self._sensor.values() # read all data from the sensor
        pres_hPa = presPa / 100 # convert air pressure Pascals -> hPa (or mbar, if you prefer)

        return current_time, tempC, pres_hPa, humRH


