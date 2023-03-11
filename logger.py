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
# from collections import deque
import urequests
from utime import time_ns, ticks_us
from FIFOqueue import FIFOQueue

class uInfluxDBClient():
    """
    Small wrapper to send data to a remote InfluxDB
    WIFI Network connection must already be established
    """
    def __init__(self, url, org, token=None):
        """
        Save the parameters for future calls
        """
        self.url, self.org = url, org
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
    logEntries = FIFOQueue()  # deque((), 1000)  #  FIFO queue accepting 3000 pending readings

    def __init__(self, systemId, host="192.168.18.3", port="8086", org="Perso"):
        # connects to the database hosted on http://host:port
        # systemId: identfies the system either by a given name or by its mac address
        #			this will be a measurement/database for InfluxDb
        self.data["systemId"] = systemId
        self.dbLogs = uInfluxDBClient(url=f"http://{host}:{port}", org=org)

    def map(self, e):
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
        le = self.data
        le["timestamp"] = time_ns()+ticks_us()
        le["logType"], le["sensorId"], le["message"] = logType, sensorId, message
        le["rawValue"] = float(rawValue)
        le["calcValue"] = float(calcValue if calcValue is not None else rawValue)
        self.logEntries.enqueue(le)
        print("le=", le, "Q length:", len(self.logEntries))

    def push(self, bucket="Pico"):
        """
        Send log entry points to InfluxDB database
        """
        data = []
        while self.logEntries:
            print("len=", len(self.logEntries))
            point = self.logEntries.dequeue()
            data.append(self.map(point))
            print("Data point:", self.map(point), "len=", len(self.logEntries))
        if data:
            res = self.dbLogs.write_api(bucket=bucket, records=data)
            print("API uRequest:", res.status_code)
            print(data)
            if res.status_code >= 300:
                print(f"Error calling {self.dbLogs.url}/write?db={bucket}")
                print(res.json())
