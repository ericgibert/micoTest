"""
Logger for the application into InfluxDb time-serie Database

Every Log entry will have the following structure:
- timestamp: the moment the data was collected ; Unix timestamp in nanosecond
- logType: INFO, WARNING, ERROR, DATA
- systemId: a free name to identify the system generating the logs ; PicoW mac is used
- sensorId: a sensor belonging to the system
- message: free text
- rawValue: the value obtained from the sensor, as a real number
- calcValue: the result of a calculation from the raw value to convert the raw value to the final value

"""
from micropython import const
from collections import deque
import urequests
import socket
from utime import time_ns, ticks_us
from ssids import influxDBsecrets, LOCALTZ


class uInfluxDBClient():
    """
    Small wrapper to send data to a remote InfluxDB
    WIFI Network connection must already be established
    """
    def __init__(self, org=None, url=None, host=None, port=None, token=None):
        """
        Save the parameters for future calls
        Mandatory: either the url OR both host and port
        The influxDBsecrets dictionary helps to set the influxDb data safely in a Python file.
        Priority is given to the given parameters to this __init__ method, then to the values in influxDBsecrets
        """
        # mandatory ; either given as this method's parameters or from the module influxDBsecrets
        self.org = org or influxDBsecrets["org"]
        self.token = token or influxDBsecrets["token"]
        # optional
        self.host, self.port = host or influxDBsecrets.get('host'), int(port or influxDBsecrets.get('port', 8086))
        self.url = url or influxDBsecrets.get("url") or f"http://{self.host}:{self.port}"
        self.bucket = influxDBsecrets.get("bucket")

    def write_api(self, bucket, records):
        """
        bucket:  A created database in InfluxDb
        records: A list of points/data to write in this bucket/database expressed as line protocol string
        """
        url_write = f"{self.url}/write?db={bucket or self.bucket}"
        try:
            response = urequests.post(url_write,
                                  data="\n".join(records), timeout=5,
                                  headers={'Authorization': f'Token {self.token}'} if self.token else {})
            res = response.status_code
        except OSError as err:
            print("***", err)
            res = 500
        return res

    def health_api(self):
        """
        health check of the influxDb database access
        Only to be used for a local database
        using the socket library to check if the connection is not lost
        """
        # step 1: check the server is reachable
        try:
            s=socket.socket()
            s.settimeout(3)
            addr = socket.getaddrinfo(self.host, self.port)[0][-1]
            s.connect(addr)
        except OSError as err:
            print("Socket timeout", err)
            return 500
        finally:
            s.close()              
        # check the database is reachable
        url_health = f"{self.url}/health"
        try: 
            response = urequests.post(url_health, timeout=5,
                                  headers={'Authorization': f'Token {self.token}'} if self.token else {})
            res = response.status_code
        except OSError as err:
            print("error 10001:", err)
            res = 500
        return res


