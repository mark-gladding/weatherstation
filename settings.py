import json
import os
import sys

aws_region = 'ap-southeast-2'
ntp_time_server = 'au.pool.ntp.org'

database_name = 'WeatherDb'
sensor_readings_table = 'Weather'
device_log_table = 'DeviceLog'

sensor_read_period_s = 60     # Read the sensors every 60 seconds

display_cycle_period_ms = 5000  # Time to display a reading on the display before moving to the next reading (e.g remote sensor temperature).

sync_time_period = 30 * 60 / sensor_read_period_s   # Sync the RTC with the ntp time server every 30 minutes

reboot_on_error = True      # If true, reboot the Pico on error. If false, just raise the exception (useful during development)

timezone_location = '-37.9707183%2C144.392352'  # Australia / Melbourne

# Load the location specific settings from a 'settings_[location].json' file.
files = os.listdir()
settings_file =  [file for file in files if file.startswith('settings_')]
if len(settings_file) == 0:
    sys.exit('Cannot find a location specific settings file.')
settings_file = settings_file[0]

try:
    with open(settings_file) as f:
        location_settings = json.load(f)
        sensor_location = location_settings['sensor_location']
        remote_sensor_location = location_settings['remote_sensor_location']
        draw_power_period_s = location_settings['draw_power_period_s']
        deep_sleep = location_settings['deep_sleep']

except OSError:
    sys.exit(f'Cannot load location specific settings file {settings_file}.')



