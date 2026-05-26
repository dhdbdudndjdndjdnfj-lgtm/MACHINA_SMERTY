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
        self.last_text = None
        self.last_time = 0
        self.repeat_delay_ms = 1500 
        
        self.np = neopixel.NeoPixel(Pin(21), 16)
        
        self.color_map = {
            "белый":      (255, 255, 255),
            "черный":     (0, 0, 0),        
            "чёрный":     (0, 0, 0),        
            "красный":    (255, 0, 0),
            "желтый":     (255, 255, 0),
            "жёлтый":     (255, 255, 0),
            "синий":      (0, 0, 255),
            "голубой":    (0, 191, 255),
            "зеленый":    (0, 255, 0),
            "зелёный":    (0, 255, 0),
            "оранжевый":  (255, 165, 0),
            "розовый":    (255, 0, 200),
            "фиолетовый": (128, 0, 128),
            "коричневый": (139, 69, 19),
            "серый":      (128, 128, 128),
            "white":      (255, 255, 255),
            "black":      (0, 0, 0),        
            "red":        (255, 0, 0),
            "yellow":     (255, 255, 0),
            "blue":       (0, 0, 255),
            "green":      (0, 255, 0),
            "orange":     (255, 165, 0),
            "pink":       (255, 0, 200),
            "purple":     (128, 0, 128),
            "brown":      (139, 69, 19),
            "grey":       (128, 128, 128)
        }

        print("📡 RFID готов. Режим чтения меток NTAG активен.")

    def start(self):
        self.enabled = True
        print("🟢 RFID включен")

    def stop(self):
        self.enabled = False
        self.last_text = None
        print("🔴 RFID выключен")
        self.clear_lights()

    def clear_lights(self):
        for i in range(16):
            self.np[i] = (0, 0, 0)
        self.np.write()

    async def running_light(self, r, g, b):
        for i in range(16):
            self.np[i] = (r, g, b)
            if i > 0:
                self.np[i-1] = (0, 0, 0)
            self.np.write()
            await asyncio.sleep_ms(50) 
        self.np[15] = (0, 0, 0)
        self.np.write()

    def get_exact_text(self, chunks):
        full_data = bytearray()
        for c in chunks:
            full_data.extend(c)
            
        try:
            idx = full_data.find(b'\xd1\x01')
            if idx == -1 or idx + 4 >= len(full_data):
                return "empty"
                
            payload_len = full_data[idx + 2] 
            
            if full_data[idx + 3] != ord('T'):
                return "empty"
                
            status_byte = full_data[idx + 4]
            lang_len = status_byte & 0x3F
            
            text_start = idx + 5 + lang_len
            pure_text_len = payload_len - (1 + lang_len)
            
            if text_start + pure_text_len > len(full_data):
                return "error"
                
            text_bytes = full_data[text_start : text_start + pure_text_len]
            return text_bytes.decode('utf-8').strip().lower()
            
        except Exception as e:
            print("Ошибка расшифровки:", e)
            return "error"

    async def run(self):
        print("🔍 RFID задача запущена (поиск цветных меток)")

        while True:
            try:
                if not self.enabled:
                    await asyncio.sleep_ms(50)
                    continue

                stat, _ = self.rdr.request(self.rdr.REQIDL)

                if stat == self.rdr.OK:
                    stat, raw_uid = self.rdr.anticoll()

                    if stat == self.rdr.OK:
                        if self.rdr.select_tag(raw_uid) == self.rdr.OK:
                            blockArray0 = bytearray(16) 
                            blockArray1 = bytearray(16) 
                            blockArray2 = bytearray(16) 
                            
                            self.rdr.read(4, into=blockArray0)  # Читает 4, 5, 6, 7
                            self.rdr.read(8, into=blockArray1)  # Читает 8, 9, 10, 11
                            self.rdr.read(12, into=blockArray2) # Читает 12, 13, 14, 15
                            
                            tag_text = self.get_exact_text([blockArray0, blockArray1, blockArray2])
                            now = time.ticks_ms()
                            
                            if (tag_text != self.last_text or 
                                time.ticks_diff(now, self.last_time) > self.repeat_delay_ms):
                                
                                self.last_text = tag_text
                                self.last_time = now
                                print(f"📝 Прочитан текст: '{tag_text}'")
                                
                                if tag_text in self.color_map:
                                    r, g, b = self.color_map[tag_text]
                                    print(f"🎨 Включаю бегущий цвет: {tag_text} RGB({r},{g},{b})")
                                    
                                    await self.running_light(r, g, b)
                                    self.enabled = False 
                                    
                                elif tag_text != "empty" and tag_text != "error":
                                    print("❌ Неизвестный цвет!")
                                    await self.running_light(139, 69, 19)
                                    self.enabled = False 
                                    
                            self.rdr.stop_crypto1()

                await asyncio.sleep_ms(50)

            except Exception as e:
                print("RFID системная ошибка:", e)
                await asyncio.sleep_ms(200)