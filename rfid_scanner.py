import uasyncio as asyncio
import time
from machine import Pin, SPI
from mfrc522 import MFRC522
import neopixel

class RFIDScanner:
    def __init__(self, sck, mosi, miso, rst, cs, spi_id=1, baudrate=400000):
        self.spi = SPI(
            spi_id,
            baudrate=baudrate,
            polarity=0,
            phase=0,
            sck=Pin(sck),
            mosi=Pin(mosi),
            miso=Pin(miso)
        )

        self.rst_pin = Pin(rst, Pin.OUT, value=1)
        self.cs_pin = Pin(cs, Pin.OUT, value=1)

        self.rst_pin.value(0)
        time.sleep_ms(50)
        self.rst_pin.value(1)
        time.sleep_ms(100)

        self.rdr = MFRC522(
            spi=self.spi,
            gpioRst=self.rst_pin,
            gpioCs=self.cs_pin
        )

        self.enabled = False
        self.last_uid = None
        self.last_time = 0
        self.repeat_delay_ms = 1000
        
        # NeoPixel на пине 21
        self.np = neopixel.NeoPixel(Pin(21), 16)
        
        # Разрешенный UID
        self.allowed_uids = ["8804F531"]

        version = self.rdr.version()
        print("RC522 version:", hex(version))

        if version in (0x00, 0xFF):
            print("⚠️ Нет нормальной связи по SPI с RC522")
        else:
            print("📡 RFID готов")

    def start(self):
        self.enabled = True
        print("🟢 RFID включен")

    def stop(self):
        self.enabled = False
        self.last_uid = None
        print("🔴 RFID выключен")

    @staticmethod
    def uid_to_str(uid):
        return "".join("{:02X}".format(x) for x in uid)

    def running_light(self, r, g, b):
        """Бегающий свет один цикл"""
        for i in range(16):
            self.np[i] = (r, g, b)
            if i > 0:
                self.np[i-1] = (0, 0, 0)
            self.np.write()
            time.sleep(0.05)
        self.np[15] = (0, 0, 0)
        self.np.write()

    async def run(self):
        print("🔍 RFID задача запущена")

        while True:
            try:
                if not self.enabled:
                    await asyncio.sleep_ms(20)
                    continue

                stat, _ = self.rdr.request(self.rdr.REQIDL)

                if stat == self.rdr.OK:
                    stat, uid = self.rdr.anticoll()

                    if stat == self.rdr.OK:
                        uid_str = self.uid_to_str(uid[:4])
                        now = time.ticks_ms()

                        if (
                            uid_str != self.last_uid or
                            time.ticks_diff(now, self.last_time) > self.repeat_delay_ms
                        ):
                            self.last_uid = uid_str
                            self.last_time = now
                            print("🔑 UID:", uid_str)
                            
                            if uid_str in self.allowed_uids:
                                print("✅ ДОСТУП РАЗРЕШЕН")
                                self.running_light(0, 255, 0)
                            else:
                                print("❌ ДОСТУП ЗАПРЕЩЕН")
                                self.running_light(255, 0, 0)

                        self.rdr.stop_crypto1()

                await asyncio.sleep_ms(50)

            except Exception as e:
                print("RFID ошибка:", e)
                await asyncio.sleep_ms(200)