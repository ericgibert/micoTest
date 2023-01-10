# testing internet connection
# looking for different SSID thru a hidden file
import network
from machine import Pin, Timer, I2C
import time
from ssids import SSIDs
from ssd1306_helper import Display

onboard_led = Pin("LED", Pin.OUT)

def connect_to_WIFI():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    for SSID, PASSWORD in SSIDs:
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
while True:
    now = localtime()
    dis.multiLines(f"""{now[0]}-{now[1]:02}-{now[2]:02}
{now[3]}:{now[4]:02}:{now[5]:02}""")
    
    wlan = connect_to_WIFI()
    if wlan:
        print("Connected:", wlan.ifconfig())
    else:
        print ("Trying to connect")
    
    
sleep(1)