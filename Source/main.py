from machine import I2C, Pin
from pmbus_manager import PMBusManager

# Настройка I2C
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=50000)

# Запуск менеджера
manager = PMBusManager(i2c)
manager.run()

