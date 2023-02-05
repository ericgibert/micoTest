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
from json import dumps
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db


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
        jsonSelf = dumps(le)
        print(jsonSelf)
        self.logEntries.append(jsonSelf)

    def connect_firebase(self):
        # Fetch the service account key JSON file contents
        cred = credentials.Certificate('picologger-71ff9-firebase-adminsdk-uygcx-7e36ac05a3.json')
        # Initialize the app with a service account, granting admin privileges
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://picologger-71ff9-default-rtdb.asia-southeast1.firebasedatabase.app/'
        })
        self.dbLogs = db.reference(self.data["systemId"])

    def push(self):
        if self.dbLogs is None:
            self.connect_firebase()
        while log.logEntries:
            entry = log.logEntries.popleft()
            new_entry = log.dbLogs.push(entry)
            print("new log in Firebase", new_entry.key)

if __name__ == "__main__":
    log = Logger("mySysId")
    print(len(log.logEntries), bool(log.logEntries))
    log.add("INFO", "sensor 1", "testing the logger", 1, 3.0)
    print(len(log.logEntries), bool(log.logEntries))
    # send to Firebase
    log.push()




