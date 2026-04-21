from machine import Pin, SPI
import time


class MFRC522:
    OK = 0
    NOTAGERR = 1
    ERR = 2

    REQIDL = 0x26
    REQALL = 0x52
    PICC_ANTICOLL = 0x93

    PCD_IDLE = 0x00
    PCD_TRANSCEIVE = 0x0C
    PCD_RESETPHASE = 0x0F
    PCD_CALCCRC = 0x03

    CommandReg = 0x01
    ComIEnReg = 0x02
    DivIEnReg = 0x03
    ComIrqReg = 0x04
    DivIrqReg = 0x05
    ErrorReg = 0x06
    Status1Reg = 0x07
    Status2Reg = 0x08
    FIFODataReg = 0x09
    FIFOLevelReg = 0x0A
    ControlReg = 0x0C
    BitFramingReg = 0x0D
    ModeReg = 0x11
    TxControlReg = 0x14
    TxASKReg = 0x15
    TModeReg = 0x2A
    TPrescalerReg = 0x2B
    TReloadRegH = 0x2C
    TReloadRegL = 0x2D
    VersionReg = 0x37

    def __init__(self, spi, gpioRst, gpioCs):
        self.spi = spi
        self.rst = gpioRst
        self.cs = gpioCs

        self.rst.init(Pin.OUT, value=1)
        self.cs.init(Pin.OUT, value=1)

        time.sleep_ms(50)  # задержка перед сбросом

        self.reset()
        time.sleep_ms(50)  # задержка после сброса

        self._init_hardware()

    def _wreg(self, reg, val):
        self.cs.value(0)
        self.spi.write(bytearray([((reg << 1) & 0x7E)]))
        self.spi.write(bytearray([val]))
        self.cs.value(1)

    def _rreg(self, reg):
        self.cs.value(0)
        self.spi.write(bytearray([((reg << 1) & 0x7E) | 0x80]))
        val = self.spi.read(1)
        self.cs.value(1)
        return val[0]

    def _sbits(self, reg, mask):
        self._wreg(reg, self._rreg(reg) | mask)

    def _cbits(self, reg, mask):
        self._wreg(reg, self._rreg(reg) & (~mask))

    def reset(self):
        self._wreg(self.CommandReg, self.PCD_RESETPHASE)

    def _init_hardware(self):
        self.reset()
        time.sleep_ms(20)
        self._wreg(self.TModeReg, 0x8D)
        self._wreg(self.TPrescalerReg, 0x3E)
        self._wreg(self.TReloadRegL, 30)
        self._wreg(self.TReloadRegH, 0)
        self._wreg(self.TxASKReg, 0x40)
        self._wreg(self.ModeReg, 0x3D)
        time.sleep_ms(20)
        self.antenna_on()
        time.sleep_ms(20)

    def antenna_on(self):
        if (self._rreg(self.TxControlReg) & 0x03) != 0x03:
            self._sbits(self.TxControlReg, 0x03)

    def antenna_off(self):
        self._cbits(self.TxControlReg, 0x03)

    def version(self):
        return self._rreg(self.VersionReg)

    def _tocard(self, cmd, send):
        recv = []
        bits = 0
        stat = self.ERR

        if cmd == 0x0E:
            irq_en = 0x12
            wait_irq = 0x10
        else:
            irq_en = 0x77
            wait_irq = 0x30

        self._wreg(self.ComIEnReg, irq_en | 0x80)
        self._cbits(self.ComIrqReg, 0x80)
        self._sbits(self.FIFOLevelReg, 0x80)
        self._wreg(self.CommandReg, self.PCD_IDLE)

        for c in send:
            self._wreg(self.FIFODataReg, c)

        self._wreg(self.CommandReg, cmd)

        if cmd == self.PCD_TRANSCEIVE:
            self._sbits(self.BitFramingReg, 0x80)

        i = 2000
        while i > 0:
            n = self._rreg(self.ComIrqReg)
            if (n & 0x01) or (n & wait_irq):
                break
            i -= 1

        self._cbits(self.BitFramingReg, 0x80)

        if i == 0:
            return self.ERR, recv, bits

        if (self._rreg(self.ErrorReg) & 0x1B) != 0:
            return self.ERR, recv, bits

        stat = self.OK

        if n & irq_en & 0x01:
            stat = self.NOTAGERR

        if cmd == self.PCD_TRANSCEIVE:
            n = self._rreg(self.FIFOLevelReg)
            lbits = self._rreg(self.ControlReg) & 0x07

            if lbits != 0:
                bits = (n - 1) * 8 + lbits
            else:
                bits = n * 8

            if n == 0:
                n = 1
            elif n > 16:
                n = 16

            for _ in range(n):
                recv.append(self._rreg(self.FIFODataReg))

        return stat, recv, bits

    def request(self, mode):
        self._wreg(self.BitFramingReg, 0x07)
        stat, recv, bits = self._tocard(self.PCD_TRANSCEIVE, [mode])

        if stat != self.OK or bits != 0x10:
            stat = self.ERR

        return stat, bits

    def anticoll(self):
        ser_chk = 0
        ser = [self.PICC_ANTICOLL, 0x20]
        self._wreg(self.BitFramingReg, 0x00)
        stat, recv, bits = self._tocard(self.PCD_TRANSCEIVE, ser)

        if stat == self.OK:
            if len(recv) == 5:
                for i in range(4):
                    ser_chk ^= recv[i]
                if ser_chk != recv[4]:
                    stat = self.ERR
            else:
                stat = self.ERR

        return stat, recv

    def stop_crypto1(self):
        self._cbits(self.Status2Reg, 0x08)