from connection import *
from ntptime import *
import machine
import settings
import urequests # handles making and servicing network requests
import time
from timestream import *

def prepare():
    while(True):
        if connect():
            print("LAN connection established")
            if set_rtc_from_ntp_time():
                print("time has been set from ntp time server")
                rtc = machine.RTC()
                print(rtc.datetime())
                return
            else:
                print("time could not be read from ntp time server")
        else:
            print("Could not establish LAN connection")
        disconnect()
        time.sleep(settings.sensor_read_period_s)

_sync_time_count = 0
def sync_time():
    global _sync_time_count
    if _sync_time_count >= settings.sync_time_period:
        if set_rtc_from_ntp_time():
            _sync_time_count = 0
            return
    _sync_time_count += 1


def read_sensor():

    current_time = f'{time.time()}'

    temperature = {
        'MeasureName': 'temperature',
        'MeasureValue': '18.2',
        'Time': current_time
    }

    pressure = {
        'MeasureName': 'pressure',
        'MeasureValue': '13.5',
        'Time': current_time
    }

    humidity = {
        'MeasureName': 'humidity',
        'MeasureValue': '95.4',
        'Time': current_time
    }

    return [temperature, pressure, humidity]

_records = []

def upload_records(records):

    dimensions = [ {'Name': 'location', 'Value': settings.sensor_location} ]
    commonAttributes = {
            'Dimensions': dimensions,
            'MeasureValueType': 'DOUBLE',
            'TimeUnit' : 'SECONDS'        
            }
    response = WriteRecords( "WeatherDb", "Weather", records, commonAttributes )    
    if response != None:
        try:
            total = json.loads(response.text)["RecordsIngested"]["Total"]
            print(f'Uploaded {total} records of {len(records)}.')
            if total == len(records):
                records.clear()
                return
        except AttributeError:
            pass
    print("Upload failed.")

def get_seconds_until_next_reading():
    current_seconds = time.gmtime()[5]
    return 30 - (current_seconds % 30)

def sleep_until_next_reading():
    seconds_to_sleep = get_seconds_until_next_reading()
    if seconds_to_sleep > 0:
        print(f'Sleeping for {seconds_to_sleep} seconds...')
        time.sleep(seconds_to_sleep)

def deep_sleep_until_next_reading():
    sleep_until_next_reading()

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


prepare()
sleep_until_next_reading()
_loop = 2
while(_loop > 0):
    records = read_sensor()
    _records.extend(records)
    if connect():
        sync_time()
        upload_records(_records)
    if settings.has_display:
        sleep_until_next_reading()
    else:
        disconnect()
        deep_sleep_until_next_reading()
    _loop -= 1

disconnect()


