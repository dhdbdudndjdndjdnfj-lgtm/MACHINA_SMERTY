from machine import Pin, PWM
from time import sleep

class servo:
    def __init__(self, pin, hook_angle=30, release_angle=100):
        self.servo = PWM(Pin(pin), freq=50)
        self.period_us = 20000
        self.stop_us = 1450
        self.hook_angle = hook_angle
        self.release_angle = release_angle
        self.current_angle = 90
        self.degrees_per_sec = 450
        
    def _set_pulse(self, us):
        duty = int((us / self.period_us) * 65535)
        self.servo.duty_u16(duty)
    
    def _rotate(self, direction, duration_sec):
        if direction > 0:
            self._set_pulse(2000)
        else:
            self._set_pulse(1000)
        sleep(duration_sec)
        self._set_pulse(self.stop_us)
    
    def set_angle(self, target_angle):
        target_angle = max(0, min(180, target_angle))
        delta = target_angle - self.current_angle
        
        if delta > 180:
            delta -= 360
        elif delta < -180:
            delta += 360
        
        if abs(delta) < 1:
            return
        
        duration = abs(delta) / self.degrees_per_sec
        direction = 1 if delta > 0 else -1
        
        self._rotate(direction, duration)
        self.current_angle = target_angle
    
    def simple_angle(self):
        if self.current_angle == self.release_angle:
            self.set_angle(self.hook_angle)
        else:
            self.set_angle(self.release_angle)
        print(self.current_angle, "ДЕБ")


# ========== ТЕСТ ПОВОРОТА НА 90° ==========

my_servo = servo(pin=23)

print("Тест: поворот на 90°")
print("Исходное положение: 90°")
sleep(1)

my_servo.set_angle(180)
print(f"Текущий угол: {my_servo.current_angle}°")
sleep(2)

my_servo.set_angle(90)
print(f"Текущий угол: {my_servo.current_angle}°")
sleep(2)

my_servo.set_angle(0)
print(f"Текущий угол: {my_servo.current_angle}°")
sleep(2)

my_servo.set_angle(90)
print(f"Текущий угол: {my_servo.current_angle}°")

print("Тест завершён")