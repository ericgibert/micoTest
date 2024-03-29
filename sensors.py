"""
Declaration of all the sensors that will be interacting with the micro-controller
in this project.
"""
from utime import time
from machine import Pin, ADC
from micropython import const
from dht import DHT11, DHT22

class Sensor:
    id = "1234"         # sensorId
    rawValue = 0.0
    calcValue = 0.0

    def __init__(self, id):
        self.id = id

    def read(self):
        """default behaviour: calcValue is returned"""
        return self.calcValue

    def calculate(self):
        """default formula is simply using the rawValue for the calculated one"""
        self.calcValue = self.rawValue

    def __str__(self):
        """representation"""
        return f"Sensor({self.id})"

#
# ----  Sensor for reading the level of moisture in the soil
# ----  MAker Soil Moisture Sensor
#
WET_READ = const(27803.7)
DRY_READ = const(45675.9)
class MakerSoilMoisture(Sensor):
    """
    LED Turn On Output Voltage @VCC = 3.3V
                        Min     Max
        Blue (WET)      1.4     1.8V        Reading:  27803
        Green (MOIST)   1.8     2.1V
        Red (DRY)       2.1     2.3V        Reading:  45676
    https://sg.cytron.io/p-maker-soil-moisture-sensor?r=1
    """
    def __init__(self, id, pin):
        Sensor.__init__(self, id)
        self._adc = ADC(Pin(pin))

    def calculate(self):
        """transform the reading in Volt into the moisture %"""
        calcValue = (DRY_READ - self.rawValue) * 100.0 / (DRY_READ - WET_READ)
        return min(100.0, max(0.0, calcValue))

    def read(self):
        self.rawValue = self._adc.read_u16()
        self.calcValue = self.calculate()
        return self.calcValue

class DHT:
    """
    Supports both DHT11 and DHT 22
    Since the sensor captures both air temperature and humidity, one reading is performed
    """
    lastRead = time() - 4
    def __init__(self, id, serie, pin):
        """
        serie: either 11 or 22 to choose between DHT11 and DHT22
        """
        self.dht = DHT11(Pin(pin)) if serie == 11 else DHT22(Pin(pin))
        self.DHTT = Sensor(f"{id}_T")
        self.DHTH = Sensor(f"{id}_H")

    def read(self):
        """
        Only read if the last read was done 3 seconds ago
        """
        if time() - self.lastRead > 3:
            try:
                self.dht.measure()
                self.DHTT.rawValue = self.DHTT.calcValue = self.dht.temperature()
                self.DHTH.rawValue = self.DHTH.calcValue = self.dht.humidity()
            except OSError as err:
                pass
            else:
                self.lastRead = time()

    @property
    def temperature(self):
        return self.DHTT.calcValue

    @property
    def humidity(self):
        return self.DHTH.calcValue

if __name__ == "__main__":
    acds = (MakerSoilMoisture("ACD0", 26), MakerSoilMoisture("ACD1", 27), MakerSoilMoisture("ACD2", 28))
    for s in acds:
        moisture = s.read()
        print(s.id, s.rawValue, f"{moisture}%")

    dht = DHT("DHT", 11, 15)
    dht.read()
    print("temperature:", dht.temperature)
    dht.read()
    print("humidity:", dht.humidity)