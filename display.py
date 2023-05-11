from PiicoDev_SSD1306 import *
import machine
import time
import packed_font

_led = machine.Pin("LED", machine.Pin.OUT)
_display = None
_show_status = True

def init_display():
    global _display

    _display = create_PiicoDev_SSD1306()
    if _display.comms_err:
        print('Display not detected.')
        _display = None
    else:
        packed_font.load_font('digits-32')
        packed_font.load_font('text-16')

def is_present():
    return not _display == None 

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

def update_readings(local_time_string, sensor_location, tempC, pres_hPa, humRH):
    global _display

    if not _display:
        return
    

    _display.fill_rect(0, 0, 128, 56, 0)

    packed_font.select_font('digits-32')
    packed_font.text(_display, f'{tempC:.1f}d', 0, 16, 128, 1)

    packed_font.select_font('text-16')
    packed_font.text(_display, f'{local_time_string}', 0, 0, 128, 1)
    packed_font.text(_display, f'{_title(sensor_location)}', 0, 48, 128, 1, 16, 2)

    # _display.text(f'Locn: {sensor_location}', 0, 0)
    # _display.text(f'Time: {local_time_string}', 0, 8)
    # _display.text(f'Temp: {tempC:.1f}', 0, 16)
    # _display.text(f'Pres: {pres_hPa:.0f}', 0, 24)
    # _display.text(f'Humi: {humRH:.0f}', 0, 32)
    _display.show()
