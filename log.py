# Log class
#
# Copyright (C) Mark Gladding 2023.
#
# MIT License (see the accompanying license file)
#
# https://github.com/mark-gladding/weatherstation
#

import json
from io import StringIO
import os
import sys
import time

class Log:
    """
    """    
    def __init__(self):
        self._last_error_filename = 'LastError.json'

    def write_last_error(self, exception):

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

        with open(self._last_error_filename, 'w') as f:
            json.dump(records, f)
    
    def read_last_error(self):
        try:
            with open(self._last_error_filename) as f:
                return json.load(f)
        except OSError:
            pass
        return None
            
    def clear_last_error(self):
        try:
            os.remove(self._last_error_filename)
        except:
            pass