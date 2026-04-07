import uasyncio as asyncio
import bluetooth
from engine import engine_managment
from Servo import servo
from rfid_scanner import RFIDScanner

# ПИНЫ
LEFT_IN1 = 12
LEFT_IN2 = 13
RIGHT_IN1 = 14
RIGHT_IN2 = 15

SPEED_FAST = 55000
SPEED_MEDIUM = 40000

SERVO_CLAW_PIN = 25
SERVO_ARM_PIN = 26

CLAW_HOOK_ANGLE = 30
CLAW_RELEASE_ANGLE = 100

# BLE UUID
UART_SERVICE_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
UART_RX_CHAR_UUID = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
UART_TX_CHAR_UUID = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")


class BLECar:
    def __init__(self, name="ESP32_CAR"):
        self.ble = bluetooth.BLE()
        self.ble.active(True)

        self.connected = False
        self.name = name

        # МОТОРЫ
        self.motors = engine_managment(
            LEFT_IN1, LEFT_IN2,
            RIGHT_IN1, RIGHT_IN2,
            smooth_steps=10,
            smooth_delay=0.02,
            boost_duration=0.05,
            min_start_speed=30000
        )

        # СЕРВО
        self.claw = servo(
            pin=SERVO_CLAW_PIN,
            hook_angle=CLAW_HOOK_ANGLE,
            release_angle=CLAW_RELEASE_ANGLE
        )
        self.claw.set_angle(CLAW_RELEASE_ANGLE)

        self.arm = servo(pin=SERVO_ARM_PIN)
        self.arm.set_angle(90)

        # BLE
        self._register_services()
        self.ble.irq(self._irq)

        self.commands = []
        self._advertise()

        self.rfid = None

    def _register_services(self):
        tx = (UART_TX_CHAR_UUID, bluetooth.FLAG_NOTIFY)
        rx = (UART_RX_CHAR_UUID, bluetooth.FLAG_WRITE)
        service = (UART_SERVICE_UUID, (tx, rx))
        ((self.tx_handle, self.rx_handle),) = self.ble.gatts_register_services((service,))

    def _irq(self, event, data):
        if event == 1:
            self.connected = True
            print("✅ BLE подключено")

        elif event == 2:
            self.connected = False
            print("❌ BLE отключено")
            self.motors.stop()
            self._advertise()

        elif event == 3:
            try:
                cmd = self.ble.gatts_read(self.rx_handle).decode().strip()
                if len(cmd) >= 4 and cmd.startswith('!B'):
                    self.commands.append(("button", cmd[:4]))
            except:
                pass

    def _advertise(self):
        name_bytes = self.name.encode()
        adv = bytearray([2,1,6,len(name_bytes)+1,9]) + name_bytes
        self.ble.gap_advertise(250000, adv)

    async def process_commands(self):
        while True:
            if self.commands:
                cmd_type, data = self.commands.pop(0)

                if cmd_type == "button":
                    await self._handle_button(data)

            await asyncio.sleep(0.01)

    async def _handle_button(self, cmd):
        btn = cmd[2]
        action = cmd[3]

        # отпускание кнопки
        if action != '1':
            self.motors.stop()

            # RFID выключаем только для кнопки 1
            if btn == '1' and self.rfid:
                self.rfid.stop()

            return

        if btn == '5':
            asyncio.create_task(self.motors.movement(SPEED_FAST, "forward"))

        elif btn == '6':
            asyncio.create_task(self.motors.movement(SPEED_FAST, "reverse"))

        elif btn == '7':
            asyncio.create_task(self.motors.movement(SPEED_MEDIUM, "turn_left"))

        elif btn == '8':
            asyncio.create_task(self.motors.movement(SPEED_MEDIUM, "turn_right"))

        # RFID
        elif btn == '1':
            if self.rfid:
                self.rfid.start()

        # СТОП
        elif btn == '2':
            self.motors.stop()

            if self.rfid:
                self.rfid.stop()

        elif btn == '3':
            self.claw.simple_angle()

        elif btn == '4':
            self.arm.angle(30)

    async def heartbeat(self):
        while True:
            if self.connected:
                self.ble.gatts_notify(0, self.tx_handle, "OK\n")
            await asyncio.sleep(1)


# MAIN
async def main():
    car = BLECar()

    rfid = RFIDScanner()
    car.rfid = rfid

    await asyncio.gather(
        car.process_commands(),
        car.heartbeat(),
        rfid.run()
    )


# START
try:
    asyncio.run(main())
except Exception as e:
    print("Ошибка:", e)