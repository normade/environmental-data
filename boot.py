"""This file is executed on every boot (including wake-boot from deepsleep)."""
# import esp
# esp.osdebug(None)
from utime import sleep
from wifi import wifi_stat
import gc
import tempstation
# import webrepl\n
# webrepl.start()\n
gc.collect()
wifi_stat.connect()
while not wifi_stat.station.isconnected():
    sleep(1)
tempstation.main()
