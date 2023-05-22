import connection
import display
import machine
import ntptime
import time
import timestream

def connect_and_sync_time():
    """ Establish a connection and update the RTC from an NTP server.
        Will retry until successful. 
    """ 
    while(True):
        if connection.connect():
            display.status('Connected')
            if ntptime.set_rtc_from_ntp_time():
                rtc = machine.RTC()
                tm = rtc.datetime()
                print(f"UTC Time {tm[3]:02d}:{tm[4]:02d}:{tm[5]:02d} {tm[2]:02d}-{tm[1]:02d}-{tm[0]} has been set from ntp time server")
                return
            else:
                print("time could not be read from ntp time server")
        else:
            print("Could not establish LAN connection")
        connection.disconnect()
        time.sleep(10)


def startup():
    display.init_display()
    display.status('Connecting...')
    connect_and_sync_time()
    # Upload the last error message, if logged
    timestream.upload_last_error()
    # Do an initial read and display (if attached)
    display.hide_status()