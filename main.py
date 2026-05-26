import uasyncio as asyncio
import bluetooth
from machine import Pin, Timer
from engine import engine_managment 
from Servo import servo            
from rfid_scanner import RFIDScanner 

# ---------------- ПИНЫ ДРАЙВЕРА МОТОРОВ (TB6612FNG) ----------------
A_IN2 = 19
A_IN1 = 18
PWMA = 17

B_IN2 = 4
B_IN1 = 2  # Синий светодиод платы
PWMB = 16

STBY = 5

# ---------------- ПИНЫ СЕРВО ----------------
SERVO_CLAW_PIN = 22 # 180 (Клешня)
SERVO_ARM_PIN = 23  # 180 (Рука)

# ---------------- ПИНЫ RFID ----------------
RFID_SCK = 12 
RFID_MOSI = 14
RFID_MISO = 27
RFID_RST = 25
RFID_CS = 13

# ---------------- СКОРОСТИ ----------------
SPEED_FAST = 55000
SPEED_MEDIUM = 30000

# ---------------- BLE UUID ----------------
UART_SERVICE_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
UART_RX_CHAR_UUID = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
UART_TX_CHAR_UUID = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E") 


# Моторы 
engine = engine_managment(A_IN1, A_IN2, PWMA, B_IN1, B_IN2, PWMB, STBY)

# Сервоприводы (настраиваем углы захвата для клешни)
claw = servo(pin=SERVO_CLAW_PIN, hook_angle=30, release_angle=100)
arm = servo(pin=SERVO_ARM_PIN)

# RFID Сканер
scanner = RFIDScanner(
    sck=RFID_SCK, 
    mosi=RFID_MOSI, 
    miso=RFID_MISO, 
    rst=RFID_RST, 
    cs=RFID_CS
)


async def main_loop():
    print("🤖 Робот запущен! Ожидание команд...")
    
    # Включаем сканер
    scanner.start()
    

    asyncio.create_task(scanner.run())

    while True:
        # 1. ПРОВЕРКА RFID
        current_color = scanner.last_text
        
        if current_color:
            if current_color in ["красный", "red"]:
                if not claw.is_moving:
                    print("🔴 Реакция: Хватаю/Бросаю кубик!")
                    await claw.simple_angle()
                    
            elif current_color in ["зеленый", "зелёный", "green"]:
                if not arm.is_moving:
                    print("🟢 Реакция: Двигаю рукой!")
                    await arm.step_angle()
            
            elif current_color in ["синий", "blue"]:
                if not arm.is_moving:
                    print("🔵 Реакция: Полный сброс механики!")
                    await arm.set_angle(0)
                    await claw.set_angle(100)
                    
            # Очищаем память сканера
            scanner.last_text = None 
            await asyncio.sleep(1) # Пауза перед следующим чтением
            scanner.start()



        # command = ble.read_command()
        # if command == "F":
        #     engine.forward(SPEED_FAST)
        # elif command == "S":
        #     engine.stop()

        await asyncio.sleep_ms(50)


try:

    asyncio.run(main_loop())
except KeyboardInterrupt:
    print("🛑 Остановка программы")
    scanner.clear_lights()
    engine.stop() 