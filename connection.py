import time
import network   # handles connecting to WiFi
from settings import *

# Connect to network
_wlan = network.WLAN(network.STA_IF)

def connect():
    if not _wlan.active():
        print('activating connection')
        _wlan.active(True)
    if not _wlan.isconnected():
        print(f'Connecting to "{ssid}"')
        _wlan.connect(ssid, password)
        retries = 0
        while not _wlan.isconnected() and _wlan.status() >= 0 and retries < 20:
            retries += 1
            print(f"Retry {retries}")
            time.sleep_ms(500)      
    return _wlan.isconnected()

def disconnect():
    if _wlan.isconnected():
        print('disconnecting connection')
        _wlan.disconnect()
    if _wlan.active():
        print('deactivating connection')
        _wlan.active(False)
        
