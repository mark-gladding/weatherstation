# Module providing functions to connect/disconnect to/from a wireless LAN.
# Includes functionality to optionally turn off the WiFi radio on disconnect.
#
# Copyright (C) Mark Gladding 2023.
#
# MIT License (see the accompanying license file)
#
# https://github.com/mark-gladding/weatherstation
#

import time
import network
import secrets          # Required for the WiFi SSID and password
import settings         # Uses the deep_sleep setting to determine if the WiFi radio should be turned off during disconnect.

_wlan = None

def connect():
    """ Establish a connection to the local WiFi network.
        Uses secrets.wifi_ssid and secrets.wifi_password when estblishing the connection.
        Uses settings.deep_sleep to determine if an additional 3 seconds should be allowed for the WiFi radio to be re-activated.
        Safe to call multiple times - if the connection is already established, it will return immediately.
    """     
    global _wlan

    if not _wlan:
        _wlan = network.WLAN(network.STA_IF)

    if not _wlan.active():
        print('activating connection')
        _wlan.active(True)
        if settings.deep_sleep:
            time.sleep_ms(3000)     # Allow 3 seconds to re-activate the WiFi radio, etc.
    if not _wlan.isconnected():
        print(f'Connecting to "{secrets.wifi_ssid}"')
        _wlan.connect(secrets.wifi_ssid, secrets.wifi_password)
        retries = 0
        while not _wlan.isconnected() and _wlan.status() >= 0 and retries < 20:
            retries += 1
            print(f"Retry {retries}")
            time.sleep_ms(500)      
    return _wlan.isconnected()

def disconnect():
    """ Disconnect from the local WiFi network.
        Uses settings.deep_sleep to determine if the WiFi radio should be turned off, so the Pico W can be placed in a low power mode.
        Safe to call multiple times - if there is no connection or its already disconnected, this function will do nothing.
    """ 
    global _wlan

    if _wlan == None:
        return

    if _wlan.isconnected():
        print('disconnecting connection')
        _wlan.disconnect()
    if _wlan.active():
        print('deactivating connection')
        _wlan.active(False)
        if settings.deep_sleep:
            _wlan.deinit()          # Turn off the WiFi radio.
            _wlan = None
            time.sleep_ms(200)
