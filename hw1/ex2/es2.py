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
args = parser.parse_args()


redis_client = redis.Redis(
    host=args.host,
    port=args.port,
    password=args.password,
    username=args.user
)
print('Is connected:', redis_client.ping())

def safe_ts_create(key):
    try:
        redis_client.ts().create(key)
    except redis.ResponseError:
        pass
        
def safe_ts_createrule(key, key_agg, aggregation, bucket_size):
    try:
        redis_client.ts().createrule(
            key, key_agg, 
            aggregation_type = aggregation, 
            bucket_size_msec = bucket_size)
    except redis.ResponseError:
        redis_client.ts().deleterule(key, key_agg)
        redis_client.ts().createrule(
            key, key_agg, 
            aggregation_type = aggregation, 
            bucket_size_msec = bucket_size)
    

mac_address = hex(uuid.getnode())
safe_ts_create(f"{mac_address}:battery")
safe_ts_create(f"{mac_address}:power")
safe_ts_create(f"{mac_address}:plugged_seconds")
safe_ts_create(f"{mac_address}:battery_avg")
safe_ts_create(f"{mac_address}:power_avg")
safe_ts_create(f"{mac_address}:plugged_seconds_avg")
one_day_in_s = 24*60*60
time_now = time()
sec_plug = 0
ret_time = 0

while True:
    ts_in_s = time()
    ts_in_ms = int(ts_in_s*1000)
    battery_level = psutil.sensors_battery().percent
    power_plugged = psutil.sensors_battery().power_plugged
    
    redis_client.ts().add(f"{mac_address}:battery", ts_in_ms, battery_level)
    redis_client.ts().add(f"{mac_address}:power",ts_in_ms, int(power_plugged))
    if power_plugged:
        sec_plug += 1

    if time()-time_now == one_day_in_s:
        redis_client.ts().add(f"{mac_address}:plugged_seconds", ts_in_ms, sec_plug)
        time_now = time()

    # CHECK SE LA RULE ESISTE GIÀ

    # redis_client.ts().createrule(
    #     f"{mac_address}:battery", f"{mac_address}:battery_avg", 
    #     aggregation_type = "avg", 
    #     bucket_size_msec = 5*1000) #### CONTROLLARE LA BUCKET SIZE

    # redis_client.ts().createrule(
    #     f"{mac_address}:power", f"{mac_address}:power_avg", 
    #     aggregation_type = "avg", 
    #     bucket_size_msec = 5*1000) #### CONTROLLARE LA BUCKET SIZE
    
    # redis_client.ts().createrule(
    #     f"{mac_address}:plugged_seconds", f"{mac_address}:plugged_seconds_avg", 
    #     aggregation_type = "avg", 
    #     bucket_size_msec = 5*1000) #### CONTROLLARE LA BUCKET SIZE

    safe_ts_createrule(f"{mac_address}:battery", f"{mac_address}:battery_avg", "avg", 5*1000)
    safe_ts_createrule(f"{mac_address}:power", f"{mac_address}:power_avg", "avg", 5*1000)
    safe_ts_createrule(f"{mac_address}:plugged_seconds", f"{mac_address}:plugged_seconds_avg", "avg", 5*1000)

    if redis_client.ts().info(f"{mac_address}:battery_avg").memory_usage/1e6 >= 5:
        if ret_time < time()-time_now:
            ret_time = time()-time_now()
        redis_client.ts().alter(f"{mac_address}:battery_avg", retention_msec = time()-time_now())
    
    if redis_client.ts().info(f"{mac_address}:power_avg").memory_usage/1e6 >= 5:
        if ret_time < time()-time_now:
            ret_time = time()-time_now()
        redis_client.ts().alter(f"{mac_address}:power_avg", retention_msec = time()-time_now())
    
    if redis_client.ts().info(f"{mac_address}:plugged_seconds_avg").memory_usage/1e6 >= 1:
        if ret_time < time()-time_now:
            ret_time = time()-time_now()
        redis_client.ts().alter(f"{mac_address}:plugged_seconds", retention_msec = time()-time_now())

    sleep(1)


