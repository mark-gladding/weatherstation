# Application to monitor indoor and outdoor temperatures
#
# Copyright (C) Mark Gladding 2023.
#
# MIT License (see the accompanying license file)
#
# https://github.com/mark-gladding/weatherstation
#

from connection import Connection
from display import Display
from log import Log
from power import Power
from ntptime import NtpTime
import machine
from sensor import AtmosphericSensor
import secrets
import settings
from startup import Startup
from timestream import Timestream

if __name__ == "__main__":
    try:
        log = Log()
        display = Display(display_cycle_period_ms=settings.display_cycle_period_ms)
        connection = Connection(ssid=secrets.wifi_ssid, 
                                password=secrets.wifi_password, 
                                perform_complete_poweroff=settings.deep_sleep)
        power = Power(display=display, 
                      connection=connection, 
                      sensor_read_period_s=settings.sensor_read_period_s, 
                      draw_power_period_s=settings.draw_power_period_s)
        sensor = AtmosphericSensor()
        ntptime = NtpTime(ntp_time_server=settings.ntp_time_server, 
                          timezone_api_key=secrets.timezone_api_key, 
                          sync_time_period_m=settings.sync_time_period_m, 
                          timezone_location=settings.timezone_location,
                          day_mode_start_hour=settings.day_mode_start_hour,
                          night_mode_start_hour=settings.night_mode_start_hour)
        timestream = Timestream(display=display, 
                                aws_access_key=secrets.aws_access_key, 
                                aws_secret_access_key=secrets.aws_secret_access_key, 
                                aws_region=settings.aws_region,
                                database_name=settings.database_name, 
                                sensor_readings_table=settings.sensor_readings_table,
                                sensor_location=settings.sensor_location, 
                                remote_sensor_location=settings.remote_sensor_location, 
                                device_log_table=settings.device_log_table)
        startup = Startup(display=display, 
                          connection=connection, 
                          ntptime=ntptime, 
                          timestream=timestream, 
                          log=log)

        startup.startup()

        remote_tempC = 0
        current_time, tempC, pres_hPa, humRH = sensor.read_sensor()
        display.update_readings(ntptime.get_local_time_string(current_time), settings.sensor_location, tempC, None, 0)
        remote_tempC = timestream.read_remote_sensor(remote_tempC)
        display.update_readings(ntptime.get_local_time_string(current_time), settings.sensor_location, tempC, settings.remote_sensor_location, remote_tempC)
        power.wait_until_next_reading(False)

        readings_to_upload = []
        upload_countdown = settings.day_upload_period if ntptime.is_day() else settings.night_upload_period
        print(f'upload_countdown: {upload_countdown}')
        while(True):
            current_time, tempC, pres_hPa, humRH = sensor.read_sensor()
            display.update_readings(ntptime.get_local_time_string(current_time), settings.sensor_location, tempC, settings.remote_sensor_location, remote_tempC)
            readings = timestream.format_readings(current_time, tempC, pres_hPa, humRH)
            readings_to_upload.extend(readings)
            upload_countdown -= 1
            if upload_countdown <= 0 and connection.connect():
                ntptime.sync_time()
                timestream.upload_readings(readings_to_upload)
                remote_tempC = timestream.read_remote_sensor(remote_tempC)
                upload_countdown = settings.day_upload_period if ntptime.is_day() else settings.night_upload_period
            power.wait_until_next_reading(settings.deep_sleep or not ntptime.is_day())

    except Exception as e:
        log.write_last_error(e)
        display.show_status()
        display.error(str(e))
        connection.disconnect()
        if settings.reboot_on_error:
            machine.reset()
        else:
            raise

