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
import ntptime
import machine
import sensor
import secrets
import settings
import startup
import timestream

if __name__ == "__main__":
    try:
        connection = Connection(ssid=secrets.wifi_ssid, password=secrets.wifi_password, perform_complete_poweroff=settings.deep_sleep)
        power = Power(connection=connection, sensor_read_period_s=settings.sensor_read_period_s, draw_power_period_s=settings.draw_power_period_s, deep_sleep=settings.deep_sleep)
        startup.startup(connection)

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
            readings = sensor.format_readings(current_time, tempC, pres_hPa, humRH)
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

