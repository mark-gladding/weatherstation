# NtpTime class
#
# Copyright (C) Mark Gladding 2023.
#
# MIT License (see the accompanying license file)
#
# https://github.com/mark-gladding/weatherstation
#

import json
import machine
import socket
import struct
import time
import urequests

class NtpTime:
    """Class providing functions to connect/disconnect to/from a wireless LAN.

     Includes functionality to optionally turn off the WiFi radio on disconnect.
    """    
    def __init__(self, ntp_time_server : str, timezone_api_key : str, sync_time_period : int, timezone_location : str):
        self._ntp_time_server = ntp_time_server
        self._timezone_api_key = timezone_api_key
        self._sync_time_period = sync_time_period
        self._timezone_location = timezone_location
        self._timezone_offset = 0
        self._sync_time_count = 0

    def set_rtc_from_ntp_time(self):
        tm = self._request_ntp_time()
        if not tm:
            return False
        machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))

        self._timezone_offset = self._get_timezone_offset()
        return True        

    def sync_time(self):
        if self._sync_time_count >= self._sync_time_period:
            if self.set_rtc_from_ntp_time():
                self._sync_time_count = 0
                return
        self._sync_time_count += 1        

    def _get_timezone_offset(self):
        response = urequests.get(f'https://maps.googleapis.com/maps/api/timezone/json?location={self._timezone_location}&timestamp={time.time()}&key={self._timezone_api_key}')
        try:
            jresponse = json.loads(response.text)
            isOk = jresponse["status"] == 'OK'
            if isOk:
                offset_in_seconds = jresponse['rawOffset'] + jresponse['dstOffset']
                hours = (int)(offset_in_seconds / 3600)
                minutes = (int)((offset_in_seconds - hours * 3600) / 60)
                seconds = (int)(offset_in_seconds % 60)
                print(f'Retrieved timezone information {jresponse["timeZoneName"]} for {jresponse["timeZoneId"]}, offset = {hours:02d}:{minutes:02d}:{seconds:02d}.')
                return offset_in_seconds

        except AttributeError:
            pass    
        return 0

    def _request_ntp_time(self):
        addr = self._ntp_time_server
        REF_TIME_1970 = 2208988800  # Reference time
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        NTP_QUERY = b'\x1b' + 47 * b'\0'
        print(f'Requesting time from {addr}')
        sockaddr = socket.getaddrinfo(addr, 123)[0][-1]
        try:
            s.settimeout(1)
            s.sendto(NTP_QUERY, sockaddr)
            msg = s.recv(48)
            if msg:
                t = struct.unpack("!I", msg[40:44])[0]
                t -= REF_TIME_1970
                return time.gmtime(t)        
        except Exception as e:
            print(f'Failed to read time from {addr}: {str(e)}')
        finally:
            s.close()    
        return None
        
    def get_timezone_offset(self):
        return self._timezone_offset

    def get_local_time_string(self, utc_time):

        seconds_since_epoch = (int)(utc_time) + self.get_timezone_offset()
        tm = time.gmtime(seconds_since_epoch)
        hours_in_24_hour_format = tm[3]
        hours_in_12_hour_format = hours_in_24_hour_format % 12
        if hours_in_12_hour_format == 0:
            hours_in_12_hour_format = 12
        minutes = tm[4]

        return f"{ hours_in_12_hour_format:02d}:{minutes:02d} {'PM' if hours_in_24_hour_format >= 12 else 'AM' }"

