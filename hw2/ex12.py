import psutil
from time import time, sleep
from datetime import datetime
import uuid
import redis
from time import time
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--host", type = str, default = "redis-15072.c77.eu-west-1-1.ec2.cloud.redislabs.com")
parser.add_argument("--port", type = int, default = 15072)
parser.add_argument("--user", type = str, default = "default")
parser.add_argument("--password", type = str, default = "53R8YAlL81zAHIEVcPjwjzcnVQoSPhzt")
parser.add_argument("--device", type = int, default = 1)  #### rivedere questo
args = parser.parse_args()

redis_client = redis.Redis(
    host = args.host, 
    password = args.password, 
    username = args.user, 
    port = args.port)

print("Is connected? ", redis_client.ping())

def safe_ts_create(key):
    try:
        redis_client.ts().create(key)
    except redis.ResponseError:
        pass

while True:
    ts_in_s = time()
    ts_in_ms = int(ts_in_s*1000)
    mac_id = hex(uuid.getnode())
    battery_level = psutil.sensors_battery().percent
    power_plugged = psutil.sensors_battery().power_plugged
    formatted_datetime = datetime.fromtimestamp(ts_in_s)
    print(f"{formatted_datetime} - {mac_id}: battery level ", battery_level)
    print(f"{formatted_datetime} - {mac_id}: power plugged: ", power_plugged)
    
    safe_ts_create("mac_adress:battery")
    redis_client.ts().add("mac_adress:battery", ts_in_ms, battery_level)

    safe_ts_create("mac_adress:power")
    redis_client.ts().add("mac_adress:power",ts_in_ms, int(power_plugged))

    sleep(1)