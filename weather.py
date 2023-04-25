import sys
import time

from timestream import *

from aws_auth import *

def _current_seconds_time():
    return str(int(round(time.time())))

# payload = "{\r\n   \"MaxRows\": 500,\r\n   \"QueryString\": \"SELECT truck_id from sampleDB.IoTMulti\"\r\n}"
# response = QueryRequest( payload )
# if response and response.ok:
#     print(response.text)
# else:
#     print("Query failed")
#     sys.exit(-1)

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

current_time = _current_seconds_time()

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
    sys.exit(-1)