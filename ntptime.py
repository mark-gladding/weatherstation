import json
import machine
import secrets
import settings
import socket
import struct
import time
import urequests

_timezone_offset = 0

def _get_timezone_offset():
    response = urequests.get(f'https://maps.googleapis.com/maps/api/timezone/json?location={settings.timezone_location}&timestamp={time.time()}&key={secrets.timezone_api_key}')
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

def _request_ntp_time(addr=settings.ntp_time_server):
    REF_TIME_1970 = 2208988800  # Reference time
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    NTP_QUERY = b'\x1b' + 47 * b'\0'
    print(f'Requesting time from {addr}')
    sockaddr = socket.getaddrinfo(addr, 123)[0][-1]
    try:
        s.settimeout(1)
        res = s.sendto(NTP_QUERY, sockaddr)
        msg = s.recv(48)
        if msg:
            t = struct.unpack("!I", msg[40:44])[0]
            t -= REF_TIME_1970
            return time.gmtime(t)        
    finally:
        s.close()    
    return None

def set_rtc_from_ntp_time():
    global _timezone_offset

    tm = _request_ntp_time()
    if not tm:
        return False
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))

    _timezone_offset = _get_timezone_offset()
    return True
    
def get_timezone_offset():
    return _timezone_offset

def get_local_time_string(utc_time):

    seconds_since_epoch = (int)(utc_time) + get_timezone_offset()
    tm = time.gmtime(seconds_since_epoch)

    return f'{tm[3] % 12:02d}:{tm[4]:02d}:{tm[5]:02d}'
