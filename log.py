import json
from io import StringIO
import os
import sys
import time

_last_error_filename = 'LastError.json'

def write_last_error(exception):

    current_time = f'{time.time()}'

    message = {
        'Time': current_time,
        'MeasureName': 'exception',
        'MeasureValue': str(exception),
    }

    s = StringIO()
    sys.print_exception(exception, s)

    stack_trace = {
        'Time': current_time,
        'MeasureName': 'stack_trace',
        'MeasureValue': s.getvalue(),
    }

    records = [message, stack_trace]

    with open(_last_error_filename, 'w') as f:
       json.dump(records, f)
 
def read_last_error():
    try:
        with open(_last_error_filename) as f:
            return json.load(f)
    except OSError:
        pass
    return None
        
def clear_last_error():
    try:
        os.remove(_last_error_filename)
    except:
        pass