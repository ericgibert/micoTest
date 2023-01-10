# small python module to help manging thessd1306 OLED display
from micropython import const
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

WIDTH=const(128)
HEIGHT=const(64)
FONTSIZE=const(10)  #  code to improve when we can change the font size

class Display:
    def __init__(self, port, scl, sda, width=WIDTH, height=HEIGHT, freq=400000):
        i2c = I2C(port, scl=Pin(scl), sda=Pin(sda), freq=freq)
        self.display = SSD1306_I2C(width, height, i2c)

    def multiLines(self, lines, topMargin=0, leftMargin=0):
        """
        Display all the lines separated by a \n from top to bottom
        :param lines: list of str separeted by \n
        :param topMargin: top margin in pixel
        :param leftMargin: left margin in pixel
        :return:
        """
        self.display.fill(0)  # erase current screnn to black
        x,y = leftMargin, topMargin
        for line in lines.split('\n'):
            self.display.text(line, x, y)
            y += FONTSIZE
        self.display.show()

# if __name__ == "__main__":
#     from time import sleep, localtime
#     dis = Display(0, 17, 16)
#     while True:
#         now = localtime()
#         dis.multiLines(f"""{now[0]}-{now[1]:02}-{now[2]:02}
#     {now[3]}:{now[4]:02}:{now[5]:02}""")
#     sleep(1)
