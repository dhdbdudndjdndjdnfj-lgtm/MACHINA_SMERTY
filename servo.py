from machine import Pin, PWM
from time import sleep

class servo:
    def __init__(self, pin, freq = 50, min_us = 500, max_us = 2500,hook_angle = 30, release_angle = 100):
        self.freq = freq
        self.min_us = min_us
        self.max_us = max_us
        self.period_us = 1000000 // freq
        self.duty = 0
        self.hook_angle = hook_angle
        self.release_angle = release_angle
        
        self.servo = PWM(Pin(pin), freq = self.freq)
        self.servo.duty_u16(0)
        self.current_angle = 90
        
    def set_angle(self,angle):
        self.current_angle = angle
        pulse_us = self.min_us + (angle / 180) * (self.max_us - self.min_us)
        duty = int((pulse_us / self.period_us) * 65535)
        self.servo.duty_u16(duty)
    
    def angle(self, step = 30):
        if(self.current_angle == 180):
            self.current_angle = 0
        self.current_angle = (self.current_angle + step)%181
        print(self.current_angle,"ДЕБ")
        self.set_angle(self.current_angle)
        
    def simple_angle(self):
        if(self.current_angle == self.release_angle):
            self.current_angle = self.hook_angle
            print(self.current_angle,"ДЕБ")
            self.set_angle(self.hook_angle)
        elif(self.current_angle == self.hook_angle) :
            self.current_angle = self.release_angle
            print(self.current_angle,"ДЕБ")
            self.set_angle(self.release_angle)
 