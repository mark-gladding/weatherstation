# Power class
#
# Copyright (C) Mark Gladding 2023.
#
# MIT License (see the accompanying license file)
#
# https://github.com/mark-gladding/weatherstation
#

import machine
import time

class Power:
    """Class providing functions to sleep between readings.

     This allows power to be conserved when operating on battery.
    """    
    def __init__(self, display, connection, sensor_read_period_s : int, draw_power_period_s : int, deep_sleep : bool):
        """Constructor

        Args:
            display (Display): The display to output messages to.
            connection (Connection): The connection being used.
            sensor_read_period_s (int): Period in seconds between sensor reads.
            draw_power_period_s (int): Period in seconds between power draws (0=disable power draws) on a power bank.
            deep_sleep (bool): True to perform a deep sleep between reads, false to keep the unit away between reads.
        """        
        self._display = display
        self._connection = connection
        self._sensor_read_period_s = sensor_read_period_s
        self._draw_power_period_s = draw_power_period_s
        self._deep_sleep = deep_sleep

    def draw_power(self):
        """ Generate a power draw to keep the attached power bank alive
            by turning the WiFi off, on, connecting for a second and turning it back off.
        """

        self._display.status('Power pulse.')
        self._connection.disconnect()
        self._connection.connect()
        time.sleep(1)
        self._connection.disconnect()

    def get_seconds_until_next_reading(self):
        """ Return the number of seconds until the next sensor reading should be taken. 
        """
        current_seconds = time.gmtime()[5]
        return self._sensor_read_period_s - (current_seconds % self._sensor_read_period_s)

    def get_seconds_until_next_power_draw(self):
        """ Return the number of seconds until the next power draw should be performed. 
        """
        if self._draw_power_period_s == 0:
            return -1

        current_seconds = time.gmtime()[5]
        return self._draw_power_period_s - (current_seconds % self._draw_power_period_s)

    def wait_until_next_reading(self):
        """Either perform a deep sleep to conserve power when running from a battery or
        keep the unit awake until the next reading.
        """        
        if self._deep_sleep:
            self.deep_sleep_until_next_reading()
        else:
            self.keep_awake_until_next_reading()

    def sleep_until_next_reading(self):
        """ Sleep until the next sensor reading is ready to be taken.
            All peripherals remain at full power. 
        """
        seconds_to_sleep = self.get_seconds_until_next_reading()
        if seconds_to_sleep > 0:
            self._display.status(f'Sleeping for {seconds_to_sleep}s')
            time.sleep(seconds_to_sleep)

    def keep_awake_until_next_reading(self):
        """ If a power bank is being used, periodically draw some power to ensure the power bank doesn't switch off,
        otherwise just perform a standard sleep (at full power).
        """
        while(True):
            secs_until_next_power_draw = self.get_seconds_until_next_power_draw()
            secs_until_next_reading  = self.get_seconds_until_next_reading()
            if secs_until_next_power_draw != -1 and secs_until_next_power_draw < secs_until_next_reading:
                self._display.status(f'Pulse in {secs_until_next_power_draw}s')
                time.sleep(secs_until_next_power_draw)
                self.draw_power()
            else:
                self.sleep_until_next_reading()
                break

    def deep_sleep_until_next_reading(self):
        """ Sleep in dormant mode until the next sensor reading is ready to be taken.
            All peripherals are shut down. 
        """
        seconds_to_sleep = self.get_seconds_until_next_reading()
        if seconds_to_sleep > 0:
            self._display.status(f'Deep sleeping for {seconds_to_sleep}s')
            self._connection.disconnect()
            machine.lightsleep(seconds_to_sleep * 1000)
