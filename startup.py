# Startup class
#
# Copyright (C) Mark Gladding 2023.
#
# MIT License (see the accompanying license file)
#
# https://github.com/mark-gladding/weatherstation
#
import machine
import time

class Startup:
    """
    """    
    def __init__(self, display, connection, ntptime, timestream, log):
        self._display = display
        self._connection = connection
        self._ntptime = ntptime
        self._timestream = timestream
        self._log = log

    def startup(self):
        self._display.init()
        self._display.status('Connecting...')
        self.connect_and_sync_time()
        # Upload the last error message, if logged
        self._timestream.upload_last_error(self._log)
        # Do an initial read and display (if attached)
        self._display.hide_status()        

    def connect_and_sync_time(self):
        """ Establish a connection and update the RTC from an NTP server.
            Will retry until successful. 
        """ 
        while(True):
            if self._connection.connect():
                self._display.status('Connected')
                if self._ntptime.set_rtc_from_ntp_time():
                    rtc = machine.RTC()
                    tm = rtc.datetime()
                    print(f"UTC Time {tm[3]:02d}:{tm[4]:02d}:{tm[5]:02d} {tm[2]:02d}-{tm[1]:02d}-{tm[0]} has been set from ntp time server")
                    return
                else:
                    print("time could not be read from ntp time server")
            else:
                print("Could not establish LAN connection")
            self._connection.disconnect()
            time.sleep(10)


