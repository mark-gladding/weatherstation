# Application to monitor indoor and outdoor temperatures
#
# Copyright (C) Mark Gladding 2023.
#
# MIT License (see the accompanying license file)
#
# https://github.com/mark-gladding/weatherstation
#

from connection import Connection
import display
import log
from power import Power
from ntptime import NtpTime
import machine
from sensor import AtmosphericSensor
import secrets
import settings
from startup import Startup
import timestream

if __name__ == "__main__":
    try:
        connection = Connection(ssid=secrets.wifi_ssid, password=secrets.wifi_password, perform_complete_poweroff=settings.deep_sleep)
        power = Power(connection=connection, sensor_read_period_s=settings.sensor_read_period_s, draw_power_period_s=settings.draw_power_period_s, deep_sleep=settings.deep_sleep)
        sensor = AtmosphericSensor()
        ntptime = NtpTime(ntp_time_server=settings.ntp_time_server, timezone_api_key=secrets.timezone_api_key, sync_time_period=settings.sync_time_period, timezone_location=settings.timezone_location)
        startup = Startup(connection=connection, ntptime=ntptime)

        startup.startup()

        remote_tempC = 0
        current_time, tempC, pres_hPa, humRH = sensor.read_sensor()
        if settings.remote_sensor_location:
            remote_tempC = timestream.read_remote_sensor(remote_tempC)
        display.update_readings(ntptime.get_local_time_string(current_time), settings.sensor_location, tempC, settings.remote_sensor_location, remote_tempC)
        power.wait_until_next_reading()

        readings_to_upload = []
        while(True):
            current_time, tempC, pres_hPa, humRH = sensor.read_sensor()
            display.update_readings(ntptime.get_local_time_string(current_time), settings.sensor_location, tempC, settings.remote_sensor_location, remote_tempC)
            readings = timestream.format_readings(current_time, tempC, pres_hPa, humRH)
            readings_to_upload.extend(readings)
            if connection.connect():
                ntptime.sync_time()
                timestream.upload_readings(readings_to_upload)
                if settings.remote_sensor_location:
                    remote_tempC = timestream.read_remote_sensor(remote_tempC)
            power.wait_until_next_reading()

    except Exception as e:
        log.write_last_error(e)
        display.show_status()
        display.error(str(e))
        connection.disconnect()
        if settings.reboot_on_error:
            machine.reset()
        else:
            raise

