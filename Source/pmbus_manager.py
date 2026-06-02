from commands import *
from pmbus import PMBusDevice
from decode import decode_linear_format, linear16_to_float
from machine import I2C, Pin
import fru_map
import time

class PMBusManager:
    GPIO_PINS = tuple(list(range(0, 23)) + [25, 26, 27, 28])

    def __init__(self, i2c):
        self.device = PMBusDevice(i2c)
        self.pmbus_addr = None
        self.eeprom_addr = None
        self.reserved_gpio = {
            0: "I2C SDA",
            1: "I2C SCL",
        }
        self.gpio_pins = {}
        self.gpio_modes = {}
        self.gpio_names = {}
        self.i2c_freq = 50000

    def set_pmbus_addr(self, addr):
        self.pmbus_addr = addr
        self.device.addr = self.pmbus_addr

    def set_eeprom_addr(self, addr):
        self.eeprom_addr = addr

    def read_and_print(self, cmd: PMBusCommand):
        if cmd.type == "Read Byte" or cmd.size == 1:
            data = self.device.read_bytes(cmd.code, 1)
            value = data[0] if data else None
        elif cmd.type == "Read Word" or cmd.size == 2:
            data = self.device.read_bytes(cmd.code, 2)
            if data:
                if cmd.name.startswith("STATUS_") or cmd.name in ["STATUS_WORD"]:
                    value = (data[1] << 8) | data[0]
                else:
                    if cmd in [READ_VOUT,
                               VOUT_OV_FAULT_LIMIT,
                               VOUT_UV_FAULT_LIMIT,
                               MFR_VOUT_MIN,
                               MFR_VOUT_MAX,
                               READ_VSB_OUT]:
                        exp_data = self.device.read_bytes(VOUT_MODE.code, 1)
                        if exp_data:
                            exponent_raw = int.from_bytes(exp_data, 'little')
                            exponent = exponent_raw & 0x1F
                            if exponent > 15:
                                exponent -= 32
                            lsb = data[0]
                            msb = data[1]
                            value = linear16_to_float( lsb | (msb << 8) , exponent)
                        else:
                            value = None
                    else:       
                        value = decode_linear_format(data[0], data[1])
            else:
                value = None
        elif cmd.type == "Block Read":
            data = self.device.block_read(cmd.code, cmd.size)
            value = data if data else None
        else:
            value = None

        if value is None:
            print(f"{cmd.name:<25}: [ERROR]")
        elif isinstance(value, (int, float)):
            print(f"{cmd.name:<25}: {value:.2f}" if not cmd.name.startswith("STATUS_") else f"{cmd.name:<25}: 0x{value:04X}")
        elif isinstance(value, (bytes, bytearray, list)):
            if cmd.name.startswith("MFR_") or "ID" in cmd.name or "REVISION" in cmd.name:
                try:
                    text = bytes(value).decode("ascii", errors="ignore").strip()
                    print(f"{cmd.name:<25}: {text[:60]}" + ("..." if len(text) > 60 else ""))
                except:
                    print(f"{cmd.name:<25}: {[hex(b) for b in value]}")
            else:
                hex_str = " ".join(hex(b) for b in value)
                print(f"{cmd.name:<25}: {hex_str[:60]}" + ("..." if len(hex_str) > 60 else ""))
        else:
            print(f"{cmd.name:<25}: {value}")

    def decode_status(self, name, data, bit_defs):
        if not data:
            print(f"Decoded {name}: [ERROR]")
            return
        byte = data[0] if len(data) == 1 else (data[1] << 8 | data[0])
        print(f"Decoded {name}:")
        for bit, label in bit_defs.items():
            active = (byte >> bit) & 1
            print(f"  [{bit}] {label:<30}: {'YES' if active else 'NO'}")

    def decode_all_statuses(self):
        self.decode_status("STATUS_WORD", self.device.read_bytes(STATUS_WORD.code, STATUS_WORD.size), {
            15: "VOUT", 14: "IOUT/POUT", 13: "INPUT", 12: "MFR", 11: "POWER_GOOD#",
            10: "FANS", 9: "OTHER", 8: "UNKNOWN",
            7: "BUSY", 6: "OFF", 5: "VOUT_OV", 4: "IOUT_OC", 3: "VIN_UV",
            2: "TEMPERATURE", 1: "CML", 0: "NONE OF THE ABOVE"
        })
        self.decode_status("STATUS_VOUT", self.device.read_bytes(STATUS_VOUT.code, STATUS_VOUT.size), {
            7: "VOUT Over voltage Fault", 6: "VOUT Over voltage Warning",
            5: "VOUT Under voltage Warning", 4: "VOUT Under voltage Fault",
            3: "VOUT_MAX Warning", 2: "TON_MAX_FAULT", 1: "TOFF_MAX Warning", 0: "VOUT Tracking Error"
        })
        self.decode_status("STATUS_IOUT", self.device.read_bytes(STATUS_IOUT.code, STATUS_IOUT.size), {
            7: "IOUT Over current Fault", 6: "IOUT OC + LV Shutdown Fault",
            5: "IOUT Over current Warning", 4: "IOUT Undercurrent Fault",
            3: "Current Share Fault", 2: "Power Limiting",
            1: "POUT Overpower Fault", 0: "POUT Overpower Warning"
        })
        self.decode_status("STATUS_INPUT", self.device.read_bytes(STATUS_INPUT.code, STATUS_INPUT.size), {
            7: "VIN Over voltage Fault", 6: "VIN Over voltage Warning",
            5: "VIN Under voltage Warning", 4: "VIN Under voltage Fault",
            3: "Unit Off - Low Input", 2: "IIN Over current Fault",
            1: "IIN Over current Warning", 0: "PIN Overpower Warning"
        })
        self.decode_status("STATUS_TEMPERATURE", self.device.read_bytes(STATUS_TEMPERATURE.code, STATUS_TEMPERATURE.size), {
            7: "Over temperature Fault", 6: "Over temperature Warning",
            5: "Under temperature Warning", 4: "Under temperature Fault"
        })
        self.decode_status("STATUS_FANS_1_2", self.device.read_bytes(STATUS_FANS_1_2.code, STATUS_FANS_1_2.size), {
            7: "Fan 1 Fault", 6: "Fan 2 Fault", 5: "Fan 1 Warning", 4: "Fan 2 Warning",
            3: "Fan 1 Speed Overridden", 2: "Fan 2 Speed Overridden",
            1: "Airflow Fault", 0: "Airflow Warning"
        })
        self.decode_status("STATUS_OTHER", self.device.read_bytes(STATUS_OTHER.code, STATUS_OTHER.size), {
            5: "Input A Fuse Fault", 4: "Input B Fuse Fault",
            3: "Input A OR-ing Fault", 2: "Input B OR-ing Fault",
            1: "Output OR-ing Fault"
        })

    def poll_params(self):
        cmds = [
            VOUT_OV_FAULT_LIMIT, VOUT_UV_FAULT_LIMIT,
            IOUT_OC_FAULT_LIMIT, IOUT_OC_WARN_LIMIT,
            OT_FAULT_LIMIT, OT_WARN_LIMIT,
            VIN_OV_FAULT_LIMIT, VIN_OV_WARN_LIMIT,
            VIN_UV_WARN_LIMIT, VIN_UV_FAULT_LIMIT,
            READ_VIN, READ_IIN, READ_VOUT, READ_IOUT,
            READ_TEMPERATURE_1, READ_TEMPERATURE_2, READ_TEMPERATURE_3,
            READ_FAN_SPEED_1, READ_POUT, READ_PIN,
            VOUT_MODE, MFR_ID, MFR_MODEL, MFR_REVISION,
            MFR_VIN_MIN, MFR_VIN_MAX, MFR_VOUT_MIN, MFR_VOUT_MAX, MFR_IOUT_MAX, READ_LSB, READ_VSB_OUT, READ_ISB_OUT, READ_FAN_DUTY,
            READ_PSON, READ_CRB, READ_VINOK, READ_ALERT, READ_ADDR
        ]
        for cmd in cmds:
            self.read_and_print(cmd)
            
    def scan_bus(self):
        print("Scanning I2C bus...")
        try:
            found = self.device.i2c.scan()
        except Exception as e:
            print("[ERROR] I2C scan failed:", e)
            return
        if found:
            for addr in found:
                print(f"Found device at 0x{addr:02X}")
        else:
            print("No devices found.")

    def set_i2c_freq(self, freq):
        if freq <= 0:
            print("[!] I2C frequency must be greater than 0.")
            return
        try:
            self.device.i2c.init(freq=freq)
        except Exception as e:
            try:
                self.device.i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=freq)
            except Exception as recreate_error:
                print("I2C frequency change failed:", e)
                print("I2C re-create failed:", recreate_error)
                return
        self.i2c_freq = freq
        print(f"I2C frequency set to {freq} Hz.")

    def handle_i2c_command(self, cmd):
        parts = cmd.split()
        if len(parts) == 2 and parts[1] == "freq":
            print(f"I2C frequency: {self.i2c_freq} Hz")
            return
        if len(parts) == 3 and parts[1] == "freq":
            try:
                freq = int(parts[2], 0)
            except ValueError:
                print("[!] I2C frequency must be a number in Hz.")
                return
            self.set_i2c_freq(freq)
            return
        print("Usage: i2c freq | i2c freq <hz>")

    def gpio_occupied(self):
        occupied = dict(self.reserved_gpio)
        for pin, mode in self.gpio_modes.items():
            name = self.gpio_names.get(pin)
            occupied[pin] = f"{mode}, name={name}" if name else mode
        return occupied

    def print_free_gpio(self):
        occupied = self.gpio_occupied()
        free = [pin for pin in self.GPIO_PINS if pin not in occupied]
        print("Free GPIO pins: " + (", ".join(str(pin) for pin in free) if free else "none"))
        print("Occupied GPIO pins:")
        for pin in sorted(occupied):
            print(f"  GPIO {pin:<2} - {occupied[pin]}")

    def parse_gpio_pin(self, value):
        try:
            pin = int(value, 0)
        except ValueError:
            print("[!] GPIO pin must be a number.")
            return None

        if pin not in self.GPIO_PINS:
            print("[!] Unsupported GPIO pin. Use GPIO 0-22 or 25-28.")
            return None
        return pin

    def gpio_pull(self, value):
        if value in ("none", "nopull", "off"):
            return None
        if value in ("up", "pullup"):
            return Pin.PULL_UP
        if value in ("down", "pulldown"):
            return Pin.PULL_DOWN
        print("[!] Pull must be one of: none, pullup, pulldown.")
        return False

    def gpio_name_from_parts(self, raw_parts, parts, start_index):
        if "as" not in parts[start_index:]:
            return None
        as_index = parts.index("as", start_index)
        if as_index + 1 >= len(raw_parts):
            print("[!] GPIO name cannot be empty.")
            return False
        return " ".join(raw_parts[as_index + 1:])

    def handle_gpio_command(self, cmd):
        raw_parts = cmd.split()
        parts = [part.lower() for part in raw_parts]
        if len(parts) < 2:
            print("Usage: gpio free | gpio use <pin> <in|out> [pullup|pulldown|none|0|1] [as <name>] | gpio name <pin> <name> | gpio read <pin> | gpio write <pin> <0|1> | gpio release <pin>")
            return

        action = parts[1]

        if action == "free":
            self.print_free_gpio()
            return

        if action in ("use", "name", "read", "write", "release"):
            if len(parts) < 3:
                print(f"Usage: gpio {action} <pin>")
                return
            pin_num = self.parse_gpio_pin(parts[2])
            if pin_num is None:
                return
        else:
            print("Unknown GPIO command. Type 'help' for list of commands.")
            return

        if action == "use":
            if len(parts) < 4:
                print("Usage: gpio use <pin> <in|out> [pullup|pulldown|none|0|1] [as <name>]")
                return
            if pin_num in self.gpio_occupied():
                print(f"[!] GPIO {pin_num} is already occupied by {self.gpio_occupied()[pin_num]}.")
                return

            mode = parts[3]
            name = self.gpio_name_from_parts(raw_parts, parts, 4)
            if name is False:
                return
            option_end = parts.index("as", 4) if "as" in parts[4:] else len(parts)
            if mode in ("in", "input"):
                pull = None
                pull_name = "none"
                if option_end >= 5:
                    pull = self.gpio_pull(parts[4])
                    if pull is False:
                        return
                    pull_name = parts[4]
                self.gpio_pins[pin_num] = Pin(pin_num, Pin.IN, pull)
                self.gpio_modes[pin_num] = f"input ({pull_name})"
                if name:
                    self.gpio_names[pin_num] = name
                print(f"GPIO {pin_num} configured as input ({pull_name})" + (f", name={name}." if name else "."))
            elif mode in ("out", "output"):
                initial = 0
                if option_end >= 5:
                    try:
                        initial = int(parts[4])
                    except ValueError:
                        print("[!] Output value must be 0 or 1.")
                        return
                    if initial not in (0, 1):
                        print("[!] Output value must be 0 or 1.")
                        return
                self.gpio_pins[pin_num] = Pin(pin_num, Pin.OUT, value=initial)
                self.gpio_modes[pin_num] = "output"
                if name:
                    self.gpio_names[pin_num] = name
                print(f"GPIO {pin_num} configured as output, value={initial}" + (f", name={name}." if name else "."))
            else:
                print("Usage: gpio use <pin> <in|out> [pullup|pulldown|none|0|1] [as <name>]")
            return

        if pin_num in self.reserved_gpio:
            print(f"[!] GPIO {pin_num} is reserved for {self.reserved_gpio[pin_num]}.")
            return

        pin = self.gpio_pins.get(pin_num)
        if pin is None:
            print(f"[!] GPIO {pin_num} is not configured. Use 'gpio use {pin_num} <in|out>' first.")
            return

        if action == "name":
            if len(raw_parts) < 4:
                print("Usage: gpio name <pin> <name>")
                return
            name = " ".join(raw_parts[3:])
            self.gpio_names[pin_num] = name
            print(f"GPIO {pin_num} name set to {name}.")
        elif action == "read":
            print(f"GPIO {pin_num}: {pin.value()}")
        elif action == "write":
            if len(parts) != 4:
                print("Usage: gpio write <pin> <0|1>")
                return
            if self.gpio_modes.get(pin_num) != "output":
                print(f"[!] GPIO {pin_num} is not configured as output.")
                return
            try:
                value = int(parts[3])
            except ValueError:
                print("[!] GPIO value must be 0 or 1.")
                return
            if value not in (0, 1):
                print("[!] GPIO value must be 0 or 1.")
                return
            pin.value(value)
            print(f"GPIO {pin_num} set to {value}.")
        elif action == "release":
            del self.gpio_pins[pin_num]
            del self.gpio_modes[pin_num]
            if pin_num in self.gpio_names:
                del self.gpio_names[pin_num]
            print(f"GPIO {pin_num} released.")
    
    def is_pmbus_set(self):
        if self.pmbus_addr is None:
            print("[!] PMBus address not set. Use 'addr pmbus <hex>' to set it.")
            return False
        return True

    def run(self):
        all_cmds = {cmd.name.lower(): cmd for cmd in [
            VOUT_OV_FAULT_LIMIT, VOUT_UV_FAULT_LIMIT,
            IOUT_OC_FAULT_LIMIT, IOUT_OC_WARN_LIMIT,
            OT_FAULT_LIMIT, OT_WARN_LIMIT,
            VIN_OV_FAULT_LIMIT, VIN_OV_WARN_LIMIT,
            VIN_UV_WARN_LIMIT, VIN_UV_FAULT_LIMIT,
            READ_VIN, READ_IIN, READ_VOUT, READ_IOUT,
            READ_TEMPERATURE_1, READ_TEMPERATURE_2, READ_TEMPERATURE_3,
            READ_FAN_SPEED_1, READ_POUT, READ_PIN,
            VOUT_MODE, MFR_ID, MFR_MODEL, MFR_REVISION,
            MFR_VIN_MIN, MFR_VIN_MAX, MFR_VOUT_MIN, MFR_VOUT_MAX, MFR_IOUT_MAX
        ]}

        print("PMBus console. Type 'help' for available commands.")

        while True:
            raw_cmd = input("\n> ").strip()
            cmd = raw_cmd.lower()

            needs_pmbus = (
                cmd in ["params", "status"] or
                cmd.startswith("read ") or cmd.startswith("write ") or
                cmd in all_cmds
            )
            if needs_pmbus and not self.is_pmbus_set():
                continue

            if cmd == "params":
                self.poll_params()
            elif cmd == "status":
                self.decode_all_statuses()
            elif cmd == "scan":
                self.scan_bus()
            elif cmd == "exit":
                print("Exiting.")
                break
            elif cmd.startswith("addr"):
                parts = cmd.split()
                if len(parts) == 3:
                    try:
                        addr = int(parts[2], 16)
                    except ValueError:
                        print("[!] Address must be a hex number, for example: 5A")
                        continue
                    if parts[1] == "pmbus":
                        self.set_pmbus_addr(addr)
                        print(f"PMBus address set to 0x{self.pmbus_addr:02X}")
                    elif parts[1] == "eeprom":
                        self.set_eeprom_addr(addr)
                        print(f"EEPROM address set to 0x{self.eeprom_addr:02X}")
                    else:
                        print("Usage: addr pmbus <hex> or addr eeprom <hex>")
                else:
                    print("Usage: addr pmbus <hex> or addr eeprom <hex>")
            elif cmd == "showaddr":
                print(f"PMBus address : 0x{self.pmbus_addr:02X}" if self.pmbus_addr else "PMBus address not set")
                print(f"EEPROM address: 0x{self.eeprom_addr:02X}" if self.eeprom_addr else "EEPROM address not set")
            elif cmd.startswith("i2c"):
                self.handle_i2c_command(cmd)
            elif cmd == "writefru":
                if not self.eeprom_addr:
                    print("[!] EEPROM address not set. Use 'addr eeprom <hex>' to set it.")
                    continue
                print("Writing FRU image to EEPROM...")
                img = fru_map.get_image()
                success = self.device.write_eeprom(self.eeprom_addr, img, page_size=8)
                print("FRU write complete" if success else "[ERROR] FRU write failed")
            elif cmd == "verifyfru":
                if not self.eeprom_addr:
                    print("[!] EEPROM address not set. Use 'addr eeprom <hex>' to set it.")
                    continue
                expected = fru_map.get_image()
                data = self.device.read_eeprom(self.eeprom_addr, 0, len(expected))
                if data is None:
                    print("[ERROR] EEPROM read failed")
                elif bytes(data) == expected:
                    print("FRU verify OK — contents match")
                else:
                    print("FRU verify FAILED — mismatch detected")
            elif cmd.startswith("fru set "):
                parts = raw_cmd.split()
                if len(parts) >= 4:
                    field = parts[2]
                    value = " ".join(parts[3:])
                    try:
                        normalized = fru_map.set_field(field, value)
                        print(f"FRU field '{normalized}' set.")
                    except KeyError:
                        print("Unknown FRU field. Use 'fru fields' to list supported fields.")
                    except Exception as e:
                        print(f"Invalid value for FRU field '{field}': {e}")
                else:
                    print("Usage: fru set <field> <value>")
            elif cmd == "fru fields":
                print("Supported FRU fields:")
                for field, description in fru_map.field_help():
                    print(f"  {field:<38} {description}")
            elif cmd == "fru read":
                print("Current FRU image fields:")
                for info in fru_map.field_values():
                    print(f"  {info['name']:<38} {info['address']:<13} raw={info['raw']:<8} value={info['value']}")
            elif cmd == "fru read eeprom":
                if not self.eeprom_addr:
                    print("[!] EEPROM address not set. Use 'addr eeprom <hex>' to set it.")
                    continue
                data = self.device.read_eeprom(self.eeprom_addr, 0, len(fru_map.get_image()))
                if data is None:
                    print("[ERROR] EEPROM read failed")
                    continue
                print("EEPROM FRU fields:")
                for info in fru_map.field_values(data):
                    print(f"  {info['name']:<38} {info['address']:<13} raw={info['raw']:<8} value={info['value']}")
            elif cmd == "fru checksum":
                checks = fru_map.validate_checksums()
                for name in sorted(checks):
                    print(f"{name:<15}: {'OK' if checks[name] else 'FAIL'}")
            elif cmd.startswith("gpio"):
                try:
                    self.handle_gpio_command(raw_cmd)
                except Exception as e:
                    print("[ERROR] GPIO command failed:", e)
            elif cmd.startswith("read "):
                parts = cmd.split()
                if len(parts) == 3:
                    try:
                        reg = int(parts[1], 16)
                        length = int(parts[2])
                    except ValueError:
                        print("Usage: read <reg> <len>")
                        continue
                    data = self.device.read_bytes(reg, length)
                    print(f"Data: {data}")
            elif cmd.startswith("write "):
                parts = cmd.split()
                if len(parts) >= 3:
                    try:
                        reg = int(parts[1], 16)
                        values = [int(v, 16) for v in parts[2:]]
                    except ValueError:
                        print("Usage: write <reg> <val1> [val2 ...]")
                        continue
                    self.device.write_bytes(reg, values, len(values))
                    print("Write complete")
            elif cmd == "help":
                print("Available commands:")
                print("  params             - show all monitored parameters")
                print("  status             - show all decoded status registers")
                print("  <PARAM_NAME>       - show value of one known command (e.g. MFR_VIN_MIN)")
                print("  addr pmbus <hex>   - set PMBus address")
                print("  addr eeprom <hex>  - set EEPROM address")
                print("  showaddr           - show current addresses")
                print("  i2c freq           - show current I2C frequency")
                print("  i2c freq <hz>      - set I2C frequency in Hz")
                print("  read <reg> <len>   - read <len> bytes from <reg> (hex)")
                print("  write <reg> <val1> [val2 ...] - write bytes to register")
                print("  fru fields         - list writable FRU fields with addresses")
                print("  fru read           - decode all fields from current FRU image")
                print("  fru read eeprom    - decode all fields from EEPROM")
                print("  fru set <field> <value> - set one FRU field in RAM image")
                print("  fru checksum       - validate FRU image checksums")
                print("  writefru           - write current FRU image to EEPROM")
                print("  verifyfru          - compare EEPROM with current FRU image")
                print("  scan               - scan and list devices on I2C bus")
                print("  check <cmd>         - check if a command code is supported by device")
                print("  readpec <reg> <len>       - read with PEC")
                print("  writepec <reg> <val1>...  - write with PEC")
                print("  gpio free          - show free and occupied GPIO pins")
                print("  gpio use <pin> <in|out> [pullup|pulldown|none|0|1] [as <name>] - configure GPIO")
                print("  gpio name <pin> <name> - set configured GPIO name")
                print("  gpio read <pin>    - read configured GPIO state")
                print("  gpio write <pin> <0|1> - set configured output GPIO")
                print("  gpio release <pin> - release configured GPIO")
                print("  exit               - exit the console")
            elif cmd in all_cmds:
                self.read_and_print(all_cmds[cmd])
            elif cmd.startswith("check "):
                if not self.is_pmbus_set():
                    continue
                parts = cmd.split()
                if len(parts) == 2:
                    try:
                        code = int(parts[1], 16)
                        self.device.i2c.writeto(self.pmbus_addr, bytes([0x1A, code]))
                        result = self.device.i2c.readfrom(self.pmbus_addr, 1)
                        if result and result[0] == 1:
                            print(f"Command 0x{code:02X} is supported.")
                        else:
                            print(f"Command 0x{code:02X} is NOT supported.")
                    except Exception as e:
                        print("QUERY failed:", e)
            elif cmd.startswith("readpec "):
                parts = cmd.split()
                if len(parts) == 3:
                    try:
                        reg = int(parts[1], 16)
                        length = int(parts[2])
                    except ValueError:
                        print("Usage: readpec <reg> <len>")
                        continue
                    data = self.device.read_bytes_with_pec(reg, length)
                    print(f"Data: {list(data) if data else '[ERROR]'}")
            elif cmd.startswith("writepec "):
                parts = cmd.split()
                if len(parts) >= 3:
                    try:
                        reg = int(parts[1], 16)
                        values = [int(v, 16) for v in parts[2:]]
                    except ValueError:
                        print("Usage: writepec <reg> <val1>...")
                        continue
                    success = self.device.write_bytes_with_pec(reg, values, len(values))
                    print("Write complete" if success else "[ERROR] Write failed")
            elif cmd.startswith("read_page_plus "):
                parts = cmd.split()
                if len(parts) != 4:
                    print("Usage: read_page_plus <byte_count> <page> <command>")
                    continue
                try:
                    values = [int(v, 16) for v in parts[1:]]
                except ValueError:
                    print("Usage: read_page_plus <byte_count> <page> <command>")
                    continue
                byte_count, page, command = values
                response = self.device.page_plus_read(byte_count, page, command)
                print(f"PAGE_PLUS_READ Response {response}")
                
            else:
                print("Unknown command. Type 'help' for list of commands.")
                
