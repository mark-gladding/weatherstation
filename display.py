# Display class
#
# Copyright (C) Mark Gladding 2023.
#
# MIT License (see the accompanying license file)
#
# https://github.com/mark-gladding/weatherstation
#

from enhanced_display import Enhanced_Display
import machine
from machine import Timer
import micropython
import time

class Display:
    """
    """    
    def __init__(self, display_cycle_period_ms : int):
        self._display_cycle_period_ms = display_cycle_period_ms
        self._led = machine.Pin("LED", machine.Pin.OUT)
        self._display = None
        self._timer = None
        self._readings = []
        self._reading_index = 0
        self._show_status = True

    def init(self):

        self._display = Enhanced_Display()

        if not self._display.is_present:
            print('Display not detected.')
            self._display = None
        else:
            self._display.load_fonts(['digits-30','text-16'])

    def is_present(self):
        return self._display != None 

    def _flash_led(self):
        self._led.on()
        time.sleep(.05)
        self._led.off()

    def hide_status(self):
        self.status('', 0)
        self._show_status = False

    def show_status(self):
        self._show_status = True

    def status(self, text, flashcount=1):

        print(text)

        if not self._show_status:
            return

        if not self._display:
            while flashcount > 0:
                self._flash_led()
                flashcount -= 1
            return
        
        self._display.fill_rect(0, 56, self._display.width, 8, 0)
        self._display.select_font(None)
        self._display.text(text, 0, 56)
        self._display.show()

    def error(self, text):
        self.status(text, 2)

    def _title(self, text):
        isTitlePos = True
        base = ord('A')
        offset = -ord('a')
        titleText = ''
        for c in text:
            if(isTitlePos and c >= 'a' and c <= 'z'):
                titleText += (chr(ord(c) + offset + base))
                isTitlePos = False
            else:
                if c == ' ':
                    isTitlePos = True
                titleText += c
        return titleText

    def cycle_display(self):

        self._display.fill(0)

        if len(self._readings) == 0:
            return
        
        self._reading_index = min(self._reading_index, len(self._readings) - 1)
        self.current_readings = self._readings[self._reading_index]
        temperature = self.current_readings['Temperature']
        local_time_string = self.current_readings['Time']
        sensor_location = self.current_readings['Location']

        self._display.select_font('digits-30')
        degrees = '\u00b0'
        self._display.text(f'{temperature:.1f}{degrees}', 0, 16, 1)

        self._display.select_font('text-16')
        self._display.text(f'{local_time_string}', 0, 0, 1)
        self._display.text(f'{self._title(sensor_location)}', 0, 0, 1, 2)

        self._display.show()
        self._reading_index = (self._reading_index + 1) % len(self._readings)

    def update_readings(self, local_time_string, sensor_location, tempC, remote_location, remote_tempC):
        if not self._display:
            return
        
        self._reading_index = 0
        self._readings = [ 
            { 'Time' : local_time_string,
            'Location' : sensor_location,
            'Temperature' : tempC }
        ]
        
        if remote_location:
            self._readings.append(        
                { 'Time' : local_time_string,
                'Location' : remote_location,
                'Temperature' : remote_tempC })
            
            if not self._timer:
                self._timer = Timer()
                self._timer.init(mode=Timer.PERIODIC, period=self._display_cycle_period_ms, callback=self._timer_callback)
                self.cycle_display()
        else:
            self.cycle_display()
        

    def _timer_callback(self, calback_arg):
            micropython.schedule(self._scheduled_cycle_display, calback_arg)

    def _scheduled_cycle_display(self, callback_arg):
        self.cycle_display()
