import uasyncio as asyncio
import bluetooth
from engine import engine_managment
from Servo import servo
from rfid_scanner import RFIDScanner


# ---------------- ПИНЫ МОТОРОВ ----------------
LEFT_IN1 = 21
LEFT_IN2 = 19
RIGHT_IN1 = 17
RIGHT_IN2 = 16

# ---------------- ПИНЫ СЕРВО ----------------
SERVO_CLAW_PIN = 22 #360
SERVO_ARM_PIN = 23 #180

# ---------------- ПИНЫ RFID ----------------
RFID_SCK = 12
RFID_MOSI = 14
RFID_MISO = 27
RFID_RST = 25
RFID_CS = 13

# ---------------- СКОРОСТИ ----------------
SPEED_FAST = 55000
SPEED_MEDIUM = 40000

# ---------------- УГЛЫ ----------------
CLAW_HOOK_ANGLE = 30
CLAW_RELEASE_ANGLE = 100

# ---------------- BLE UUID ----------------
UART_SERVICE_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
UART_RX_CHAR_UUID = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
UART_TX_CHAR_UUID = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")


class BLECar:
    def __init__(self, name="ESP32_CAR"):
        self.name = name
        self.connected = False
        self.commands = []

        # BLE
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self._register_services()
        self.ble.irq(self._irq)
        self._advertise()

        # Моторы
        self.motors = engine_managment(
            LEFT_IN1, LEFT_IN2,
            RIGHT_IN1, RIGHT_IN2,
            smooth_steps=10,
            smooth_delay=0.02,
            boost_duration=0.05,
            min_start_speed=30000
        )

        # Сервы
        self.claw = servo(
            pin=SERVO_CLAW_PIN,
            hook_angle=CLAW_HOOK_ANGLE,
            release_angle=CLAW_RELEASE_ANGLE
        )
        self.claw.set_angle(CLAW_RELEASE_ANGLE)

        self.arm = servo(pin=SERVO_ARM_PIN)
        self.arm.set_angle(0)

        # RFID
        self.rfid = RFIDScanner(
            sck=RFID_SCK,
            mosi=RFID_MOSI,
            miso=RFID_MISO,
            rst=RFID_RST,
            cs=RFID_CS
        )

    def _register_services(self):
        tx = (UART_TX_CHAR_UUID, bluetooth.FLAG_NOTIFY)
        rx = (UART_RX_CHAR_UUID, bluetooth.FLAG_WRITE)
        service = (UART_SERVICE_UUID, (tx, rx))
        ((self.tx_handle, self.rx_handle),) = self.ble.gatts_register_services((service,))

    def _advertise(self):
        name_bytes = self.name.encode()
        adv = bytearray([2, 1, 6, len(name_bytes) + 1, 9]) + name_bytes
        self.ble.gap_advertise(250000, adv)

    def _irq(self, event, data):
        if event == 1:  # подключено
            self.connected = True
            print("✅ BLE подключено")

        elif event == 2:  # отключено
            self.connected = False
            print("❌ BLE отключено")
            self.motors.stop()
            self.rfid.stop()
            self._advertise()

        elif event == 3:  # получены данные
            try:
                cmd = self.ble.gatts_read(self.rx_handle).decode().strip()
                if len(cmd) >= 4 and cmd.startswith("!B"):
                    self.commands.append(cmd[:4])
            except Exception as e:
                print("BLE ошибка:", e)

    async def process_commands(self):
        while True:
            if self.commands:
                cmd = self.commands.pop(0)
                await self.handle_button(cmd)
            await asyncio.sleep_ms(10)

    async def handle_button(self, cmd):
        btn = cmd[2]
        action = cmd[3]

        # Отпускание кнопки
        if action != '1':
            if btn in ('5', '6', '7', '8'):
                self.motors.stop()
            if btn == '1':
                self.rfid.stop()
            return

        # Нажатие
        if btn == '5':
            asyncio.create_task(self.motors.movement(SPEED_FAST, "forward"))
        elif btn == '6':
            asyncio.create_task(self.motors.movement(SPEED_FAST, "reverse"))
        elif btn == '7':
            asyncio.create_task(self.motors.movement(SPEED_MEDIUM, "turn_left"))
        elif btn == '8':
            asyncio.create_task(self.motors.movement(SPEED_MEDIUM, "turn_right"))
        elif btn == '1':
            self.rfid.start()
        elif btn == '2':
            # Кнопка 2 — например, аварийный стоп
            self.motors.stop()
            self.rfid.stop()
        elif btn == '3':
            self.claw.simple_angle()  # предполагается, что есть такой метод
        elif btn == '4':
            self.arm.step_angle()

    async def heartbeat(self):
        """Отправка сигнала жизни по BLE раз в секунду"""
        while True:
            if self.connected:
                try:
                    self.ble.gatts_notify(0, self.tx_handle, "OK\n")
                except:
                    pass
            await asyncio.sleep(1)


# ------------------- ЗАПУСК -------------------
async def main():
    car = BLECar()
    # Запускаем все задачи параллельно
    await asyncio.gather(
        car.process_commands(),
        car.heartbeat(),
        car.rfid.run()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Остановлено пользователем")
    except Exception as e:
        print("Общая ошибка:", e)