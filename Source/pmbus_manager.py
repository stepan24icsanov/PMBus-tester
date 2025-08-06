from commands import *
from pmbus import PMBusDevice
from decode import decode_linear_format, linear16_to_float
import time

class PMBusManager:
    def __init__(self, i2c):
        self.device = PMBusDevice(i2c)
        self.pmbus_addr = None
        self.eeprom_addr = None

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
                        exponent_raw = int.from_bytes(exp_data, 'little')
                        exponent = exponent_raw & 0x1F
                        if exponent > 15:
                            exponent -= 32
                        lsb = data[0]
                        msb = data[1]
                        value = linear16_to_float( lsb | (msb << 8) , exponent)
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
        found = self.device.i2c.scan()
        if found:
            for addr in found:
                print(f"Found device at 0x{addr:02X}")
        else:
            print("No devices found.")
    
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
            cmd = input("\n> ").strip().lower()

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
                    if parts[1] == "pmbus":
                        self.set_pmbus_addr(int(parts[2], 16))
                        print(f"PMBus address set to 0x{self.pmbus_addr:02X}")
                    elif parts[1] == "eeprom":
                        self.set_eeprom_addr(int(parts[2], 16))
                        print(f"EEPROM address set to 0x{self.eeprom_addr:02X}")
                else:
                    print("Usage: addr pmbus <hex> or addr eeprom <hex>")
            elif cmd == "showaddr":
                print(f"PMBus address : 0x{self.pmbus_addr:02X}" if self.pmbus_addr else "PMBus address not set")
                print(f"EEPROM address: 0x{self.eeprom_addr:02X}" if self.eeprom_addr else "EEPROM address not set")
            elif cmd.startswith("read "):
                parts = cmd.split()
                if len(parts) == 3:
                    reg = int(parts[1], 16)
                    length = int(parts[2])
                    data = self.device.read_bytes(reg, length)
                    print(f"Data: {data}")
            elif cmd.startswith("write "):
                parts = cmd.split()
                if len(parts) >= 3:
                    reg = int(parts[1], 16)
                    values = [int(v, 16) for v in parts[2:]]
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
                print("  read <reg> <len>   - read <len> bytes from <reg> (hex)")
                print("  write <reg> <val1> [val2 ...] - write bytes to register")
                print("  scan               - scan and list devices on I2C bus")
                print("  check <cmd>         - check if a command code is supported by device")
                print("  readpec <reg> <len>       - read with PEC")
                print("  writepec <reg> <val1>...  - write with PEC")
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
                    reg = int(parts[1], 16)
                    length = int(parts[2])
                    data = self.device.read_bytes_with_pec(reg, length)
                    print(f"Data: {list(data) if data else '[ERROR]'}")
            elif cmd.startswith("writepec "):
                parts = cmd.split()
                if len(parts) >= 3:
                    reg = int(parts[1], 16)
                    values = [int(v, 16) for v in parts[2:]]
                    success = self.device.write_bytes_with_pec(reg, values, len(values))
                    print("Write complete" if success else "[ERROR] Write failed")
            elif cmd.startswith("read_page_plus "):
                parts = cmd.split()
                print(parts)
                values = [int(v, 16) for v in parts[1:]]
                byte_count, page, command = values
                response = self.device.page_plus_read(byte_count, page, command)
                print(f"PAGE_PLUS_READ Response {response}")
                
            else:
                print("Unknown command. Type 'help' for list of commands.")
                