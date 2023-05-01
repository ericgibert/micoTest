"""
I AM THIRSTY!

Application to monitor the moisture level in the soil of 3 plants.
- Readings are uploaded in InfluxDB database
- Other sensor: DHT for air temperature and humidity
"""
from micropython import const
from machine import Pin, Timer
from time import sleep, localtime
# import _thread
import gc

from ntp import setClock
from uwifi import uWifi
from display import Display
from sensors import MakerSoilMoisture, DHT
from state import State
from logger import Logger

# pins and hardware definitions
onboard_led = Pin("LED", Pin.OUT)
# ic2 port and pins for the mini LCD display
dis = Display(0, 17, 16)
# the 4 buttons around the screen
NB_BUTTONS = const(4)
buttons = [Pin(i, Pin.IN, Pin.PULL_DOWN) for i in range(NB_BUTTONS)]
lastValues = [-1] * NB_BUTTONS
# the 3 ACDs and DHT11
acds = (MakerSoilMoisture("ACD0", 26), MakerSoilMoisture("ACD1", 27), MakerSoilMoisture("ACD2", 28))
airSensor = DHT("DHT11", 11, 15)
# buzzer
buzzer = Pin(12, Pin.OUT)

DAYS = const(('MON', "TUE", "WED", "THU", "FRI", 'SAT', "SUN"))
wlan = None


def connectWifi():
    """
    Connection to Wifi
    Get localtime to the Pico's clock
    Need to do a full reset on current Wifi to start a fresh connection
    """
    global wlan
    onboard_led.on()
    wlan = uWifi(dis)
    if wlan:
        print("Connected:", wlan.ifconfig())
    else:
        print("Failed to connect any Wifi SSIDs")


def disconnectWifi():
    global wlan
    try:
        # wlan._wlan.active(False)
        wlan._wlan.disconnect()
    except:
        pass
    finally:
        onboard_led.off()


connectWifi()
try:
    setClock(tz=+8)  # need to better manage timezone, for now, clock is TZ ignorant
except:
    pass
print("my MAC address:", wlan.mac)
log = Logger(wlan.mac, tz=+8)  # MAC address used a systemId i.e. InfluxDb database
now = localtime()
print("Local time:", now)
disconnectWifi()


# start a second thread to send data thru Wifi automatically
def core1_sendData(timer=None):
    if len(log.logEntries) > 0:
        print("Core1 thread...")
        connectWifi()
        log.push()
        disconnectWifi()
        print("Data sent")
        gc.collect()


def goto98(timer):
    global state
    state.changeTo(98)


# second_thread = _thread.start_new_thread(core1_sendData, ())
# second_thread = Timer(mode=Timer.PERIODIC, period= (10 * 60 + 30) * 1000, callback=goto98)  #core1_sendData)

def allReleased():
    """
        Wait for all the buttons to be released - prevents bounce effect
    """
    while sum([b.value() for b in buttons]):
        sleep(0.05)


buttonPressed = None


def getButtons():
    """
    Check all 4 buttons and set the global variable if a button is pressed
    """
    global lastValues, buttonPressed
    for i, button in enumerate(buttons):
        btn = button.value()
        if btn != lastValues[i]:
            lastValues[i] = btn
            if btn:
                buttonPressed = i + 1  # button 1 to 4
                print("Pressed on", buttonPressed)
            else:
                print("Button", buttonPressed, "released")
                buttonPressed = None


state = State(99)  # 99 to display HOME screen as default screen
refresh = 0
while True:
    sleep(0.1)
    getButtons()
    # Automation based on states
    if state.currentState == 0:
        # default waiting state: act on a pressed button to change state
        if buttonPressed:
            state.changeTo(buttonPressed)
        else:
            if refresh >= 5:
                state.changeTo(99)  # once in a while, refresh the screen for time display
                refresh = 0
            else:
                refresh += 1

    # Action for button 1: look for a WIFI connection
    elif state.currentState == 1:
        if state.firstTime:
            # wlan = uWifi(dis)
            connectWifi()
            state.firstTime = False
        elif buttonPressed:
            # a button is pressed
            state.changeTo(98)  # send data if any to InfluxDb

    # Action for button 2: display the readings of all ACDs for moisture
    elif state.currentState == 2:
        if state.firstTime:
            mLines = ""
            for i, acd in enumerate(acds):
                moisture = acd.read()
                mLines += f"""{i}: {moisture}% [{acd.rawValue}]\n"""
                log.add("DATA", acd.id, "moisture", acd.rawValue, moisture)
            dis.screen(mLines,
                       title="Moisture",
                       button3="Read", button4="HOME")
            state.firstTime = False
        elif buttonPressed == 4:  # button4: let's go back to main screen
            state.changeToDefault()
        elif buttonPressed == 3:  # press on BTN3 -->  read again
            state.firstTime = True
            allReleased()

    # Action for button 3: buzzer - force push all logs to InfluxDb
    elif state.currentState == 3:
        if state.firstTime:
            dis.screen("Press STOP", button3="STOP")
            buzzer.on()
            state.firstTime = False
        elif buttonPressed == 3:  # button3: let's go back to main screen
            buzzer.off()
            state.changeTo(98)  # send data if any to InfluxDb

    # Action for button 4: read data from DHT11
    elif state.currentState == 4:
        if state.firstTime:
            now = localtime()
            try:
                airSensor.read()
            except OSError as err:
                continue
            temperature = airSensor.DHTT.read()
            humidity = airSensor.DHTH.read()
            dis.screen(f"""{now[3]}:{now[4]:02}:{now[5]:02}
Temp: {temperature}C
Humidity: {humidity}%""", button3="Read", button4="Home")
            log.add("DATA", airSensor.DHTT.id, "temperature", temperature)
            log.add("DATA", airSensor.DHTH.id, "humidity", humidity)
            state.firstTime = False
        elif buttonPressed == 4:  # button4: let's go back to main screen
            state.changeToDefault()
        elif buttonPressed == 3:  # press on BTN3 -->  read again
            state.firstTime = True
            allReleased()

    # request to send data to InfluxDb
    elif state.currentState == 98:
        if len(log.logEntries) > 0:
            if not wlan:
                connectWifi()
            if wlan:
                dis.screen(f"Sending {len(log.logEntries)} pts")
                http_code = log.push()
                if http_code >= 300:
                    dis.screen(f"""Failed to send.\nEnQ {len(log.logEntries)} pts""")
                    sleep(3)
            else:
                dis.screen(f"""No internet\n{len(log.logEntries)} pts in Q""")
                sleep(2)
            disconnectWifi()
            gc.collect()
        state.changeToDefault()

    # default action
    elif state.currentState == 99:  # display the HOME screen and go to waiting a press (state = 0)
        now = localtime()
        dis.screen(f""" {now[0]}-{now[1]:02}-{now[2]:02} {DAYS[now[6]]}
 {now[3]}:{now[4]:02}:{now[5]:02}
 Connected to
 {wlan.ssid or "None"}""", footer=f"{len(log.logEntries)}",
                   button1="Wifi", button2="ACD", button3="Buzz", button4="DHT")
        #         if wlan: log.push()
        state.changeTo(0)
        allReleased()
