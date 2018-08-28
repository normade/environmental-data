"""A tempstation with the BME280 sensor for posting data to an API."""
import bme280
import credentials
import machine
import ujson
import urequests

from network import WLAN
from ubinascii import hexlify
from utime import sleep


class Tempstation():
    """Tempstation according to the Tempstation API."""

    MAC_ADDRESS = str(hexlify(WLAN().config('mac')).decode())
    SCL = None
    SDA = None
    BME = None
    LED_BLUE_ONBOARD = None
    LED_RED = None
    LED_GREEN = None
    LED_BLUE = None
    ID = 0
    TEMP_MIN = 0
    TEMP_MAX = 0
    HUM_MIN = 0
    HUM_MAX = 0
    PRES_MIN = 0
    PRES_MAX = 0
    INTERVAL = 0

    def set_up_pins(self):
        """Set up all necessary pins on the board."""
        self.SCL = machine.Pin(0)
        self.SDA = machine.Pin(4)
        self.LED_BLUE_ONBOARD = machine.Pin(2, machine.Pin.OUT)
        self.LED_BLUE_ONBOARD.on()
        self.LED_RED = machine.Pin(13, machine.Pin.OUT)
        self.LED_RED.on()
        self.LED_BLUE = machine.Pin(12, machine.Pin.OUT)
        self.LED_BLUE.on()
        self.LED_GREEN = machine.Pin(15, machine.Pin.OUT)
        self.LED_GREEN.on()
        sleep(2)

    def check_leds(self):
        """Check if the RGB led is working."""
        red = self.LED_RED
        green = self.LED_GREEN
        blue = self.LED_BLUE
        led_colors = [
            [red], [green], [blue], [red, blue], [blue, green], [red, green]
        ]
        for led_color in led_colors:
            if len(led_color) > 1:
                for color in led_color:
                    color.off()
                sleep(1)
                for color in led_color:
                    color.on()
            else:
                led_color[0].off()
                sleep(1)
                led_color[0].on()
            sleep(1)

    def set_up_sensor(self):
        """
        Set up the BME280 sensor.

        It's necessary to scan for the IC2 address and give it to the
        constructor of the BME280 (see driver file bme280.py).
        """
        i2c = machine.I2C(scl=self.SCL, sda=self.SDA)
        address = i2c.scan()
        self.BME = bme280.BME280(i2c=i2c, address=address[0])

    def initialize_controller_data(self):
        """Assign controller values given by the API."""
        api_data = urequests.get(credentials.get_controller_data.format(
            hardware_id=self.MAC_ADDRESS)).json()
        self.ID = api_data['id']
        self.critical_values = api_data['location']['criticalValues']

        for values in self.critical_values:
            if(values['id'] == 1):
                self.TEMP_MIN = values['minValue']
                self.TEMP_MAX = values['maxValue']
            if(values['id'] == 2):
                self.HUM_MIN = values['minValue']
                self.HUM_MAX = values['maxValue']
            if(values['id'] == 11):
                self.PRES_MIN = values['minValue']
                self.PRES_MAX = values['maxValue']

        self.INTERVAL = api_data['settings']['measureDuration']

    def _give_led_signal(self, values):
        """
        Light the LED to signal if measured data breaks critical values.

        - magenta: pressure is too low or high
        - red: temperature is too low or high
        - cyan: humidity is too low or high
        - green: otherwise
        """
        if (
            (float(values['pressure'][0]) > self.PRES_MAX) or
            (float(values['pressure'][0]) < self.PRES_MIN)
        ):
            for i in range(0, 3):
                self.LED_RED.off()
                self.LED_BLUE.off()
                sleep(1)
                self.LED_RED.on()
                self.LED_BLUE.on()
                sleep(1)
        else:
            self.LED_GREEN.off()
            sleep(1)
            self.LED_GREEN.on()
            sleep(1)

        if (
            (float(values['temperature'][0]) > self.TEMP_MAX) or
            (float(values['temperature'][0]) < self.TEMP_MIN)
        ):
            for i in range(0, 3):
                self.LED_RED.off()
                sleep(1)
                self.LED_RED.on()
                sleep(1)
        else:
            self.LED_GREEN.off()
            sleep(1)
            self.LED_GREEN.on()
            sleep(1)

        if (
            (float(values['humidity'][0]) > self.HUM_MAX) or
            (float(values['humidity'][0]) < self.HUM_MIN)
        ):
            for i in range(0, 3):
                self.LED_BLUE.off()
                self.LED_GREEN.off()
                sleep(1)
                self.LED_BLUE.on()
                self.LED_GREEN.on()
                sleep(1)
        else:
            self.LED_GREEN.off()
            sleep(1)
            self.LED_GREEN.on()
            sleep(1)

    def measure_and_post(self):
        """Measure data and post to the API."""
        values = {}
        data = self.BME.values
        values['temperature'] = [data[0], 1]
        values['humidity'] = [data[2], 2]
        values['pressure'] = [data[1], 3]
        self.LED_BLUE_ONBOARD.off()
        self.LED_BLUE.off()
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
        self.LED_BLUE_ONBOARD.on()
        self.LED_BLUE.on()
        sleep(2)
        self._give_led_signal(values)


def main():
    """Starter function."""
    temp_stat = Tempstation()
    temp_stat.set_up_pins()
    temp_stat.check_leds()
    temp_stat.set_up_sensor()
    temp_stat.initialize_controller_data()
    sleep(2)
    while True:
        temp_stat.measure_and_post()
        sleep(temp_stat.INTERVAL)
