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

def draw_power():
    """ Generate a power draw to keep the attached power bank alive
        by turning the WiFi off, on, connecting for a second and turning it back off.
    """

    display.status('Power pulse.')
    connection.disconnect()
    connection.connect()
    time.sleep(1)
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

def wait_until_next_reading():
    if settings.deep_sleep:
        deep_sleep_until_next_reading()
    else:
        keep_awake_until_next_reading()

def sleep_until_next_reading():
    """ Sleep until the next sensor reading is ready to be taken.
        All peripherals remain at full power. 
    """
    seconds_to_sleep = get_seconds_until_next_reading()
    if seconds_to_sleep > 0:
        display.status(f'Sleeping for {seconds_to_sleep}s')
        time.sleep(seconds_to_sleep)

def keep_awake_until_next_reading():
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

def deep_sleep_until_next_reading():
    """ Sleep in dormant mode until the next sensor reading is ready to be taken.
        All peripherals are shut down. 
    """
    seconds_to_sleep = get_seconds_until_next_reading()
    if seconds_to_sleep > 0:
        display.status(f'Deep sleeping for {seconds_to_sleep}s')
        connection.disconnect()
        machine.lightsleep(seconds_to_sleep * 1000)

try:
  
    display.init_display()
    display.status('Connecting...')
    prepare()
    # Upload the last error message, if logged
    timestream.upload_last_error()
    # Do an initial read and display (if attached)
    display.hide_status()
    remote_tempC = 0
    current_time, tempC, pres_hPa, humRH = sensor.read_sensor()
    if settings.remote_sensor_location:
        remote_tempC = timestream.read_remote_sensor(settings.database_name, settings.sensor_readings_table, settings.remote_sensor_location, remote_tempC)
    display.update_readings(ntptime.get_local_time_string(current_time), settings.sensor_location, tempC, settings.remote_sensor_location, remote_tempC)
    wait_until_next_reading()
    while(True):
        current_time, tempC, pres_hPa, humRH = sensor.read_sensor()
        display.update_readings(ntptime.get_local_time_string(current_time), settings.sensor_location, tempC, settings.remote_sensor_location, remote_tempC)
        readings = sensor.format_readings(current_time, tempC, pres_hPa, humRH)
        _readings.extend(readings)
        if connection.connect():
            sync_time()
            timestream.upload_readings(_readings)
            if settings.remote_sensor_location:
                remote_tempC = timestream.read_remote_sensor(settings.database_name, settings.sensor_readings_table, settings.remote_sensor_location, remote_tempC)
        wait_until_next_reading()

except Exception as e:
    log.write_last_error(e)
    display.show_status()
    display.error(str(e))
    connection.disconnect()
    if settings.reboot_on_error:
        machine.reset()
    else:
        raise

