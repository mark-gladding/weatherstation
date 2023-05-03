from PiicoDev_BME280 import PiicoDev_BME280
import time

_sensor = None

def read_sensor():
    global _sensor

    if not _sensor:
        _sensor = PiicoDev_BME280() # initialize the sensor

    current_time = f'{time.time()}'
    tempC, presPa, humRH = _sensor.values() # read all data from the sensor
    pres_hPa = presPa / 100 # convert air pressure Pascals -> hPa (or mbar, if you prefer)

    return current_time, tempC, pres_hPa, humRH

def format_readings(current_time, tempC, pres_hPa, humRH):

    temperature = {
        'MeasureName': 'temperature',
        'MeasureValue': f'{tempC}',
        'Time': current_time
    }

    pressure = {
        'MeasureName': 'pressure',
        'MeasureValue': f'{pres_hPa}',
        'Time': current_time
    }

    humidity = {
        'MeasureName': 'humidity',
        'MeasureValue': f'{humRH}',
        'Time': current_time
    }

    return [temperature, pressure, humidity]
