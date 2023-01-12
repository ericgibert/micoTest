# testing internet connection
# looking for different SSID thru a hidden file
from micropython import const
from machine import Pin, ADC
import time
import network
from ssids import SSIDs
from display import Display
from dht import DHT11
from state import State

onboard_led = Pin("LED", Pin.OUT)

def connect_to_WIFI():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    for SSID, PASSWORD in SSIDs:
        print("SSID ", SSID)
        wlan.connect(SSID, PASSWORD)
        # Wait for connect or fail
        max_wait = 10
        while max_wait > 0:
            if wlan.status() < 0 or wlan.status() >= 3:
                break
            max_wait -= 1
            print('waiting for connection...')
            time.sleep(1)
        
        
        if wlan.isconnected(): return wlan
    return None


from time import sleep, localtime
dis = Display(0, 17, 16)

now = localtime()

wlan = connect_to_WIFI()
if wlan:
    print("Connected:", wlan.ifconfig())
else:
    print ("Trying to connect")


# buzzer and DHT11
sensor = DHT11(Pin(15))
buzzer = Pin(12, Pin.OUT)

# the 4 buttons around the screen
NB_BUTTONS = const(4)
buttons = [Pin(i, Pin.IN, Pin.PULL_DOWN) for i in range(NB_BUTTONS)]
lastValues = [-1] * NB_BUTTONS

# the 4 ACDs
NB_ACDS = const(3)
acds = [ADC(Pin(26)), ADC(Pin(27)), ADC(Pin(28))]
min_moisture=const(0)
max_moisture=const(65535)

state = State(99)   # to display HOME screen and get back to it after 5 seconds

def allReleased():
    """
        Wait that all the buttons are realsed - biounce effect
    """
    while sum([b.value() for b in buttons]):
        sleep(0.05)

while True:
    sleep(0.1)
    for i, button in enumerate(buttons):
        if button.value() != lastValues[i]:
            lastValues[i] = button.value()
            print(f"B{i} = {lastValues[i]}")
    
#     if state.lastState != state.currentState:
#         print(state)

    if state.currentState == 0:
        # default waiting state to wait for button to be pressed
        if lastValues[0]:
            firstTime = True
            state.changeTo(1)
        elif lastValues[1]:
            firstTime = True
            state.changeTo(2)
        elif lastValues[2]:
            firstTime = True
            state.changeTo(3)
        elif lastValues[3]:
            firstTime = True
            state.changeTo(4)
            
        # wait for button to be released
        allReleased()
    
    elif state.currentState == 1:
        if firstTime:
            dis.multiLines("Press any button")
            firstTime = False
        if sum(lastValues) > 0:
            # a button is pressed: let's go back to main screen
            state.changeToDefault()
    
    elif state.currentState == 2:
        if firstTime:
            raw_value = acds[0].read_u16()
            moisture = (max_moisture - raw_value) * 100 // (max_moisture - min_moisture)
            dis.screen(f"""{moisture}% moisture\n{raw_value}""",
                       button3="Read", button4="HOME")
            firstTime = False
        if lastValues[3]:
            # button4: let's go back to main screen
            state.changeToDefault()
        elif lastValues[2]:
            firstTime = True
    
    elif state.currentState == 3:
        if firstTime:
            dis.screen("Press STOP", button3="STOP")
            buzzer.on()
            firstTime = False
        if lastValues[2]:
            # button3: let's go back to main screen
            buzzer.off()
            state.changeToDefault()
   
    elif state.currentState == 4:
        if firstTime:
            now = localtime()
            sensor.measure()
            temperature = sensor.temperature()
            humidity=sensor.humidity()
            dis.screen(f"""{now[3]}:{now[4]:02}:{now[5]:02}
Temp: {temperature}C
Humidity: {humidity}%""", button4="Home")
            firstTime = False
        if lastValues[3]:
            # button4: let's go back to main screen
            state.changeToDefault()
   
    elif state.currentState == 99:
        # display the HOME screen and go to waiting a press (state = 0)
        dis.screen(f"""{now[0]}-{now[1]:02}-{now[2]:02}
{now[3]}:{now[4]:02}:{now[5]:02}
Connected to
{wlan.config("ssid")}""",
button1="1", button2="2",button3="3", button4="4")
        state.changeTo(0)
        allReleased()
        