#
# Copyright (C) Mark Gladding 2023.
#
# MIT License (see the accompanying license file)
#
# https://github.com/mark-gladding/weatherstation
#

import time
import network

class Connection:
    """Class providing functions to connect/disconnect to/from a wireless LAN.

     Includes functionality to optionally turn off the WiFi radio on disconnect.
    """    
    def __init__(self, ssid : str, password : str, perform_complete_poweroff : bool):
        """Constructor

        Args:
            ssid (str): WiFi SSID to use when connecting
            password (str): WiFi password to use when connecting
            perform_complete_poweroff (bool): If True, disconnect will turn off the WiFi radio and connect will wait additional time for the WiFi radio to turn on.
        """        
        self._wlan = None
        self._ssid = ssid
        self._password = password
        self._perform_complete_poweroff = perform_complete_poweroff

    def connect(self):
        """ Establish a connection to the local WiFi network.
            Uses self._ssid and self._password when estblishing the connection.
            Uses self._perform_complete_poweroff to determine if an additional 3 seconds should be allowed for the WiFi radio to be re-activated.
            Safe to call multiple times - if the connection is already established, it will return immediately.
        """     
        if not self._wlan:
            self._wlan = network.WLAN(network.STA_IF)

        if not self._wlan.active():
            print('activating connection')
            self._wlan.active(True)
            if self._perform_complete_poweroff:
                time.sleep_ms(3000)     # Allow 3 seconds to re-activate the WiFi radio, etc.
        if not self._wlan.isconnected():
            print(f'Connecting to "{self._ssid}"')
            self._wlan.connect(self._ssid, self._password)
            retries = 0
            while not self._wlan.isconnected() and self._wlan.status() >= 0 and retries < 20:
                retries += 1
                print(f"Retry {retries}")
                time.sleep_ms(500)      
        return self._wlan.isconnected()

    def disconnect(self):
        """ Disconnect from the local WiFi network.
            Uses self._perform_complete_poweroff to determine if the WiFi radio should be turned off, so the Pico W can be placed in a low power mode.
            Safe to call multiple times - if there is no connection or its already disconnected, this function will do nothing.
        """ 
        if self._wlan == None:
            return

        if self._wlan.isconnected():
            print('disconnecting connection')
            self._wlan.disconnect()
        if self._wlan.active():
            print('deactivating connection')
            self._wlan.active(False)
            if self._perform_complete_poweroff:
                self._wlan.deinit()          # Turn off the WiFi radio.
                self._wlan = None
                time.sleep_ms(200)
