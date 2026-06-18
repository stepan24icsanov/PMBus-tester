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

        safe_boot = Pin(22, Pin.IN, Pin.PULL_UP)
        if safe_boot.value() == 0:
            print("Safe boot: GP22 is low, PMBus console not started.")
            break

        i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=50000)
        manager = PMBusManager(i2c)
        manager.run()

        print("Console stopped. Returning to MicroPython REPL.")
        break
    except KeyboardInterrupt:
        print("Interrupted. Console stopped.")
        break
    except Exception as e:
        print("[ERROR] Runtime error:", e)
        print("Restarting console.")
        sleep_ms(500)
