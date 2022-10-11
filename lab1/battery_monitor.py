import psutil
import time
import datetime
import uuid

mac_address = hex(uuid.getnode())

while True:
    battery_info = psutil.sensors_battery()
    #i need battery level and plug flag:
    #battery -> .percent
    #plug flag -> .power_plugged
    timestamp = time.time() #expressed in seconds
    #using dataetime to properly format timestamp
    fdt = datetime.datetime.fromtimestamp(timestamp)
    battery_level_percentage = battery_info.percent
    battery_plug_flag = battery_info.power_plugged
    print(f"{fdt} - {mac_address}:battery = {battery_level_percentage}")
    print(f"{fdt} - {mac_address}:power = {battery_plug_flag}")
    time.sleep(2)#becuase i want this info every 2 seconds to be written in the stream