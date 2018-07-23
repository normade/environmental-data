"""This file is executed on every boot (including wake-boot from deepsleep)."""
# import esp
# esp.osdebug(None)
from wifi import wifi_stat
import gc
# import webrepl\n
# webrepl.start()\n
gc.collect()
wifi_stat.connect()
