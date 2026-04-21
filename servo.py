from machine import Pin, PWM
from time import sleep

class servo:
    def __init__(self, pin, hook_angle=30, release_angle=100):
        self.servo = PWM(Pin(pin), freq=50)
        self.period_us = 20000
        self.min_us = 500
        self.max_us = 2500
        self.stop_us = 1450
        self.hook_angle = hook_angle
        self.release_angle = release_angle
        self.degrees_per_sec = 470
        self._relative_state = False
        self.step_count = 0
        self.current_angle = 0
        
        self._set_pulse(0)
        
    def _set_pulse(self, us):
        duty = int((us / self.period_us) * 65535)
        self.servo.duty_u16(duty)
    
    def _set_angle_180(self, angle):
        angle = max(0, min(180, angle))
        pulse_us = self.min_us + (angle / 180) * (self.max_us - self.min_us)
        self._set_pulse(pulse_us)
        sleep(0.3)
        self._set_pulse(0)
    
    def _rotate(self, direction, duration_sec):
        if direction > 0:
            self._set_pulse(2000)
        else:
            self._set_pulse(1000)
        sleep(duration_sec)
        self._set_pulse(self.stop_us)
    
    def simple_angle(self):
        duration_sec = 70 / self.degrees_per_sec + 1/8
        
        if self._relative_state:
            self._rotate(-1, duration_sec)
            self._relative_state = False
        else:
            self._rotate(1, duration_sec)
            self._relative_state = True
        print("Поворот на 70°")
    
    def step_angle(self):
        if self.step_count < 5:
            self.step_count += 1
            self.current_angle = self.step_count * 30
            self._set_angle_180(self.current_angle)
            print(f"Шаг {self.step_count}/5: {self.current_angle}°")
        else:
            self.step_count = 0
            self.current_angle = 0
            self._set_angle_180(0)
            print("Сброс в 0°")
    
    def set_angle(self, angle):
        pass
    
    def angle(self, step=30):
        self.step_angle()