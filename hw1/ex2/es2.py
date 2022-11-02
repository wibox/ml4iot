import psutil
from time import time, sleep
from datetime import datetime
import uuid
import redis
from time import time

REDIS_HOST = "redis-15072.c77.eu-west-1-1.ec2.cloud.redislabs.com"
REDIS_PORT = 15072
REDIS_USER = "default"
REDIS_PASSWORD = "53R8YAlL81zAHIEVcPjwjzcnVQoSPhzt"


redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    username=REDIS_USER
)
print('Is connected:', redis_client.ping())

def safe_ts_create(key):
    try:
        redis_client.ts().create(key)
    except redis.ResponseError:
        pass

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

    redis_client.ts().createrule(
        f"{mac_address}:battery", f"{mac_address}:battery_avg", 
        aggregation_type = "avg", 
        bucket_size_msec = 5*1000) #### CONTROLLARE LA BUCKET SIZE

    redis_client.ts().createrule(
        f"{mac_address}:power", f"{mac_address}:power_avg", 
        aggregation_type = "avg", 
        bucket_size_msec = 5*1000) #### CONTROLLARE LA BUCKET SIZE
    
    redis_client.ts().createrule(
        f"{mac_address}:plugged_seconds", f"{mac_address}:plugged_seconds_avg", 
        aggregation_type = "avg", 
        bucket_size_msec = 5*1000) #### CONTROLLARE LA BUCKET SIZE


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


