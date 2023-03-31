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
import time
from collections import deque
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from flightsql import FlightSQLClient
from ssids import influxDBsecrets, LOCALTZ

class Logger:
    """
    Connectivity with the Firebase Realtime database
    Offer helpers to add or retrieve log entries
    """
    point = {
        "timestamp": 1679738601965652859,   # timestamp when the data are given to the Logger ==> time in influxDb
        "logType": "DATA",                  # INFO, WARNING, ERROR, DATA (default)
        "systemId": "28:cd:c1:07:e5:d5",    # influxDB measurement/database: one per system or PicoW
        "sensorId": "ACD2",                 # influxDB Tag/key for one sensor reading by the PicoW
        "message": "moisture in geranium pot",  # influxDB data field: description of this sensor
        "rawValue": 46331.0,        # influxDB data field: raw value when PicoW reads the sensor or the PIN
        "calcValue": 29.0           # influxDB data field: converted raw value to proper value or same a raw if no conversion applies
    }
    logEntries = deque((), 10_000)  #  FIFO queue

    def __init__(self, systemId):
        # connects to the database
        # identifies the system either by a given name or by its mac address
        self.point["systemId"] = systemId
        self.dbLogs = InfluxDBClient(url=influxDBsecrets["url"],
                                     token=influxDBsecrets["token"],
                                     org=influxDBsecrets["org"])
        self.dbLogs.bucket = influxDBsecrets["bucket"]

    def add(self, logType, sensorId, message, rawValue=0.0, calcValue=None):
        """
        Post/insert a new entry in the systemId table of the Firebase RT database
        PRAJNA,sensorId=TestPC logType="DATA",message="testing the posting of a point",rawValue=1.23,calcValue=4.56 1679723496728941000
        """
        point = {
            "systemId": self.point["systemId"],
            "timestamp": int(time.time() * 1_000_000_000), # nanosecond
            "logType": logType,
            "sensorId": sensorId,
            "message": message,
            "rawValue": float(rawValue),
            "calcValue": float(calcValue if calcValue is not None else rawValue)
        }
        self.logEntries.append(point)   # .enqueue(point)
        print("Point timestamp:", point["timestamp"])

    def mapping(self, e):
        """
        Transforms Logger instance into an InfluxDb Point dictionary
        """
        return {
            "measurement": e['systemId'],
            "time": e["timestamp"],
            "tags": { "sensorId": e["sensorId"]},
            "fields": {
                "rawValue": e["rawValue"],
                "calcValue": e["calcValue"],
                "message": e["message"],
                "logType": e["logType"]
            }
        }

    def toLineProtocol(self, influxPoint):
        """
        Serialize an InfluxDb Point dictionary into one line protocol string
        """
        _tags = ",".join([f'{k}="{v}"' for k,v in influxPoint["tags"].items()])
        _fields = ",".join([f'{k}="{v}"' if isinstance(v, str) else f'{k}={v}' for k, v in influxPoint["fields"].items()])
        return f"""{influxPoint["measurement"]},{_tags} {_fields} {influxPoint["time"]}"""

    def push(self, bucket=None):
        if not self.logEntries: # or self.dbLogs.health_api() != 200:
            return
        data = []
        print(len(self.logEntries), "points in Q to send to InfluxDb...", end="")
        while self.logEntries:
            #             print("len=", len(self.logEntries))
            point = self.logEntries.popleft()  # .dequeue()
            #             print("before Data point:", point, "len=", len(self.logEntries))
            data.append(self.mapping(point))
            print("after Data point:", self.mapping(point), "len=", len(self.logEntries))

        # call InfluxDB API
        # status_code = self.dbLogs.write(bucket=bucket or self.dbLogs.bucket, records=data)
        write_api = self.dbLogs.write_api(SYNCHRONOUS)
        status_code = write_api.write(bucket=bucket or self.dbLogs.bucket, record=data)
        print("API response code:", status_code)
        # if status_code >= 300:
        #     print(f"Error calling {self.dbLogs.url}/write?db={bucket or self.dbLogs.bucket}")

        # new_entry = log.dbLogs.push(entry)  #  firebase
        # print("new log in Firebase", new_entry.key)

if __name__ == "__main__":
    # write data in influxDB
    log = Logger("PRAJNA")
    log.add("DATA", "TestPC", "testing the posting of a point", 1.23, 4.56)
    e = log.logEntries[0]
    point = log.mapping(e)
    print("Point dico:", point)
    line = log.toLineProtocol(point)
    print("As Line Protocol:", line)
    log.push()
    # query data from InfluxDb
    query = f"""SELECT *
    FROM 'PRAJNA'
    WHERE time >= now() - interval '2 hours'"""
    # AND ('bees' IS NOT NULL OR 'ants' IS NOT NULL)"""

    # Define the query client
    query_client = FlightSQLClient(
        host=influxDBsecrets["host"],
        token=influxDBsecrets["token"],
        metadata={"bucket-name": influxDBsecrets['bucket']})

    # Execute the query
    info = query_client.execute(query)
    reader = query_client.do_get(info.endpoints[0].ticket)

    # Convert to dataframe
    point = reader.read_all()
    df = point.to_pandas().sort_values(by="time")
    print(df)

#     from random import uniform, seed
#     seed()
#     SYSID = "mySysId"
#     SENSOR = "sensor1"
#     log = Logger(SYSID)
#     print(len(log.logEntries), bool(log.logEntries))
#     log.add("INFO", SENSOR, "testing the logger", 1, round(uniform(0, 5.0), 2))
#     print(len(log.logEntries), bool(log.logEntries))
#     # send to database
#     log.push()
#     # check that data
#     query=f"""from(bucket: "Pico")
# |> range(start: -90m)
# |> filter(fn: (r) => r["_measurement"] == "{SYSID}")
# |> filter(fn: (r) => r["sensorId"] == "{SENSOR}")"""
#
#     log.connect_influxDb()
#     result = log.dbLogs.query_api().query(org='Perso', query=query)
#     results = []
#     for table in result:
#         for record in table.records:
#             results.append((record.get_field(), record.get_value()))
#     print("-" * 80)
#     print(results)


    # with dbLogs as client:
    #     with client.query_api() as reader:
    #         tables = reader.query(org='Perso', query=query)
    # tables = log.dbLogs.query_api().query(org='Perso', query=query)
    # # Serialize to values
    # output = tables.to_values(columns=['sensorId', 'calcValue'])
    # print(output)



