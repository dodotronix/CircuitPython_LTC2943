# SPDX-License-Identifier: MIT

from micropython import const
from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register.i2c_struct import ROUnaryStruct, UnaryStruct
from adafruit_register.i2c_bits import ROBits, RWBits
from adafruit_register.i2c_bit import ROBit

# REGISTER ADDRESSES
_REG_STATUS = const(0x00)
_REG_CONTROL = const(0x01)

_REG_ACCUMULATED_CHARGE = const(0x02)
_REG_CHARGE_THRESHOLD_HIGH = const(0x04)
_REG_CHARGE_THRESHOLD_LOW = const(0x06)

_REG_VOLTAGE = const(0x08)
_REG_VOLTAGE_THRESHOLD_HIGH = const(0x0a)
_REG_VOLTAGE_THRESHOLD_LOW = const(0x0c)

_REG_CURRENT = const(0x0e)
_REG_CURRENT_THRESHOLD_HIGH = const(0x10)
_REG_CURRENT_THRESHOLD_LOW = const(0x12)

_REG_TEMPERATURE = const(0x14)
_REG_TEMPERATURE_THRESHOLD = const(0x16)

class ALCC:
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
        self.i2c_bus = i2c_bus
        self.i2c_addr = addr
        self.i2c_device = I2CDevice(self.i2c_bus, self.i2c_addr)

    # CONTROL REGISTER
    adc_mode = RWBits(2, _REG_CONTROL, 6, 1)
    prescaler = RWBits(3, _REG_CONTROL, 3, 1)
    alcc = RWBits(2, _REG_CONTROL, 1, 2)
    shutdown = RWBits(1, _REG_CONTROL, 0, 1)

    # STATUS REGISTER
    status = ROUnaryStruct(_REG_STATUS, ">B")

    # CHARGE REGISTERS
    _accumulated_charge = UnaryStruct(_REG_ACCUMULATED_CHARGE, ">H")
    _charge_threshold_high = UnaryStruct(_REG_CHARGE_THRESHOLD_HIGH, ">H")
    _charge_threshold_low = UnaryStruct(_REG_CHARGE_THRESHOLD_LOW, ">H")

    # VOLTAGE REGISTERS
    _voltage_raw = ROUnaryStruct(_REG_VOLTAGE, ">H")
    _voltage_threshold_high = UnaryStruct(_REG_VOLTAGE_THRESHOLD_HIGH, ">H")
    _voltage_threshold_low = UnaryStruct(_REG_VOLTAGE_THRESHOLD_LOW, ">H")

    _current_raw = ROUnaryStruct(_REG_CURRENT, ">H")
    _current_threshold_high = UnaryStruct(_REG_CURRENT_THRESHOLD_HIGH, ">H") 
    _current_threshold_low = UnaryStruct(_REG_CURRENT_THRESHOLD_LOW, ">H") 

    _temperature_raw = ROUnaryStruct(_REG_TEMPERATURE, ">H") 
    _temperature_threshold = UnaryStruct(_REG_TEMPERATURE_THRESHOLD, ">H") 

    @property
    def voltage(self) -> float:
        """Get voltage in Volts"""
        return 23.6*self._voltage_raw/0xffff

    @property
    def voltage_range(self):
        return (self._voltage_threshold_low, self._voltage_threshold_high)

    @voltage_range.setter
    def voltage_range(self, rg):
        def tf(v) -> int:
            return int(0xffff*v/23.6)

        low, high = rg
        print(tf(low), tf(high))
        self._voltage_threshold_low = tf(low)
        self._voltage_threshold_high = tf(high)

    @property
    def temperature(self) -> float:
        """Get temperature in degree celsius"""
        return 510*self._temperature_raw/0xffff - 273.15 

    @property
    def temperature_threshold(self):
        return self._temperature_threshold

    @temperature_threshold.setter
    def temperature_threshold(self, th):
        """Set temperature threshold in degree celsius"""
        self._temperature_threshold = (th + 273.15)*0xffff/510 

    @property
    def current(self) -> float:
        """Get current in Amps."""
        return (0.06/0.002)*((self._current_raw-0x7fff)/0x7fff)

    @property
    def current_range(self):
        return (self._current_threshold_low, self._current_threshold_high)

    @current_range.setter
    def current_range(self, rg):
        """Set current low and high threshold."""

        def tf(v):
            return int((0x7fff*v/(0.06/0.002))+0x7fff)

        low, high = rg
        self._current_threshold_low  = tf(low) 
        self._current_threshold_high  = tf(high)

    @property
    def accumulated_charge(self) -> int:
        """The accumulated charge property."""
        return self._accumulated_charge

    @accumulated_charge.setter
    def accumulated_charge(self, value: int) -> None:
        """Set actual charge value """
        self._shutdown = True
        self._accumulated_charge = value
        self._shutdown = False

    @property
    def charge_range(self):
        return (self._charge_threshold_low, self._charge_threshold_high)

    @charge_range.setter
    def charge_range(self, rg):
        """Set charge low and high threshold."""
        low, high = rg
        self._charge_threshold_low = low 
        self._charge_threshold_high = high 

    def release(self):
        """ Send ARA message to get the info, who pulled the alert pin down """
        try:
            with I2CDevice(self.i2c_bus, 0x0C) as device:
                msg = bytearray(1)
                device.readinto(msg)
                return int.from_bytes(msg, "big") >> 1
        except:
            return 0
