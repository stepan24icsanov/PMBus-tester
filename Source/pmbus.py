from machine import I2C
import time

class PMBusDevice:
    def __init__(self, i2c: I2C):
        self.i2c = i2c
        self.addr = None

    def read_bytes(self, cmd, length, retries=3):
        for _ in range(retries):
            try:
                return self.i2c.readfrom_mem(self.addr, cmd, length)
            except:
                time.sleep_ms(10)
        return None

    def write_bytes(self, cmd, data, length):
        if isinstance(data, int):
            data_bytes = data.to_bytes(length, 'little')
        elif isinstance(data, (bytes, bytearray)):
            data_bytes = data[:length]
        elif isinstance(data, list):
            data_bytes = bytes(data[:length])
        else:
            raise TypeError("Unsupported data type")
        try:
            self.i2c.writeto_mem(self.addr, cmd, data_bytes)
            return True
        except Exception as e:
            print("I2C Write Error:", e)
            return False

    def block_read(self, cmd, length):
        try:
            packet = bytes(cmd)
            bytes_block = self.i2c.readfrom_mem(self.addr, cmd, length)
            
            return bytes_block
        except Exception as e:
            print("Block Read Error:", e)
            return None

    def block_write(self, cmd, data):
        if len(data) > 255:
            raise ValueError("Block too large")
        try:
            buf = bytes([cmd, len(data)] + data)
            self.i2c.writeto(self.addr, buf)
            return True
        except Exception as e:
            print("Block Write Error:", e)
            return False

    def calc_pec(self, data: bytes) -> int:
        crc = 0
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x07
                else:
                    crc <<= 1
            crc &= 0xFF
        return crc

    def read_bytes_with_pec(self, cmd, length):
        addr_wr = self.addr << 1
        addr_rd = (self.addr << 1) | 1
        pec_wr = self.calc_pec(bytes([addr_wr, cmd]))
        try:
            self.i2c.writeto(self.addr, bytes([cmd, pec_wr]))
            result = self.i2c.readfrom(self.addr, length + 1)
            data, received_pec = result[:-1], result[-1]
            packet = bytes([addr_wr, cmd, addr_rd]) + data
            calc = self.calc_pec(packet)
            if calc != received_pec:
                print(f"[!] PEC mismatch: got 0x{received_pec:02X}, expected 0x{calc:02X}")
                return None
            return data
        except Exception as e:
            print("Read with PEC error:", e)
            return None

    def write_bytes_with_pec(self, cmd, data, length):
        if isinstance(data, int):
            data_bytes = data.to_bytes(length, 'little')
        elif isinstance(data, (bytes, bytearray)):
            data_bytes = data[:length]
        elif isinstance(data, list):
            data_bytes = bytes(data[:length])
        else:
            raise TypeError("Unsupported data type")

        addr_wr = self.addr << 1
        # Для вычисления PEC включаем адрес и команду
        packet_for_crc = bytes([addr_wr, cmd]) + data_bytes
        pec = self.calc_pec(packet_for_crc)

        # Но на I2C шину отправляем ТОЛЬКО команду + данные + PEC
        try:
            self.i2c.writeto(self.addr, bytes([cmd]) + data_bytes + bytes([pec]))
            return True
        except Exception as e:
            print("Write with PEC error:", e)
            return False

        
    def page_plus_read(self, byte_count, page, command):
        addr_wr = self.addr << 1
        page_plus_read_cmd = 0x06
        packet = bytes([page_plus_read_cmd, byte_count, page, command])
        try:
            self.i2c.writeto(self.addr, packet, False)
        except Exception as e:
            print(f"Write PAGE PLUS READ ERROR {e}")
            
        try:
            return self.i2c.readfrom(self.addr, 4)
        except Exception as e:
            print(f"Read PAGE PLUS READ ERROR {e}")

    def read_eeprom(self, eeprom_addr, offset, length):
        """Read `length` bytes from EEPROM starting at `offset`.

        Uses single-byte memory address (AT24C02C style).
        """
        try:
            # Many MicroPython ports implement readfrom_mem
            return self.i2c.readfrom_mem(eeprom_addr, offset & 0xFF, length)
        except Exception as e:
            try:
                # fallback: write offset then read
                self.i2c.writeto(eeprom_addr, bytes([offset & 0xFF]))
                return self.i2c.readfrom(eeprom_addr, length)
            except Exception as e2:
                print("EEPROM read error:", e, e2)
                return None

    def write_eeprom(self, eeprom_addr, data: bytes, page_size=8, write_delay_ms=10):
        """Write `data` to EEPROM at `eeprom_addr` page-by-page (ACK-polling).

        Returns True on success, False on failure.
        """
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes or bytearray")
        if len(data) > 256:
            raise ValueError("data too large for AT24C02 (max 256 bytes)")

        for offset in range(0, len(data), page_size):
            page = data[offset:offset + page_size]
            mem_addr = offset & 0xFF
            buf = bytes([mem_addr]) + page
            try:
                self.i2c.writeto(eeprom_addr, buf)
            except Exception as e:
                print(f"EEPROM write error at 0x{mem_addr:02X}:", e)
                return False

            # ACK polling: try to contact device until it acknowledges
            start = time.ticks_ms()
            while True:
                try:
                    # try a zero-length write (some ports allow it) as poll
                    try:
                        self.i2c.writeto(eeprom_addr, b'')
                        break
                    except Exception:
                        # fallback to a single-byte read to poll ACK
                        self.i2c.readfrom(eeprom_addr, 1)
                        break
                except Exception:
                    if time.ticks_diff(time.ticks_ms(), start) > 1000:
                        print("EEPROM ack poll timeout")
                        return False
                    time.sleep_ms(write_delay_ms)

        return True
