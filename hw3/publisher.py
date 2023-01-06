import paho.mqtt.client as mqtt

import time
import psutil
import uuid
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "--msg-topic",
    type=str,
    default="s299266",
    help="Message topic to send."
)
parser.add_argument(
    "--frequency",
    type=int,
    help="Time in seconds to wait before sending a new message",
    default=1
)
args = parser.parse_args()

client = mqtt.Client()

client.connect("mqtt.eclipseprojects.io", 1883)

def _get_data() -> dict:
    data = dict()
    timestamp = time.time()*1000
    mac_address = hex(uuid.getnode())
    battery_level = psutil.sensors_battery().percent
    power_plugged  = psutil.sensors_battery().power_plugged
    data['mac_address'] = mac_address
    data['timestamp'] = timestamp
    data['battery_level'] = battery_level
    data['power_plugged'] = power_plugged
    return data


while True:
    print(f"Current time: {time.time()}")
    print("Retrieving data from current host...")
    client.publish(args.msg_topic, json.dumps(_get_data()))
    print("Sending data to reciver...")
    time.sleep(args.frequency)