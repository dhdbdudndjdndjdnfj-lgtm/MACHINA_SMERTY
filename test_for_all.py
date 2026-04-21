from machine import Pin
import neopixel
import time

np = neopixel.NeoPixel(Pin(21), 16)

def running_light():
    """Бегающий зеленый свет (один цикл)"""
    for i in range(16):
        np[i] = (0, 255, 0)
        if i > 0:
            np[i-1] = (0, 0, 0)
        np.write()
        time.sleep(0.05)
    np[15] = (0, 0, 0)
    np.write()

running_light()