from machine import Pin, PWM

class engine_managment:
    def __init__(self, ain1_pin, ain2_pin, pwma_pin, bin1_pin, bin2_pin, pwmb_pin, stby_pin):
        # Настройка пинов направления для Мотора А (Левый)
        self.ain1 = Pin(ain1_pin, Pin.OUT)
        self.ain2 = Pin(ain2_pin, Pin.OUT)
        # Настройка ШИМ (скорости) для Мотора А
        self.pwma = PWM(Pin(pwma_pin), freq=1000)

        # Настройка пинов направления для Мотора B (Правый)
        self.bin1 = Pin(bin1_pin, Pin.OUT)
        self.bin2 = Pin(bin2_pin, Pin.OUT)
        # Настройка ШИМ (скорости) для Мотора B
        self.pwmb = PWM(Pin(pwmb_pin), freq=1000)

        self.stby = Pin(stby_pin, Pin.OUT)
        self.stby.value(1)

        # Останавливаем моторы при запуске для безопасности
        self.stop()
        print("⚙️ Драйвер моторов TB6612FNG инициализирован!")

    def stop(self):
        """Остановка обоих моторов (Свободный выбег)"""
        self.pwma.duty_u16(0)
        self.pwmb.duty_u16(0)
        
        self.ain1.value(0)
        self.ain2.value(0)
        self.bin1.value(0)
        self.bin2.value(0)

    def brake(self):
        """Резкое активное торможение"""
        self.ain1.value(1)
        self.ain2.value(1)
        self.bin1.value(1)
        self.bin2.value(1)
        self.pwma.duty_u16(65535)
        self.pwmb.duty_u16(65535)

    def forward(self, speed):
        """Движение вперед"""
        speed = int(max(0, min(65535, speed)))
        
        self.ain1.value(1)
        self.ain2.value(0)
        self.bin1.value(1)
        self.bin2.value(0)
        
        self.pwma.duty_u16(speed)
        self.pwmb.duty_u16(speed)

    def backward(self, speed):
        """Движение назад"""
        speed = int(max(0, min(65535, speed)))
        
        self.ain1.value(0)
        self.ain2.value(1)
        self.bin1.value(0)
        self.bin2.value(1)
        
        self.pwma.duty_u16(speed)
        self.pwmb.duty_u16(speed)

    def left(self, speed):
        """Разворот на месте влево (левый назад, правый вперед)"""
        speed = int(max(0, min(65535, speed)))
        
        self.ain1.value(0)
        self.ain2.value(1)
        self.bin1.value(1)
        self.bin2.value(0)
        
        self.pwma.duty_u16(speed)
        self.pwmb.duty_u16(speed)

    def right(self, speed):
        """Разворот на месте вправо (левый вперед, правый назад)"""
        speed = int(max(0, min(65535, speed)))
        
        self.ain1.value(1)
        self.ain2.value(0)
        self.bin1.value(0)
        self.bin2.value(1)
        
        self.pwma.duty_u16(speed)
        self.pwmb.duty_u16(speed)