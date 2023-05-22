import connection
import display
import machine
import settings
import time

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
        Used to conserve power between readings. The WiFi will be disconnected.
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
