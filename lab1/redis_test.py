import redis
import time

host = "redis-12034.c226.eu-west-1-3.ec2.cloud.redislabs.com"
port = 12034
username = "default"
password = "ypPNXAVuFTn5nNr8H28zSN0hLYLcH1z7"

client = redis.Redis(
    host=host,
    port=port,
    username=username,
    password=password
    )

print("Is connected: ", client.ping())

#to insert a key-value pair
client.set("first MSG", "Hello, World!")
#to retrieve a value from key -> gets returned in bits -> .decode()
print(client.get("first MSG").decode())

#how to create a time series
client.ts().create("temperature")
timestamp_in_seconds = time.time()
timestamp_in_ms = int(timestamp_in_seconds * 1000)
client.ts().add("temperature", timestamp=timestamp_in_ms, value=25.6)