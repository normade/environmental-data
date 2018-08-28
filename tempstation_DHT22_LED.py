"""A tempstation for the DHT22 sensor posting data to an API."""
import credentials
import dht
import ujson
import urequests

from machine import Pin
from network import WLAN
from ubinascii import hexlify
from utime import sleep


class Tempstation():
    """Tempstation according to the Tempstation API."""

    MAC_ADDRESS = str(hexlify(WLAN().config('mac')).decode())
    SENSOR = None
    ID = 0
    TEMP_MIN = 0
    TEMP_MAX = 0
    HUM_MIN = 0
    HUM_MAX = 0
    INTERVAL = 0
    LED_BLUE = None
    LED_RED = None
    LED_GREEN = None

    def set_up_pins(self):
        """Set up all necessary pins on the board."""
        self.SENSOR = dht.DHT22(Pin(4))
        self.LED_BLUE = Pin(2, Pin.OUT)
        self.LED_BLUE.on()
        self.LED_RED = Pin(13, Pin.OUT)
        self.LED_RED.on()
        self.LED_GREEN = Pin(12, Pin.OUT)
        self.LED_GREEN.on()
        print("Pins are set up.")

    def initialize_controller_data(self):
        """Assign controller values given by the API."""
        api_data = urequests.get(credentials.get_controller_data.format(
            hardware_id=self.MAC_ADDRESS)).json()
        print("Received following API data: ", api_data)
        self.ID = api_data['id']
        critical_values = api_data['location']['criticalValues']

        for values in critical_values:
            if(values['id'] == 1):
                self.TEMP_MIN = values['minValue']
                self.TEMP_MAX = values['maxValue']
            if(values['id'] == 2):
                self.HUM_MIN = values['minValue']
                self.HUM_MAX = values['maxValue']
        self.INTERVAL = api_data['settings']['measureDuration']
        print("Assigned controller values from the API.")

    def _give_led_signal(self, values):
        """Light the LED to signal if measured data breaks critical values."""
        if (
            (values['temperature'][0] > self.TEMP_MAX) or
            (values['humidity'][0] > self.HUM_MAX) or
            (values['temperature'][0] < self.TEMP_MIN) or
            (values['humidity'][0] < self.HUM_MIN)
        ):
            for i in range(0, 3):
                self.LED_RED.off()
                sleep(1)
                self.LED_RED.on()
                sleep(1)
        else:
            for i in range(0, 3):
                self.LED_GREEN.off()
                sleep(1)
                self.LED_GREEN.on()
                sleep(1)

    def measure_and_post(self):
        """Measure data and post to the API."""
        self.LED_BLUE.off()
        values = {}
        self.SENSOR.measure()
        values['temperature'] = [self.SENSOR.temperature(), 1]
        values['humidity'] = [self.SENSOR.humidity(), 2]
        print("Measured the following: ", values)
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
        sleep(2)
        self._give_led_signal(values)


def main():
    """Starter function."""
    temp_stat = Tempstation()
    temp_stat.set_up_pins()
    temp_stat.initialize_controller_data()
    sleep(2)
    while True:
        temp_stat.measure_and_post()
        sleep(temp_stat.INTERVAL)
