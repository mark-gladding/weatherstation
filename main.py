from connection import *
from ntptime import *
import machine
import urequests # handles making and servicing network requests
import time
from timestream import *

# Two modes - normal, has display attached
#           - low power, no display upload only

# Get NTP time and set RTC
# Get the current time and wait until the next 30 second interval
# Main Loop
# while 1
#   Read all sensor values
#   Add to records
#   Attempt to upload (or when 10 or more records present if in low power mode) - clear records if attached
#   If upload unsuccessful and too many records, discard oldest
#   If not low power mode and upload successful, read latest outside values
#   Update display (if attached)
#   Read ntp time and update clock
#   If low power mode - deep sleep until next 30 second interval, else normal sleep

if connect():
    print("LAN connection established")
else:
    print("Could not establish LAN connection")

if set_rtc_from_ntp_time():
    print("time has been set from ntp time server")
rtc = machine.RTC()
print(rtc.datetime())

current_time = f'{time.time()}'

dimensions = [
            {'Name': 'location', 'Value': 'office'}
        ]

temperature = {
    'MeasureName': 'temperature',
    'MeasureValue': '18.2'
}

pressure = {
    'MeasureName': 'pressure',
    'MeasureValue': '13.5'
}

humidity = {
    'MeasureName': 'humidity',
    'MeasureValue': '95.4'
}

records = [temperature, pressure, humidity]
commonAttributes = {
            'Dimensions': dimensions,
            'MeasureValueType': 'DOUBLE',
            'Time': current_time,
            'TimeUnit' : 'SECONDS'
        }
response = WriteRecords( "WeatherDb", "Weather", records, commonAttributes )
if response != None:
    print(response.text)
else:
    print("WriteRecords failed")


disconnect()
