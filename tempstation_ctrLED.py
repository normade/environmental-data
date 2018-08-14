"""A tempstation for posting data to an API."""
import credentials
import dht
import ujson
import urequests

from machine import Pin
from network import WLAN
from ubinascii import hexlify
from utime import sleep


class Tempstation():
    """Tempstation according the Tempstation API."""

    SENSOR = dht.DHT22(Pin(4))
    LED_BLUE = Pin(2, Pin.OUT)
    LED_BLUE.on()
    LED_RED = Pin(13, Pin.OUT)
    LED_RED.on()
    LED_GREEN = Pin(12, Pin.OUT)
    LED_GREEN.on()
    MAC_ADDRESS = str(hexlify(WLAN().config('mac')).decode())
    ID = 0
    TEMP_MIN = 0
    TEMP_MAX = 0
    HUM_MIN = 0
    HUM_MAX = 0
    INTERVAL = 0

    def initialize_controller_data(self):
        """Assign controller values given by the API."""
        api_data = urequests.get(credentials.get_controller_data.format(
            hardware_id=self.MAC_ADDRESS)).json()
        self.ID = api_data['id']
        self.critical_values = api_data['location']['criticalValues']
        self.TEMP_MIN = api_data['location']['criticalValues'][0]['minValue']
        self.TEMP_MAX = api_data['location']['criticalValues'][0]['maxValue']
        self.HUM_MIN = api_data['location']['criticalValues'][1]['minValue']
        self.HUM_MAX = api_data['location']['criticalValues'][1]['maxValue']
        self.INTERVAL = api_data['settings']['measureDuration']

    def measure_and_post(self):
        """Measure data and post to the API."""
        self.LED_BLUE.off()
        values = {}
        self.SENSOR.measure()
        values['temperature'] = [self.SENSOR.temperature(), 1]
        values['humidity'] = [self.SENSOR.humidity(), 2]
        if (
            (values['temperature'][0] > self.TEMP_MAX) or
            (values['humidity'][0] > self.HUM_MAX) or
            (values['temperature'][0] < self.TEMP_MIN) or
            (values['humidity'][0] < self.HUM_MIN)
        ):
            self.LED_RED.off()
            sleep(2)
            self.LED_RED.on()
        else:
            self.LED_GREEN.off()
            sleep(2)
            self.LED_GREEN.on()

        for key in values:
            data_dict = {}
            data_dict['value'] = values[key][0]
            data_dict['unitId'] = values[key][1]
            resp = urequests.post(
                credentials.post_data.format(station_ID=self.ID),
                data=ujson.dumps(data_dict),
                headers={'Content-Type': 'application/json'}
            )
            print("Sending", key, resp.status_code, resp.text)
        self.LED_BLUE.on()


def main():
    """Starter function."""
    temp_stat = Tempstation()
    temp_stat.initialize_controller_data()
    sleep(5)
    while True:
        temp_stat.measure_and_post()
        sleep(temp_stat.INTERVAL)
