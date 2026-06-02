import time


def sleep_ms(ms):
    if hasattr(time, "sleep_ms"):
        time.sleep_ms(ms)
    else:
        time.sleep(ms / 1000)


while True:
    try:
        from machine import I2C, Pin
        from pmbus_manager import PMBusManager

        i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=50000)
        manager = PMBusManager(i2c)
        manager.run()

        print("Console stopped. Reset Pico to restart.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[ERROR] Interrupted. Restarting console.")
        sleep_ms(500)
    except Exception as e:
        print("[ERROR] Runtime error:", e)
        print("Restarting console.")
        sleep_ms(500)
