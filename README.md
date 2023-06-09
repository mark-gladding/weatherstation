# Weatherstation

![Temperature comparison in Grafana](images/grafana-temperature-display.png "Temperature comparison in Grafana")

This project was born out of a desire to compare the indoor temperature of my home office with the outside temperature over the course of a 24 hour period. This data would provide a way of evaluating the effectiveness of the insulation used in the construction of the home office. This high level goal led to the following requirements:

  * Two separate temperature sensors which can be located independent of each other and not require any physical connection between the two.
  * Ability to view the data from any location on any internet connected device with a web browser such as a mobile phone, laptop, etc.
  * Full control and ownership of the data collected.
  * No ongoing fees to store or access the data.
  * Ability to graph the indoor and outdoor temperature readings over a 24 hour period in a way that is easy to compare the different rates of change and minimum and maximum readings.

These requirements led to the following design:

  * Use of a Raspberry Pi Pico W running MicroPython, coupled with a BME280 Atmospheric Sensor.
  * Use of a SSD1306 OLED display for displaying the current indoor and outdoor temperature on the indoor unit.
  * Use of a 2000Ah LiPo battery to power the outdoor sensor.
  * Periodic (e.g. every 60 seconds) reading of the sensor and upload to AWS Timestream for storage of time-series data in the cloud.
  * Periodic (e.g. every 60 seconds) download of the latest outdoor sensor reading from AWS Timestream for display on the indoor display.
  * Use of a NTP time server to retrieve the current time and set the Pico's real time clock.
  * Use a GCP timezone server to automatically calculate the local time, adjusting for daylight saving.
  * Enter 'deepsleep' mode between readings to conserve battery power for the outdoor sensor.
  * Periodic cycling (every 5 secods) of the indoor display to alternatively show the indoor temperature and the outdoor temperature.
  * Graphing of the latest 24 hour period of the indoor and outdoor temperature readings using Grafana Cloud. 
  * Catch and upload exceptions to AWS Timestream to aid in debugging of sensor units running in the field without a display or debug port attached.

![Weather Station Network Diagram](images/network-diagram.png "Weather Station Network Diagram")

## Connecting to the Internet
The first thing we need is a means of connecting to and disconnecting from the Internet (or more accurately your WiFi network which in turn provides access to the Internet). This is relatively trivial using the Pico W and MicroPython. MicroPython provides a `network` module which contains a [WLAN](https://docs.micropython.org/en/latest/library/network.WLAN.html) class. To establish a connection you need to:  

  1. Create an instance of the WLAN class.
  1. Activate the connection. If the WiFi radio has been turned off, wait for it to be activated (e.g. 3 seconds).
  1. Initiate a connection, supplying your local WiFi _SSID_ and _password_.
  1. Perodically poll the status of the connection until `isconnected()` returns true.

For this application, being able to disconnect and turn off the WiFi radio is vital when it comes to conserving power when running on battery. To disconnect you need to:  

  1. Disconnect the connection
  1. Deactivate the connection
  1. Turn off the WiFi radio (using `deinit()`)
  1. Release the WLAN class instance.

Code to `connect()` and `disconnect()` can be found in [connection.py](connection.py).

* Time
   * NTP
   * Timezone
* Periodic reading of sensor values
* Uploading readings to AWS Timestream
   * HTTPS requests must be signed
   * Access key and secret access key
   * Locating the host cell
* Error handling
   * Uploading error logs   
* Downloading remote sensor readings
* Displaying temperatures on the display
* Battery Power
   * Battery type, power banks
   * Conserving power
   * Deep sleep mode
* Enclosures
* Graphing data
