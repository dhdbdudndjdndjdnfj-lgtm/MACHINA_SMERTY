Понял тебя. Ты хочешь иметь под рукой оригинальную логику, где клешня управляется временем вращения (для сервы 360), а рука — точными углами (для сервы 180).

Вот этот код, который я восстановил из твоего самого первого файла. Он использует _rotate с таймерами для клешни и _set_angle_180 для руки.

Python
import uasyncio as asyncio
from machine import Pin, PWM

class servo:
    def __init__(self, pin, hook_angle=30, release_angle=100):
        self.servo = PWM(Pin(pin), freq=50)
        self.period_us = 20000
        self.min_us = 500
        self.max_us = 2500
        
        # Настройка нейтрали для 360-градусной сервы
        self.stop_us = 1500 
       
        self.hook_angle = hook_angle
        self.release_angle = release_angle
        self.degrees_per_sec = 470
        self._relative_state = False
        self.step_count = 0
        self.current_angle = 0
        self.is_moving = False 
        
        self._set_pulse(0)
        
    def _set_pulse(self, us):
        duty = int((us / self.period_us) * 65535)
        self.servo.duty_u16(duty)
    
    async def _set_angle_180(self, target_angle):
        target_angle = int(max(0, min(180, target_angle)))
        
        if self.current_angle != target_angle:
            print(f"Прыжок на цель: {target_angle}°")
            pulse_us = self.min_us + (target_angle / 180) * (self.max_us - self.min_us)
            self._set_pulse(pulse_us)
            await asyncio.sleep(0.5) 
            self.current_angle = target_angle
        else:
            pulse_us = self.min_us + (target_angle / 180) * (self.max_us - self.min_us)
            self._set_pulse(pulse_us)
            await asyncio.sleep(0.3)
  
        self._set_pulse(0) 
    
    async def _rotate(self, direction, duration_sec):
        # Логика для 360-градусной сервы
        if direction > 0:
            self._set_pulse(2000) 
        else:
            self._set_pulse(1000) 
            
        await asyncio.sleep(duration_sec) 
  
        # Активный тормоз
        self._set_pulse(self.stop_us) 
        await asyncio.sleep(0.3) 
        
        self._set_pulse(0) 
    
    async def simple_angle(self):
        # Логика 360 (Клешня)
        if self.is_moving:
            print("⏳ Игнор: клешня еще работает!")
            return
 
        self.is_moving = True 
        try:
            # --- НАСТРОЙКА ВРЕМЕНИ ---
            duration_forward = 0.07  # Время движения вперед
            duration_back = 0.04    # Время движения назад
         
            if self._relative_state:
                # ПОВОРОТ НАЗАД
                print(f"Кручу назад ({duration_back} сек)")
                await self._rotate(-1, duration_back)
                self._relative_state = False
            else:
                # ПОВОРОТ ВПЕРЕД
                print(f"Кручу вперед ({duration_forward} сек)")
                await self._rotate(1, duration_forward)
                self._relative_state = True
                
            print("Поворот клешни завершен")
        finally:
            self.is_moving = False 
    
    async def step_angle(self):
        # Логика 180 (Рука)
        if self.is_moving:
            print("⏳ Игнор: рука еще в движении!")
            return
            
        self.is_moving = True 
        try:
            if self.step_count < 3:
                self.step_count += 1
                if self.step_count == 1:
                    target = 23
                elif self.step_count == 2:
                    target = 46
                else:
                    target = 70
                    
                print(f"--- ШАГ {self.step_count}/3: Цель {target}° ---")
                await self._set_angle_180(target)
            else:
                self.step_count = 0
                print("--- СБРОС В 0° ---")
                await self._set_angle_180(0)
        finally:
            self.is_moving = False 
    
    async def set_angle(self, angle):
        await self._set_angle_180(angle)