class Logger:
    """
    Connectivity with an influxDB hosted on a server
    Offer helpers to add or retrieve log entries
    """
    point = {
        "timestamp": 1679738601965652859,       #  timestamp when the data are given to the Logger ==> time in influxDb
        "logType": "DATA",                      #  INFO, WARNING, ERROR, DATA (default)
        "systemId": "28:cd:c1:07:e5:d5",        #  influxDB measurement/database: one per system or PicoW
        "sensorId": "ACD2",                     #  influxDB Tag/key for one sensor reading by the PicoW
        "message": "moisture in geranium pot",  #  influxDB data field: description of this sensor
        "rawValue": 46331.0,                    #  influxDB data field: raw value when PicoW reads the sensor or the PIN
        "calcValue": 29.0                       #  influxDB data field: converted raw value to proper value or same a raw if no conversion applies
    }
    

    def __init__(self, systemId, url=None, host=None, port=None, org=None, tz=0):
        """
        # connects to the database hosted on http://host:port
        # systemId: identifies the system either by a given name or by its mac address
        #           this will be a measurement/database for InfluxDb
        """
        self.logEntries = deque((), 1000)  #  FIFO queue accepting 1000 pending readings
        self.point["systemId"] = systemId
        self.dbLogs = uInfluxDBClient(url=url, host=host, port=port, org=org)
        self.tz = tz

    def mapping(self, e):
        """
        the map function transforms a Point as dict to a string for POSTing to InfluxDb
        i.e. the e dictionary to the line protocol string expected by influxDb:
        28:cd:c1:07:e5:d5,sensorId=ACD2 logType="DATA",message="moisture",rawValue=46331.0,calcValue=29.0 1679738601965652859
        """
        return f"""{e["systemId"]},sensorId={e["sensorId"]} \
logType="{e["logType"]}",\
message="{e["message"]}",\
rawValue={e["rawValue"]},\
calcValue={e["calcValue"]} \
{e["timestamp"]}"""
        

    def add(self, logType, sensorId, message, rawValue=0.0, calcValue=None):
        """
        Post/insert a new entry in the queue.
        The queue will hold up to 1000 data points expressed as a dictionary.
        creation of a local point variable to mask self.point --> prevent issue memory assignment
        """
        point = {
            "systemId": self.point["systemId"],
            "timestamp": time_ns() + ticks_us() - self.tz * 3_600_000_000_000,
            "logType": logType,
            "sensorId": sensorId,
            "message": message,
            "rawValue": float(rawValue),
            "calcValue": float(calcValue if calcValue is not None else rawValue)
        }
        self.logEntries.append(point)   # .enqueue(point)
        # print("Point timestamp:", point["timestamp"])  # for debugging, can be commented out later
        print("point=", point, "Q length:", len(self.logEntries)) # for debugging, can be commented out later


    def push_slice(self, bucket, slice_size=None):
        """Send 'slice_size' points to database"""
        slice_size = slice_size or len(self.logEntries)  # replace None by the current Q length
        data = []       # buffer for all converted points to send to influxDb with write_api
        safeguard = []  # keep the dequeued points to repost them if the API call fails
        for pt in range(slice_size):
            point = self.logEntries.popleft()  #  .dequeue()
            safeguard.append(point)
            data.append(self.mapping(point))
            print(f"Data point {len(self.logEntries)}: {self.mapping(point)}")
        # call InfluxDB API
        status_code = self.dbLogs.write_api(bucket=bucket, records=data)
        print("API response code:", status_code)
        if status_code >= 300:
            print(f"Error calling {self.dbLogs.url}/write?db={bucket}")
            for point in safeguard:
                self.logEntries.append(point)
        return status_code

    def push(self, bucket=None):
        """
        Send log entry points to InfluxDB database
        - WIFI connection must have been ensured before calling this method
        - abort if the queue is empty or if the connection with socket is not possible
        - if bucket is left to None then the bucket declared in the dbLogs will be used
        """
        if not self.logEntries: # or self.dbLogs.health_api() != 200:
            return
        # sending points 20 by 20 to avoid overloading the API's body
        print(len(self.logEntries), "points in Q to send to InfluxDb...")
        SLICE_SIZE = const(20)
        for slice in range(len(self.logEntries) // SLICE_SIZE):
            status_code = self.push_slice(bucket or self.dbLogs.bucket, SLICE_SIZE)
            if status_code >= 300:
                return status_code
        # push the remaining points below 20
        status_code = self.push_slice(bucket or self.dbLogs.bucket)
        return status_code
            


if __name__ == "__main__":
    from uwifi import uWifi
    from ntp import setClock
    from time import localtime, time, gmtime
    
    wlan = uWifi()
    print(f"1 - gmtime: {gmtime()} <> localtime: {localtime()}  <>  Unix: {time()}")
    setClock(LOCALTZ)
    print(f"2 - gmtime: {gmtime()} <> localtime: {localtime()}  <>  Unix: {time()}")
    
    # testing the different creation of a proper Unix timestamp at nanosecond level (default for InfluxdDb)
    print("time_ns:", time_ns())
    print("ticks_us:", ticks_us())
    print("time_ns()+ticks_us():", time_ns()+ticks_us())
    print("time_ns()+ticks_us() to GMT:", time_ns()+ticks_us()-LOCALTZ*3_600_000_000_000)

    print("=" * 50)
    idb = uInfluxDBClient()
    # print("Health status code:", idb.health_api())  # only when InfluxDb is on local LAN i.e. not InfluxDb CLoud
    print("=" * 50)
    log = Logger(wlan.mac, tz=LOCALTZ)
    log.add("DATA", "TestPC", "testing posting from PicoW", 1.23, 4.56)
    log.push()

