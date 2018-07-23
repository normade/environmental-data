"""Measure and post data."""

import credentials
import dht
from machine import Pin
import network
import ubinascii
import ujson
import urequests
from utime import sleep_ms


sleep_ms(1000)
sensor = dht.DHT22(Pin(4))
blue_led = Pin(2, Pin.OUT)

while True:
    data_dict = {}
    sensor.measure()
    print("Measured")
    data_dict['mac_id'] = str(
        ubinascii.hexlify(network.WLAN().config('mac'), ':').decode())
    data_dict['temp'] = str(sensor.temperature())
    data_dict['hum'] = str(sensor.humidity())
    blue_led.off()
    response = urequests.post(
        credentials.endpoint,
        data=ujson.dumps(data_dict),
        headers={'Content-Type': 'application/json'}
    )
    print("Server response: ", response.text)
    blue_led.on()
    sleep_ms(30000)
