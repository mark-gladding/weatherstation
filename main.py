import connection
import display
import json
import log
import ntptime
import machine
import sensor
import settings
import sys
import time
import timestream

def prepare():
    """ Establish a connection and update the RTC from an NTP server.
        Will retry until successful. 
    """ 
    while(True):
        if connection.connect():
            print('LAN connection established')
            display.status('Connected')
            if ntptime.set_rtc_from_ntp_time():
                rtc = machine.RTC()
                tm = rtc.datetime()
                print(f"UTC Time {tm[3]:02d}:{tm[4]:02d}:{tm[5]:02d} {tm[2]:02d}-{tm[1]:02d}-{tm[0]} has been set from ntp time server")
                return
            else:
                print("time could not be read from ntp time server")
        else:
            print("Could not establish LAN connection")
        connection.disconnect()
        time.sleep(10)

_sync_time_count = 0
def sync_time():
    global _sync_time_count
    if _sync_time_count >= settings.sync_time_period:
        if ntptime.set_rtc_from_ntp_time():
            _sync_time_count = 0
            return
    _sync_time_count += 1


_readings = []

def upload_readings(readings):

    display.status(f'Upload {len(readings)} reads.')
    dimensions = [ {'Name': 'location', 'Value': settings.sensor_location} ]
    commonAttributes = {
            'Dimensions': dimensions,
            'MeasureValueType': 'DOUBLE',
            'TimeUnit' : 'SECONDS'
            }
    response = timestream.write_records(settings.database_name, settings.sensor_readings_table, readings, commonAttributes )    
    if response != None:
        try:
            total = json.loads(response.text)["RecordsIngested"]["Total"]
            display.status(f'Uploaded {total} of {len(readings)}.')

            if total == len(readings):
                readings.clear()
                return
        except KeyError:
            display.error(response.text)
    display.error("Upload failed.")

def upload_last_error():

    last_error = log.read_last_error()
    if not last_error:
        return
     
    display.status(f'Upload log.')
    dimensions = [ {'Name': 'location', 'Value': settings.sensor_location} ]
    commonAttributes = {
            'Dimensions': dimensions,
            'MeasureValueType': 'VARCHAR',
            'TimeUnit' : 'SECONDS'
            }
    response = timestream.write_records( settings.database_name, settings.device_log_table, last_error, commonAttributes )    
    if response != None:
        try:
            total = json.loads(response.text)["RecordsIngested"]["Total"]
            if total == len(last_error):
                display.status(f'Upload successful.')
                log.clear_last_error()
                return
        except KeyError:
            display.error(response.text)
    display.error("Upload failed.")    

def draw_power():
    """ Generate a power draw to keep the attached power bank alive
        by turning the WiFi off, on, connecting for a couple of seconds and turning it back off.
    """

    display.status('Power pulse.')
    connection.disconnect()
    connection.connect()
    time.sleep(2)
    connection.disconnect()

def get_seconds_until_next_reading():
    """ Return the number of seconds until the next sensor reading should be taken. 
    """
    current_seconds = time.gmtime()[5]
    return settings.sensor_read_period_s - (current_seconds % settings.sensor_read_period_s)

def get_seconds_until_next_power_draw():
    """ Return the number of seconds until the next power draw should be performed. 
    """
    if settings.draw_power_period_s == 0:
        return -1

    current_seconds = time.gmtime()[5]
    return settings.draw_power_period_s - (current_seconds % settings.draw_power_period_s)

def sleep_until_next_reading():
    """ Sleep until the next sensor reading is ready to be taken.
        All peripherals remain at full power. 
    """
    seconds_to_sleep = get_seconds_until_next_reading()
    if seconds_to_sleep > 0:
        display.status(f'Sleeping for {seconds_to_sleep}s')
        time.sleep(seconds_to_sleep)

def deep_sleep_until_next_reading():
    """ If a display is not connected, enter a deep sleep until the next sensor reading is ready to be taken.
        Used to conserve power between readings. The LAN will be disconnected.
    """
    while(True):
        secs_until_next_power_draw = get_seconds_until_next_power_draw()
        secs_until_next_reading  = get_seconds_until_next_reading()
        if secs_until_next_power_draw != -1 and secs_until_next_power_draw < secs_until_next_reading:
            display.status(f'Pulse in {secs_until_next_power_draw}s')
            time.sleep(secs_until_next_power_draw)
            draw_power()
        else:
            sleep_until_next_reading()
            break

# Two modes - normal, has display attached
#           - low power, no display upload only

# Get the current time and wait until the next 30 second interval
# Main Loop
# while 1
#   Read all sensor values
#   Add to readings
#   Attempt to upload (or when 10 or more readings present if in low power mode) - clear readings if attached
#   If upload unsuccessful and too many readings, discard oldest
#   If not low power mode and upload successful, read latest outside values
#   Update display (if attached)
#   Read ntp time and update clock
#   If low power mode - deep sleep until next 30 second interval, else normal sleep


try:
  
    display.init_display()
    display.status('Connecting...')
    prepare()
    # Upload the last error message, if logged
    upload_last_error()
    # Do an initial read and display (if attached)
    current_time, tempC, pres_hPa, humRH = sensor.read_sensor()
    display.update_readings(ntptime.get_local_time_string(current_time), tempC, pres_hPa, humRH)
    deep_sleep_until_next_reading()
    while(True):
        current_time, tempC, pres_hPa, humRH = sensor.read_sensor()
        display.update_readings(ntptime.get_local_time_string(current_time), tempC, pres_hPa, humRH)
        readings = sensor.format_readings(current_time, tempC, pres_hPa, humRH)
        _readings.extend(readings)
        if connection.connect():
            sync_time()
            upload_readings(_readings)
        deep_sleep_until_next_reading()

except Exception as e:
    log.write_last_error(e)
    display.error(str(e))
    connection.disconnect()
    if settings.reboot_on_error:
        machine.reset()
    else:
        raise

