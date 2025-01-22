# SPDX-License-Identifier: MIT


from micropython import const
from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register.i2c_struct import ROUnaryStruct, UnaryStruct
from adafruit_register.i2c_bits import ROBits, RWBits
from adafruit_register.i2c_bit import ROBit

_REG_STATUS = const(0x00)
_REG_CONTROL = const(0x01)

_REG_ACCUMULATED_CHARGE = const(0x02)

_REG_CHARGE_THRESHOLD_HIGH_MSB = const(0x04)
_REG_CHARGE_THRESHOLD_HIGH_LSB = const(0x05)

_REG_CHARGE_THRESHOLD_LOW_MSB = const(0x06)
_REG_CHARGE_THRESHOLD_LOW_LSB = const(0x07)

_REG_VOLTAGE = const(0x08)

_REG_VOLTAGE_THRESHOLD_HIGH_MSB = const(0x0a)
_REG_VOLTAGE_THRESHOLD_HIGH_LSB = const(0x0b)

_REG_VOLTAGE_THRESHOLD_LOW_MSB = const(0x0c)
_REG_VOLTAGE_THRESHOLD_LOW_LSB = const(0x0d)

_REG_CURRENT = const(0x0e)

_REG_CURRENT_THRESHOLD_HIGH_MSB = const(0x10)
_REG_CURRENT_THRESHOLD_HIGH_LSB = const(0x11)

_REG_CURRENT_THRESHOLD_LOW_MSB = const(0x12)
_REG_CURRENT_THRESHOLD_LOW_LSB = const(0x13)

_REG_TEMPERATURE = const(0x14)

_REG_TEMPERATURE_THRESHOLD_HIGH = const(0x16)
_REG_TEMPERATURE_THRESHOLD_LOW = const(0x17)

class ALCC_pin:
    ALERT = 0x02
    CHARGE_COMPLETE = 0x01
    DISABLE = 0x00

class Mode:
    AUTOMATIC = 0x03
    SCAN = 0x02
    MANUAL = 0x01
    SLEEP = 0x00

class Prescaler:
    PRES_M1 = 0x00
    PRES_M4 = 0x01
    PRES_M16 = 0x02
    PRES_M64 = 0x03
    PRES_M256 = 0x04
    PRES_M1024 = 0x05
    PRES_M4096 = 0x06


class LTC2943:
    def __init__(self, i2c_bus: I2C, addr: int = 0x64) -> None:
        self.i2c_device = I2CDevice(i2c_bus, addr)
        self.i2c_addr = addr

    # CONTROL REGISTER
    adc_mode = RWBits(2, _REG_CONTROL, 6, 1, False)
    prescaler = RWBits(3, _REG_CONTROL, 3, 1, False)
    alcc_config = RWBits(2, _REG_CONTROL, 1, 1, False)
    shutdown = RWBits(1, _REG_CONTROL, 0, 1, False)

    # STATUS REGISTER
    current_alert = ROBits(1, _REG_STATUS, 6, 1, False)
    accumulated_charge_ovf = ROBits(1, _REG_STATUS, 5, 1, False)
    temperature_alert = ROBits(1, _REG_STATUS, 4, 1, False)
    charge_alert_high = ROBits(1, _REG_STATUS, 3, 1, False)
    charge_alert_low = ROBits(1, _REG_STATUS, 2, 1, False)
    voltage_alert = ROBits(1, _REG_STATUS, 1, 1, False)
    undervoltage_alert = ROBits(1, _REG_STATUS, 0, 1, False)

    _voltage_raw = ROUnaryStruct(_REG_VOLTAGE, ">h")
    _current_raw = ROUnaryStruct(_REG_CURRENT, ">H")
    _temperature_raw = ROUnaryStruct(_REG_TEMPERATURE, ">H") 
    _accumulated_charge = UnaryStruct(_REG_ACCUMULATED_CHARGE, ">H")

    @property
    def voltage(self) -> float:
        """The voltage property."""
        return 23.6*self._voltage_raw/0xffff

    @property
    def temperature(self) -> float:
        """The temperature property."""
        return 510*self._temperature_raw/0xffff - 273.15 

    @property
    def current(self) -> float:
        """The current property."""
        return (0.06/0.002)*((self._current_raw-0x7fff)/0x7fff)

    @property
    def accumulated_charge(self) -> int:
        """The accumulated_charge property."""
        return self._accumulated_charge

    @accumulated_charge.setter
    def accumulated_charge(self, value: int) -> None:
        """The accumulated_charge property."""
        self.shutdown = True
        self._accumulated_charge = value
        self.shutdown = False

    def reset_accumulated_charge(self) -> None:
        """The reset_accumulated_charge property."""
        self.accumulated_charge = 0xffff
