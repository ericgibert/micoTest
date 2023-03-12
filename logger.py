"""
Logger for the application into Firebase Realtime Database

Every Log entry will have the following structure:
- timestamp: a Datetime object recording the moment the data was collected
- logType: INFO, WARNING, ERROR, DATA
- systemId: a free name to identify the system generating the logs
- sensorId: a sensor belonging to the system
- message: free text
- rawValue: the value obtained from the sensor, as a real number
- calcValue: the result of a calculation from the raw value to calculated value

"""
from collections import deque
import urequests
from utime import time_ns, ticks_us
# from FIFOqueue import FIFOQueue

class uInfluxDBClient():
    """
    Small wrapper to send data to a remote InfluxDB
    WIFI Network connection must already be established
    """
    def __init__(self, org, url=None, host=None, port=None, token=None):
        """
        Save the parameters for future calls
        """
        self.org = org
        self.url = url or f"http://{host}:{port}"
        self.token = token or "lfpFxGZ06BGjgiHZEqFyArU2p7FBHAnOtNzPak0HZT1hPCxv1eYA50c7XUorKRUoimFhL839PRVA3antbZeKEw=="

    def write_api(self, bucket, records):
        """
        bucket:  A created database in InfluxDb
        records: A list of points/data to write in this bucket/database
        """
        url_write = f"{self.url}/write?db={bucket}"
        response = urequests.post(url_write, data="\n".join(records), headers={'Authorization': f'Token {self.token}'})
        return response

class Logger:
    """
    Connectivity with an influxDB hosted on a server
    Offer helpers to add or retrieve log entries
    """
    data = {
        "timestamp": None,  #  this timestamp is taken when the data are given to the Logger ==> time in influxDb
        "logType": "DATA",  #  INFO, WARNING, ERROR, DATA (default)
        "systemId": None,   # influxDB measurement/database
        "sensorId": None,   # influxDB Tag/key
        "message": "",      #  data field
        "rawValue": 0.0,    #  data field
        "calcValue": 0.0    #  data field
    }
    

    def __init__(self, systemId, host="192.168.18.3", port="8086", org="Perso", tz=0):
        """
        # connects to the database hosted on http://host:port
        # systemId: identfies the system either by a given name or by its mac address
        #           this will be a measurement/database for InfluxDb
        """
        self.logEntries = deque((), 1000)  #  FIFO queue accepting 1000 pending readings
#         self.logEntries = FIFOQueue()  
        self.data["systemId"] = systemId
        self.dbLogs = uInfluxDBClient(host=host, port=port, org=org)
        self.tz = tz

    def mapping(self, e):
        """
        the map function transforms a Point as dict to a string for POSTing to InfluxDb
        """
        return f"""{e["systemId"]},sensorId={e["sensorId"]} \
logType="{e["logType"]}",\
message="{e["message"]}",\
rawValue={e["rawValue"]},\
calcValue={e["calcValue"]} \
{e["timestamp"]}"""
        

    def add(self, logType, sensorId, message, rawValue=0.0, calcValue=None):
        """
        Post/insert a new entry in the queue
        """
        point = { "systemId": self.data["systemId"]}      
        point["timestamp"] = time_ns()+ticks_us()-self.tz*3_600_000_000_000
        point["logType"], point["sensorId"], point["message"] = logType, sensorId, message
        point["rawValue"] = float(rawValue)
        point["calcValue"] = float(calcValue or rawValue)
        self.logEntries.append(point)   # .enqueue(point)
        print("Point timestamp:", point["timestamp"])
#         print("point=", point, "Q length:", len(self.logEntries))
#         print("peek", self.logEntries.peek())

    def push(self, bucket="Pico"):
        """
        Send log entry points to InfluxDB database
        """
        if not self.logEntries: return
        data = []
        print(len(self.logEntries), "points in Q to send to InfluxDb...", end="")
        while self.logEntries:
#             print("len=", len(self.logEntries))
            point = self.logEntries.popleft()  #  .dequeue()
#             print("before Data point:", point, "len=", len(self.logEntries))
            data.append(self.mapping(point))
#             print("after Data point:", self.mapping(point), "len=", len(self.logEntries))

        # call InfluxDB API
        res = self.dbLogs.write_api(bucket=bucket, records=data)
        print("API response code:", res.status_code)
        if res.status_code >= 300:
            print(f"Error calling {self.dbLogs.url}/write?db={bucket}")
            print(res.json())

if __name__ == "__main__":
    from uwifi import uWifi
    from ntp import setClock
    from time import localtime, time, gmtime
    
    wlan = uWifi()
    print(f"1 - gmtime: {gmtime()} <> localtime: {localtime()}  <>  Unix: {time()}")
    setClock()
    print(f"2 - gmtime: {gmtime()} <> localtime: {localtime()}  <>  Unix: {time()}")
    
    
    print("time_ns:", time_ns())
    print("ticks_us:", ticks_us())
    print("time_ns()+ticks_us():", time_ns()+ticks_us())
    tz = 8
    print("time_ns()+ticks_us() to GMT:", time_ns()+ticks_us()-tz*3_600_000_000_000)