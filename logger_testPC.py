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
from datetime import datetime, timezone
from collections import deque
# from json import dumps
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
# import firebase_admin
# from firebase_admin import credentials
# from firebase_admin import db



class Logger:
    """
    Connectivity with the Firebase Realtime database
    Offer helpers to add or retrieve log entries
    """
    data = {
        "timestamp": None,
        "logType": "INFO",
        "systemId": None,
        "sensorId": None,
        "message": "",
        "rawValue": 0.0,
        "calcValue": 0.0
    }
    logEntries = deque((), 10_000)  #  FIFO queue

    def __init__(self, systemId):
        # connects to the database
        # identfies the system either by a given name or by its mac address
        self.data["systemId"] = systemId
        self.dbLogs = None

    def add(self, logType, sensorId, message, rawValue=0.0, calcValue=None):
        """
        Post/insert a new entry in the systemId table of the Firebase RT database
        """
        le = self.data
        le["timestamp"] = datetime.now(timezone.utc).isoformat()[:-6]+'Z'  # replace +00:00 by Z
        le["logType"], le["sensorId"], le["message"] = logType, sensorId, message
        le["rawValue"] = rawValue
        le["calcValue"] = calcValue if calcValue is not None else rawValue
        jsonSelf = le  #dumps(le)
        print(jsonSelf)
        self.logEntries.append(jsonSelf)

    def connect_influxDb(self, host="localhost", port="8086", token=None):
        """Connect to the database"""
        InfluxToken = token or "lfpFxGZ06BGjgiHZEqFyArU2p7FBHAnOtNzPak0HZT1hPCxv1eYA50c7XUorKRUoimFhL839PRVA3antbZeKEw=="
        self.dbLogs = InfluxDBClient(url=f"http://{host}:{port}", token=InfluxToken, org="Perso")
        self.dbLogs.map = lambda e: {
                                        "measurement": e["systemId"],
                                        "tags": {'sensorId': e["sensorId"]},
                                        "fields":{
                                            'logType': e["logType"],
                                            'timestamp': e["timestamp"],
                                            'message': e["message"],
                                            'rawValue': float(e["rawValue"]),
                                            'calcValue': float(e["calcValue"])
                                        }
                                    }

    # def connect_firebase(self):
    #     # Fetch the service account key JSON file contents
    #     cred = credentials.Certificate('picologger-71ff9-firebase-adminsdk-uygcx-7e36ac05a3.json')
    #     # Initialize the app with a service account, granting admin privileges
    #     firebase_admin.initialize_app(cred, {
    #         'databaseURL': 'https://picologger-71ff9-default-rtdb.asia-southeast1.firebasedatabase.app/'
    #     })
    #     self.dbLogs = db.reference(self.data["systemId"])

    def push(self):
        if self.dbLogs is None:
            self.connect_influxDb()
        data = []
        while log.logEntries:
            entry = log.logEntries.popleft()
            data.append(self.dbLogs.map(entry))

        print(data)
        # write_api = self.dbLogs.write_api(write_options=SYNCHRONOUS)
        with self.dbLogs as client:
            with client.write_api(write_options=SYNCHRONOUS) as writer:
                writer.write(
                    bucket="Pico",
                    record=data
                )
        # res = self.dbLogs.write_api(bucket="Pico", record=data)
        # print("dta sent to influxDb:", res)

        # new_entry = log.dbLogs.push(entry)  #  firebase
        # print("new log in Firebase", new_entry.key)

if __name__ == "__main__":
    from random import uniform
    SYSID = "mySysId"
    SENSOR = "sensor1"
    log = Logger(SYSID)
    print(len(log.logEntries), bool(log.logEntries))
    log.add("INFO", SENSOR, "testing the logger", 1, round(uniform(0, 5.0), 2))
    print(len(log.logEntries), bool(log.logEntries))
    # send to Firebase
    log.push()
    # check that data
    query=f"""from(bucket: "Pico")
|> range(start: -90m)
|> filter(fn: (r) => r["_measurement"] == "{SYSID}")
|> filter(fn: (r) => r["sensorId"] == "{SENSOR}")"""

    log.connect_influxDb()
    result = log.dbLogs.query_api().query(org='Perso', query=query)
    results = []
    for table in result:
        for record in table.records:
            results.append((record.get_field(), record.get_value()))
    print("-" * 80)
    print(results)


    # with dbLogs as client:
    #     with client.query_api() as reader:
    #         tables = reader.query(org='Perso', query=query)
    # tables = log.dbLogs.query_api().query(org='Perso', query=query)
    # # Serialize to values
    # output = tables.to_values(columns=['sensorId', 'calcValue'])
    # print(output)



