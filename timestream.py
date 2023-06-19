# Timestream class
#
# Copyright (C) Mark Gladding 2023.
#
# MIT License (see the accompanying license file)
#
# https://github.com/mark-gladding/weatherstation
#

import aws_auth
import json
import urequests

class Timestream:
    """
    """    
    def __init__(self, display, aws_access_key : str, aws_secret_access_key : str, aws_region : str, 
                 database_name : str, sensor_readings_table : str, sensor_location : str, remote_sensor_location : str, device_log_table : str):
        self._display = display
        self._aws_access_key = aws_access_key
        self._aws_secret_access_key = aws_secret_access_key
        self._aws_region = aws_region
        self._database_name = database_name
        self._sensor_readings_table = sensor_readings_table
        self._sensor_location = sensor_location
        self._remote_sensor_location = remote_sensor_location
        self._device_log_table = device_log_table

    def format_readings(self, current_time, tempC, pres_hPa, humRH):

        temperature = {
            'MeasureName': 'temperature',
            'MeasureValue': f'{tempC}',
            'Time': current_time
        }

        pressure = {
            'MeasureName': 'pressure',
            'MeasureValue': f'{pres_hPa}',
            'Time': current_time
        }

        humidity = {
            'MeasureName': 'humidity',
            'MeasureValue': f'{humRH}',
            'Time': current_time
        }

        return [temperature, pressure, humidity]

    def upload_readings(self, readings):

        self._display.status(f'Upload {len(readings)} reads.')
        dimensions = [ {'Name': 'location', 'Value': self._sensor_location} ]
        commonAttributes = {
                'Dimensions': dimensions,
                'MeasureValueType': 'DOUBLE',
                'TimeUnit' : 'SECONDS'
                }
        response = self.write_records(self._database_name, self._sensor_readings_table, readings, commonAttributes )    
        if response != None:
            try:
                total = json.loads(response.text)["RecordsIngested"]["Total"]
                self._display.status(f'Uploaded {total} of {len(readings)}.')

                if total == len(readings):
                    readings.clear()
                    return
            except KeyError:
                self._display.error(response.text)
        self._display.error("Upload failed.")

    def read_remote_sensor(self, last_valid_reading):

        try:
            if self._remote_sensor_location:    # Only read the remote sensor if it has a valid name
                response = self.read_last_record(self._database_name, self._sensor_readings_table, self._remote_sensor_location, 'temperature')
                if response:
                    reading = float(json.loads(response.text)["Rows"][0]["Data"][0]["ScalarValue"])
                    return reading
        except Exception as e:
            self._display.error(f'read_remote_sensor failed: {str(e)}')
        return last_valid_reading

    def upload_last_error(self, log):

        last_error = log.read_last_error()
        if not last_error:
            return
        
        self._display.status(f'Upload log.')
        dimensions = [ {'Name': 'location', 'Value': self._sensor_location} ]
        commonAttributes = {
                'Dimensions': dimensions,
                'MeasureValueType': 'VARCHAR',
                'TimeUnit' : 'SECONDS'
                }
        response = self.write_records( self._database_name, self._device_log_table, last_error, commonAttributes )    
        if response != None:
            try:
                total = json.loads(response.text)["RecordsIngested"]["Total"]
                if total == len(last_error):
                    self._display.status(f'Upload successful.')
                    log.clear_last_error()
                    return
            except KeyError:
                self._display.error(response.text)
        self._display.error("Upload failed.")        

    def send_timestream_request(self, host, command, payload="{}"):
        url = "https://" + host + "/"

        auth = aws_auth.AWSRequestsAuth(aws_access_key=self._aws_access_key,
                            aws_secret_access_key=self._aws_secret_access_key,
                            aws_host=host,
                            aws_region=self._aws_region,
                            aws_service='timestream')

        headers = {
            'X-Amz-Target': 'Timestream_20181101.{}'.format(command),
            'Content-Type': 'application/x-amz-json-1.0',
            'x-amz-api-version': '2018-11-01'
            }
        
        auth_headers = auth.get_aws_request_headers("POST", url, payload)
        headers = headers|auth_headers

        return urequests.post(url, headers=headers, data=payload)

    def get_host_cell(self, mode):
        describeHost = f"{mode}.timestream.{self._aws_region}.amazonaws.com"
        try:
            response = self.send_timestream_request(describeHost, "DescribeEndpoints" )
            queryHost = json.loads(response.text)["Endpoints"][0]["Address"]
            if queryHost:
                return queryHost
        except Exception as e:
            self._display.error(f'get_host_cell failed: {str(e)}')
        return None

    def query(self, payload):
        try:
            queryHost = self.get_host_cell('query')
            if queryHost:
                return self.send_timestream_request(queryHost, "Query", payload )
        except Exception as e:
            self._display.error(f'query failed: {str(e)}')
        return None

    def write_records_request(self, payload):
        try:
            ingestHost = self.get_host_cell('ingest')
            if ingestHost:
                return self.send_timestream_request(ingestHost, "WriteRecords", payload )
        except Exception as e:
            self._display.error(str(e))
        return None

    def write_records(self, databaseName, tableName, records, commonAttributes):

        payload = { "DatabaseName" : databaseName, "TableName" : tableName, "Records" : records, "CommonAttributes" : commonAttributes }
        return self.write_records_request(json.dumps(payload))

    def read_last_record(self, databaseName, tableName, sensor_location, measurement_name):
        query_string = f'select MAX_BY(measure_value::double, time) FROM {databaseName}."{tableName}" WHERE measure_name = \'{measurement_name}\' and location=\'{sensor_location}\' and time between ago(30m) and now()'
        payload = { "QueryString" : query_string }
        return self.query(json.dumps(payload))




