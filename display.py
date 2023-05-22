from enhanced_display import Enhanced_Display
import machine
from machine import Timer
import micropython
import settings
import time

_led = machine.Pin("LED", machine.Pin.OUT)
_display = None
_timer = None
_readings = []
_reading_index = 0
_show_status = True

def init_display():
    global _display

    _display = Enhanced_Display()
    if not _display.is_present:
        print('Display not detected.')
        _display = None
    else:
        _display.load_fonts(['digits-30','text-16'])

def is_present():
    return _display != None 

def _flash_led():
    _led.on()
    time.sleep(.05)
    _led.off()

def hide_status():
    global _show_status
    status('', 0)
    _show_status = False

def show_status():
    global _show_status
    _show_status = True

def status(text, flashcount=1):
    global _display, _led

    print(text)

    if not _show_status:
        return

    if not _display:
        while flashcount > 0:
            _flash_led()
            flashcount -= 1
        return
    
    _display.fill_rect(0, 56, _display.width, 8, 0)
    _display.select_font(None)
    _display.text(text, 0, 56)
    _display.show()

def error(text):
    status(text, 2)

def _title(text):
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

def cycle_display():
    global _reading_index

    _display.fill(0)

    if len(_readings) == 0:
        return
    
    _reading_index = min(_reading_index, len(_readings) - 1)
    current_readings = _readings[_reading_index]
    temperature = current_readings['Temperature']
    local_time_string = current_readings['Time']
    sensor_location = current_readings['Location']

    _display.select_font('digits-30')
    degrees = '\u00b0'
    _display.text(f'{temperature:.1f}{degrees}', 0, 16, 1)

    _display.select_font('text-16')
    _display.text(f'{local_time_string}', 0, 0, 1)
    _display.text(f'{_title(sensor_location)}', 0, 0, 1, 2)

    _display.show()
    _reading_index = (_reading_index + 1) % len(_readings)

def scheduled_cycle_display(calback_arg):
    cycle_display()

def timer_callback(calback_arg):
    micropython.schedule(scheduled_cycle_display, None)

def update_readings(local_time_string, sensor_location, tempC, remote_location, remote_tempC):
    global _timer, _readings, _reading_index

    if not _display:
        return
    
    _reading_index = 0
    _readings = [ 
        { 'Time' : local_time_string,
          'Location' : sensor_location,
          'Temperature' : tempC }
    ]
    
    if remote_location:
        _readings.append(        
            { 'Time' : local_time_string,
              'Location' : remote_location,
              'Temperature' : remote_tempC })
        
        if not _timer:
            _timer = Timer()
            _timer.init(mode=Timer.PERIODIC, period=settings.display_cycle_period_ms, callback=timer_callback)
            cycle_display()
    else:
        cycle_display()
    

