import uasyncio as asyncio
from machine import Pin, PWM

led = Pin(2, Pin.OUT)

class engine:
    def __init__(self, in1, in2, freq=1000):
        self.freq = freq
        self.speed = 0
        self.p_in1 = PWM(Pin(in1, Pin.OUT), freq=self.freq)
        self.p_in2 = PWM(Pin(in2, Pin.OUT), freq=self.freq)
        self.stop()
        
    def stop(self):
        self.p_in1.duty_u16(0)
        self.p_in2.duty_u16(0)
        self.speed = 0
        
    def forward(self, speed=None):
        if speed is not None:
            self.speed = min(65535, max(0, speed))
        self.p_in1.duty_u16(self.speed)
        self.p_in2.duty_u16(0)
        
    def reverse(self, speed=None):
        if speed is not None:
            self.speed = min(65535, max(0, speed))
        self.p_in2.duty_u16(self.speed)
        self.p_in1.duty_u16(0)
            
class engine_managment:
    def __init__(self, left_in1, left_in2, right_in1, right_in2, freq=1000, 
                 smooth_steps=20, smooth_delay=0.05, boost_duration=0.1, min_start_speed=30000):
        self.left = engine(left_in1, left_in2, freq)
        self.right = engine(right_in1, right_in2, freq)
        self.speed = 0
        self.direction = "stop"
        
        self.boost_duration = boost_duration
        self.min_start_speed = min_start_speed
        self.smooth_steps = smooth_steps
        self.smooth_delay = smooth_delay
        
        self.stop_flag = False
        
    def stop(self):
        print("СТОПЕ, БРАТ!")
        led.value(not led.value())
        self.stop_flag = True
        self._set_motors_speed(0, "stop")
        self.speed = 0
        self.direction = "stop"
    
    def _set_motors_speed(self, speed, direction, ratio=2/3):
        if direction == "forward":
            print(f"FORWARD speed={speed}")
            self.left.forward(speed)
            self.right.forward(speed)
        elif direction == "reverse":
            print(f"REVERSE speed={speed}")
            self.left.reverse(speed)
            self.right.reverse(speed)
        elif direction == "stop":
            self.left.stop()
            self.right.stop()
        elif direction == "turn_left":
            print(f"TURN LEFT speed={speed}")
            self.left.reverse(speed)
            self.right.forward(speed)
        elif direction == "turn_right":
            print(f"TURN RIGHT speed={speed}")
            self.right.reverse(speed)
            self.left.forward(speed)
        elif direction == "to_left":
            left_speed = int(ratio * speed)
            print(f"TO LEFT right={speed} left={left_speed}")
            self.right.forward(speed)
            self.left.forward(left_speed)
        elif direction == "to_right":
            right_speed = int(ratio * speed)
            print(f"TO RIGHT left={speed} right={right_speed}")
            self.left.forward(speed)
            self.right.forward(right_speed)
    
    def needs_boost(self, target_speed):
        return (self.speed == 0 and target_speed < self.min_start_speed)
    
    async def movement(self, target_speed, target_direction, ratio=2/3):
        """Плавное движение"""
        # Сбрасываем флаг
        self.stop_flag = False
        
        # Буст если нужно
        if self.needs_boost(target_speed):
            self._set_motors_speed(self.min_start_speed, target_direction)
            await asyncio.sleep(self.boost_duration)
            if self.stop_flag:
                return
            start_speed = self.min_start_speed
        else:
            start_speed = self.speed
        
        # Плавный разгон
        for i in range(self.smooth_steps + 1):
            if self.stop_flag:
                return
            
            progress = i / self.smooth_steps
            current_speed = int(start_speed + (target_speed - start_speed) * progress)
            self._set_motors_speed(current_speed, target_direction)
            await asyncio.sleep(self.smooth_delay)
        
        if self.stop_flag:
            return
        
        # Сохраняем состояние
        self.speed = target_speed
        self.direction = target_direction