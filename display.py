from PiicoDev_SSD1306 import *
import machine
import time

_led = machine.Pin("LED", machine.Pin.OUT)
_display = None

def init_display():
    global _display

    _display = create_PiicoDev_SSD1306()
    if _display.comms_err:
        print('Display not detected.')
        _display = None

def is_present():
    return not _display == None 

def _flash_led():
    _led.on()
    time.sleep(.05)
    _led.off()

def status(text, flashcount=1):
    global _display, _led

    print(text)

    if not _display:
        while flashcount > 0:
            _flash_led()
            flashcount -= 1
        return
    
    _display.fill_rect(0, 56, 128, 8, 0)
    _display.text(text, 0, 56)
    _display.show()

def error(text):
    status(text, 2)

def clear():
    global _display

    if not _display:
        return
    
    _display.fill(0)
    _display.show()

def update_readings(local_time_string, tempC, pres_hPa, humRH):
    global _display

    if not _display:
        return

    _display.fill_rect(0, 0, 128, 56, 0)
    _display.text(f'Time: {local_time_string}', 0, 0)
    _display.text(f'Temp: {tempC:.1f}', 0, 8)
    _display.text(f'Pres: {pres_hPa:.0f}', 0, 16)
    _display.text(f'Humi: {humRH:.0f}', 0, 24)
    _display.show()
