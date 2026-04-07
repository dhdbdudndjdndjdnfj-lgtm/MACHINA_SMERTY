import uasyncio as asyncio
from machine import Pin, SPI
from mfrc522 import MFRC522
import time


class RFIDScanner:
    def __init__(self,
                 sck=18, mosi=23, miso=19,
                 rst=4, cs=5):

        self.spi = SPI(
            2,
            baudrate=100000,
            polarity=0,
            phase=0,
            sck=Pin(sck),
            mosi=Pin(mosi),
            miso=Pin(miso)
        )

        self.rdr = MFRC522(
            spi=self.spi,
            gpioRst=Pin(rst),
            gpioCs=Pin(cs)
        )

        self.last_uid = None
        self.last_time = 0
        self.delay = 1000

        self.enabled = False

        print("📡 RFID готов (ожидает включения)")

    def start(self):
        if not self.enabled:
            print("🟢 RFID включен")
        self.enabled = True

    def stop(self):
        if self.enabled:
            print("🔴 RFID выключен")
        self.enabled = False
        self.last_uid = None  # важно для быстрого сброса

    def uid_to_str(self, uid):
        return "".join("{:02X}".format(x) for x in uid)

    async def run(self):
        print("🔍 RFID задача запущена")

        while True:
            try:
                if not self.enabled:
                    await asyncio.sleep_ms(20)
                    continue

                (stat, _) = self.rdr.request(self.rdr.REQIDL)

                if stat == self.rdr.OK:
                    (stat, uid) = self.rdr.anticoll()

                    if stat == self.rdr.OK:
                        uid_str = self.uid_to_str(uid)

                        now = time.ticks_ms()

                        if (uid_str != self.last_uid or
                            time.ticks_diff(now, self.last_time) > self.delay):

                            self.last_uid = uid_str
                            self.last_time = now

                            print("🔑 UID:", uid_str)

                            self.rdr.stop_crypto1()

                await asyncio.sleep_ms(10)

            except Exception as e:
                print("RFID ошибка:", e)
                await asyncio.sleep_ms(50)