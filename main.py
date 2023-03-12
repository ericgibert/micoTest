# testing internet connection
# looking for different SSID thru a hidden file
from micropython import const
from machine import Pin, ADC
from time import sleep, localtime
from ntp import setClock
from uwifi import uWifi
from display import Display
from dht import DHT11
from state import State
from logger import Logger

# pins and hardware definitions
onboard_led = Pin("LED", Pin.OUT)
dis = Display(0, 17, 16) # ic2 port and pins for the mini LCD display
# the 4 buttons around the screen
NB_BUTTONS = const(4)
buttons = [Pin(i, Pin.IN, Pin.PULL_DOWN) for i in range(NB_BUTTONS)]
lastValues = [-1] * NB_BUTTONS
# the 3 ACDs
NB_ACDS = const(3)
acds = [ADC(Pin(26)), ADC(Pin(27)), ADC(Pin(28))]  # pico's ACD pins
min_moisture = const(0)
max_moisture = const(65535)
# buzzer and DHT11
buzzer = Pin(12, Pin.OUT)
sensor = DHT11(Pin(15))

DAYS=const( ('MON', "TUE", "WED", "THU", "FRI", 'SAT', "SUN") )

# first connection to WIFI
wlan = uWifi(dis)
if wlan:
    print("Connected:", wlan.ifconfig())
    setClock(tz=+8)  #  need to better manage timezone, for now, clock is TZ ignorant
    print("my MAC address:", wlan.mac)
    log = Logger(wlan.mac, tz=+8)  #  MAC address used a systemId i.e. InfluxDb database
else:
    print("Failed to connect any Wifi SSIDs")

now = localtime()
print("Local time:", now)

def allReleased():
    """
        Wait for all the buttons to be released - prevents bounce effect
    """
    while sum([b.value() for b in buttons]):
        sleep(0.05)


state = State(99)  # 99 to display HOME screen as default screen
refresh = 0
while True:
    sleep(0.1)
    for i, button in enumerate(buttons):
        if button.value() != lastValues[i]:  #  look for button havong changed i.e. pressed vs released
            lastValues[i] = button.value()
            print(f"B{i} = {lastValues[i]}")

    # Automation based on states
    if state.currentState == 0:
        # default waiting state: act on a pressed button to change state
        if lastValues[0]:   # Btn1 is pressed
            state.changeTo(1)
        elif lastValues[1]: # Btn2 is pressed
            state.changeTo(2)
        elif lastValues[2]: # Btn3 is pressed
            state.changeTo(3)
        elif lastValues[3]: # Btn4 is pressed
            state.changeTo(4)
        else:
            if refresh >= 5:
                state.changeTo(99)  # once in a while, refresh the screen for time display
                refresh = 0
            else:
                refresh += 1
        # else ensure that all buttons are released
        allReleased()

    # Action for button 1
    elif state.currentState == 1:  # look for a WIFI connection
        if state.firstTime:
            wlan = uWifi(dis)
            state.firstTime = False
        if sum(lastValues) > 0:
            # a button is pressed: let's go back to main screen
            state.changeToDefault()

    # Action for button 2
    elif state.currentState == 2:  #  display the readings of all ACDs for moisture
        if state.firstTime:
            mLines = ""
            for i, acd in enumerate(acds):
                raw_value = acd.read_u16()
                moisture = (max_moisture - raw_value) * 100 // (max_moisture - min_moisture)
                mLines += f"""{i}: {moisture}% [{raw_value}]\n"""
                log.add("DATA", f"ACD{i}", "moisture", raw_value, moisture)
            dis.screen(mLines,
                       title="Moisture",
                       button3="Read", button4="HOME")
            state.firstTime = False
        if lastValues[3]:   # button4: let's go back to main screen
            state.changeToDefault()
        elif lastValues[2]: # press on BTN3 -->  read again
            state.firstTime = True
            allReleased()

    # Action for button 3
    elif state.currentState == 3:  #  buzzer - force push all logs to InfluxDb
        if state.firstTime:
            dis.screen("Press STOP", button3="STOP")
            buzzer.on()
            state.firstTime = False
        if lastValues[2]:  # button3: let's go back to main screen
            buzzer.off()
            state.changeTo(98) # send data if any to InfluxDb
#             if wlan: log.push()
#             state.changeToDefault()

    # Action for button 4
    elif state.currentState == 4:  #  read data from DHT11
        if state.firstTime:
            now = localtime()
            try:
                sensor.measure()
            except OSError as err:
                continue
            temperature = sensor.temperature()
            humidity = sensor.humidity()
            dis.screen(f"""{now[3]}:{now[4]:02}:{now[5]:02}
Temp: {temperature}C
Humidity: {humidity}%""", button3="Read", button4="Home")
            log.add("DATA", "DHT11T", "temperature", temperature)
            log.add("DATA", "DHT11H", "humidity", humidity)
            state.firstTime = False
        if lastValues[3]:    # button4: let's go back to main screen
            state.changeToDefault()
        elif lastValues[2]: # press on BTN3 -->  read again
            state.firstTime = True
            allReleased()

    # request to send data to InfluxDb
    elif state.currentState == 98:
        if wlan: log.push()
        state.changeToDefault()

    # default action
    elif state.currentState == 99:   # display the HOME screen and go to waiting a press (state = 0)
        now = localtime()
        dis.screen(f""" {now[0]}-{now[1]:02}-{now[2]:02} {DAYS[now[6]]}
 {now[3]}:{now[4]:02}:{now[5]:02}
 Connected to
 {wlan.ssid or "None"}""", footer=f"{len(log.logEntries)}",
                   button1="Wifi", button2="ACD", button3="Buzz", button4="DHT")
#         if wlan: log.push()
        state.changeTo(0)
        allReleased()

