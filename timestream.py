import aws_auth
import display
import json
import log
import secrets
import settings
import urequests

def send_timestream_request(host, command, payload="{}"):
    url = "https://" + host + "/"

    auth = aws_auth.AWSRequestsAuth(aws_access_key=secrets.aws_access_key,
                           aws_secret_access_key=secrets.aws_secret_access_key,
                           aws_host=host,
                           aws_region=settings.aws_region,
                           aws_service='timestream')

    headers = {
        'X-Amz-Target': 'Timestream_20181101.{}'.format(command),
        'Content-Type': 'application/x-amz-json-1.0',
        'x-amz-api-version': '2018-11-01'
        }
    
    auth_headers = auth.get_aws_request_headers("POST", url, payload)
    headers = headers|auth_headers

    return urequests.post(url, headers=headers, data=payload)

def get_host_cell(mode):
    describeHost = f"{mode}.timestream.{settings.aws_region}.amazonaws.com"
    try:
        response = send_timestream_request(describeHost, "DescribeEndpoints" )
        queryHost = json.loads(response.text)["Endpoints"][0]["Address"]
        if queryHost:
            return queryHost
    except Exception as e:
        display.error(f'get_host_cell failed: {str(e)}')
    return None

def query(payload):
    try:
        queryHost = get_host_cell('query')
        if queryHost:
            return send_timestream_request(queryHost, "Query", payload )
    except Exception as e:
        display.error(f'query failed: {str(e)}')
    return None

def write_records_request(payload):
    try:
        ingestHost = get_host_cell('ingest')
        if ingestHost:
            return send_timestream_request(ingestHost, "WriteRecords", payload )
    except Exception as e:
        display.error(str(e))
    return None

def write_records(databaseName, tableName, records, commonAttributes):

    payload = { "DatabaseName" : databaseName, "TableName" : tableName, "Records" : records, "CommonAttributes" : commonAttributes }
    return write_records_request(json.dumps(payload))

def read_last_record(databaseName, tableName, sensor_location, measurement_name):
    query_string = f'select MAX_BY(measure_value::double, time) FROM {databaseName}."{tableName}" WHERE measure_name = \'{measurement_name}\' and location=\'{sensor_location}\' and time between ago(1hour) and now()'
    payload = { "QueryString" : query_string }
    return query(json.dumps(payload))

def read_remote_sensor(last_valid_reading):
    return read_remote_sensor_record(settings.database_name, settings.sensor_readings_table, settings.remote_sensor_location, last_valid_reading)
    
def read_remote_sensor_record(databaseName, tableName, sensor_location, last_valid_reading):
    
    try:
        response = read_last_record(databaseName, tableName, sensor_location, 'temperature')
        if response:
            reading = float(json.loads(response.text)["Rows"][0]["Data"][0]["ScalarValue"])
            return reading
    except Exception as e:
        display.error(f'read_remote_sensor failed: {str(e)}')
    return last_valid_reading

def format_readings(current_time, tempC, pres_hPa, humRH):

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

def upload_readings(readings):

    display.status(f'Upload {len(readings)} reads.')
    dimensions = [ {'Name': 'location', 'Value': settings.sensor_location} ]
    commonAttributes = {
            'Dimensions': dimensions,
            'MeasureValueType': 'DOUBLE',
            'TimeUnit' : 'SECONDS'
            }
    response = write_records(settings.database_name, settings.sensor_readings_table, readings, commonAttributes )    
    if response != None:
        try:
            total = json.loads(response.text)["RecordsIngested"]["Total"]
            display.status(f'Uploaded {total} of {len(readings)}.')

            if total == len(readings):
                readings.clear()
                return
        except KeyError:
            display.error(response.text)
    display.error("Upload failed.")

def upload_last_error():

    last_error = log.read_last_error()
    if not last_error:
        return
     
    display.status(f'Upload log.')
    dimensions = [ {'Name': 'location', 'Value': settings.sensor_location} ]
    commonAttributes = {
            'Dimensions': dimensions,
            'MeasureValueType': 'VARCHAR',
            'TimeUnit' : 'SECONDS'
            }
    response = write_records( settings.database_name, settings.device_log_table, last_error, commonAttributes )    
    if response != None:
        try:
            total = json.loads(response.text)["RecordsIngested"]["Total"]
            if total == len(last_error):
                display.status(f'Upload successful.')
                log.clear_last_error()
                return
        except KeyError:
            display.error(response.text)
    display.error("Upload failed.")
