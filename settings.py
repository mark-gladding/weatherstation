# Module responsible for providing configurable settings for this application.
#
# Copyright (C) Mark Gladding 2023.
#
# MIT License (see the accompanying license file)
#
# https://github.com/mark-gladding/weatherstation
#

import json
import os
import sys

sensor_read_period_s = 60     # Read the sensors every 60 seconds

# Time related settings. Update for your geographic location.
ntp_time_server = 'au.pool.ntp.org'
sync_time_period = 30 * 60 / sensor_read_period_s   # Sync the RTC with the ntp time server every 30 minutes

timezone_location = '-37.9707183%2C144.392352'  # Australia / Melbourne

# AWS Timestream Settings
aws_region = 'ap-southeast-2'
database_name = 'WeatherDb'
sensor_readings_table = 'Weather'
device_log_table = 'DeviceLog'


display_cycle_period_ms = 5000  # Time to display a reading on the display before moving to the next reading (e.g remote sensor temperature).

reboot_on_error = True      # If true, reboot the Pico on error. If false, just raise the exception (useful during development)


# Load the sensor-specific settings from a 'settings_[location].json' file.
files = os.listdir()
settings_file =  [file for file in files if file.startswith('settings_')]
if len(settings_file) == 0:
    sys.exit('Cannot find a location specific settings file.')
settings_file = settings_file[0]

try:
    with open(settings_file) as f:
        location_settings = json.load(f)
        # Merge the settings loaded from the json file into this module.
        sys.modules[__name__].__dict__.update(location_settings)

except OSError:
    sys.exit(f'Cannot load location specific settings file {settings_file}.')



