import uasyncio as asyncio
from machine import Pin, PWM

class servo:
    def __init__(self, pin, hook_angle=30, release_angle=100):
        # Настройка ШИМ (50Гц — стандарт для серв)
        self.servo = PWM(Pin(pin), freq=50)
        self.period_us = 20000
        self.min_us = 500
        self.max_us = 2500
        
        self.hook_angle = hook_angle
        self.release_angle = release_angle
        
        self.current_angle = 0
        self.is_moving = False 
        
        self._set_pulse(0)
        
    def _set_pulse(self, us):
        # Преобразуем микросекунды в duty cycle 16-бит (0-65535)
        duty = int((us / self.period_us) * 65535)
        self.servo.duty_u16(duty)
    
    async def _set_angle_180(self, target_angle, hold=True):
        # Ограничиваем угол от 0 до 180 градусов
        target_angle = int(max(0, min(180, target_angle)))
        
        # Расчет длительности импульса
        pulse_us = self.min_us + (target_angle / 180) * (self.max_us - self.min_us)
        self._set_pulse(pulse_us)
        
        # Ждем завершения движения
        await asyncio.sleep(0.5) 
        self.current_angle = target_angle
            
        # Если hold=False, отключаем питание, чтобы мотор не грелся
        if not hold:
            self._set_pulse(0) 
    
    async def simple_angle(self):
        """Логика для клешни: переключение между двумя позициями"""
        if self.is_moving:
            return
            
        self.is_moving = True 
        try:
            if not hasattr(self, '_state'): self._state = False
            
            if self._state:
                # Открываем
                await self._set_angle_180(self.release_angle, hold=False)
                self._state = False
            else:
                # Закрываем и держим кубик
                await self._set_angle_180(self.hook_angle, hold=True)
                self._state = True
        finally:
            self.is_moving = False 
    
    async def step_angle(self):
        """Логика для руки: шаги 23, 46, 70 и сброс"""
        if self.is_moving:
            return
            
        self.is_moving = True 
        try:
            if not hasattr(self, '_step'): self._step = 0
            self._step += 1
            
            if self._step == 1: target = 23
            elif self._step == 2: target = 46
            elif self._step == 3: target = 70
            else:
                target = 0
                self._step = 0
                
            await self._set_angle_180(target, hold=True)
        finally:
            self.is_moving = False 
    
    async def set_angle(self, angle):
        """Принудительная установка угла"""
        await self._set_angle_180(angle, hold=True)