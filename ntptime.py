import machine
import socket
import struct
import time

from settings import ntp_time_server

def _request_ntp_time(addr=ntp_time_server):
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
    tm = _request_ntp_time()
    if not tm:
        return False
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
    return True
    
    

