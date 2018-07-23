"""A Wifi station for the ESP8266 board."""
import credentials
import network


class WiFiStation():
    """A WiFi Station for the ESP8266."""

    ssid = credentials.ssid
    password = credentials.password
    station = network.WLAN(network.STA_IF)

    def connect(self):
        """Connect to WiFi."""
        if self.station.isconnected() is True:
            print("Already connected")
            return
        self.station.active(True)
        self.station.connect(self.ssid, self.password)
        print("Connection successful")

    def disconnect(self):
        """Disconnect from WiFi."""
        self.station.active(False)

wifi_stat = WiFiStation()
