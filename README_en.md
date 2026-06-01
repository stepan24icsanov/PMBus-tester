# I2C/SMBus/PMBus Tester

[Русский](README.md) | English

Tester for CRPS server power supplies and other I2C/SMBus/PMBus devices. The project runs on Raspberry Pi Pico with MicroPython and is controlled through an interactive USB CDC CLI.

## Hardware

- Platform: Raspberry Pi Pico / RP2040
- Language: MicroPython
- Default I2C speed: 50 kHz
- SDA: GPIO 0
- SCL: GPIO 1
- GND: common ground with the tested device
- Control interface: terminal over virtual COM port

## Uploading To Pico

Use `upload_to_pico.bat` to copy files from `Source` to the root of the Pico filesystem.

Install `mpremote`:

```text
py -m pip install mpremote
```

Upload example for a device on `COM3`:

```text
upload_to_pico.bat COM3
```

## Main CLI Commands

```text
help                         show command list
exit                         exit CLI
scan                         scan the I2C bus
showaddr                     show current PMBus and EEPROM addresses
addr pmbus <hex>             set PMBus device address
addr eeprom <hex>            set EEPROM address
i2c freq                     show I2C frequency
i2c freq <hz>                set I2C frequency
read <reg> <len>             read bytes from register
write <reg> <val1> ...       write bytes to register
readpec <reg> <len>          read with PEC
writepec <reg> <val1> ...    write with PEC
params                       print main power supply parameters
status                       print decoded status registers
check <cmd>                  check whether a PMBus command is supported
```

## GPIO

GPIO 0 and GPIO 1 are reserved for I2C.

```text
gpio free                    show free and occupied GPIO pins
gpio use <pin> in [pullup|pulldown|none] [as <name>]
gpio use <pin> out [0|1] [as <name>]
gpio name <pin> <name>
gpio read <pin>
gpio write <pin> <0|1>
gpio release <pin>
```

## FRU EEPROM

The project includes a base 256-byte FRU image for a generic CRPS power supply. Default string fields are neutral:

```text
manufacturer   GENERIC
product_name   CRPS-PSU
serial_number  CRPS0000000000
```

Product Info strings are encoded as FRU Type/Length + data. When a longer string is written, following Product Info fields are shifted automatically. If a string or the full Product Info Area does not fit, the command fails and the previous value is kept.

Checksums are recalculated automatically:

- Product Info checksum `0x057` after changing Product Info strings.
- MultiRecord checksums for MR1, MR2 and MR3 after changing power parameters.

### FRU Commands

```text
fru fields                    list all writable FRU fields with addresses
fru read                      decode all fields from the current RAM FRU image
fru read eeprom               read EEPROM and decode all fields
fru set <field> <value>       change one field in the RAM image
fru checksum                  validate checksums of the current RAM image
writefru                      write the current RAM image to EEPROM
verifyfru                     compare EEPROM contents with the current RAM image
```

Example:

```text
addr eeprom 50
fru set manufacturer GENERIC
fru set product_name CRPS-1600W
fru set serial_number CRPS1600-TEST-00001
fru set dc1_nominal_mv 12v
fru set dc2_max_current_ma 2.1a
fru checksum
writefru
verifyfru
```

Changes made with `fru set` live in RAM for the current session. They are written to EEPROM only after `writefru`.

### FRU Memory Map

EEPROM structure:

| Area | Address | Length | Purpose |
|---|---:|---:|---|
| Common Header | `0x000..0x007` | 8 B | FRU version, area offsets, checksum |
| Internal Use Area | `0x008..0x017` | 16 B | Reserved, zero-filled |
| Product Info Area | `0x018..0x057` | 64 B | Manufacturer, FRU name, version, serial number, checksum |
| MultiRecord Area | `0x058..0x098` | 65 B | Power Supply Info and two DC Output records |
| Unused Area | `0x099..0x0FF` | 103 B | Unused |

Product Info Area:

| Field | Address |
|---|---:|
| Format Version | `0x018` |
| Area Length | `0x019` |
| Language Code | `0x01A` |
| Manufacturer | variable, starts at `0x01B` |
| Product Name | variable |
| Part Number | variable |
| Product Version | variable |
| Serial Number | variable |
| Asset Tag | variable |
| FRU File ID | variable |
| No More Fields marker | variable |
| Product checksum | `0x057` |

Power Supply Info record:

| `fru set` field | Address | Units |
|---|---:|---|
| `overall_capacity_w` | `0x05D..0x05E` | W |
| `peak_va` | `0x05F..0x060` | raw/VA |
| `inrush_current_a` | `0x061` | A |
| `inrush_interval_ms` | `0x062` | ms |
| `low_input_voltage_range_1_mv` | `0x063..0x064` | mV, stored in 10 mV units |
| `high_input_voltage_range_1_mv` | `0x065..0x066` | mV, stored in 10 mV units |
| `low_input_voltage_range_2_mv` | `0x067..0x068` | mV, stored in 10 mV units |
| `high_input_voltage_range_2_mv` | `0x069..0x06A` | mV, stored in 10 mV units |
| `low_input_frequency_hz` | `0x06B` | Hz |
| `high_input_frequency_hz` | `0x06C` | Hz |
| `ac_dropout_tolerance_ms` | `0x06D` | ms |
| `power_supply_flags` | `0x06E` | raw byte |
| `peak_wattage_hold_up_raw` | `0x06F..0x070` | raw word |
| `peak_wattage_w` | `0x06F..0x070` | packed low 12 bits |
| `hold_up_s` | `0x06F..0x070` | packed high 4 bits |
| `combined_wattage_selectors` | `0x071` | raw byte |
| `total_combined_wattage_w` | `0x072..0x073` | W |
| `tachometer_lower_threshold_raw` | `0x074` | raw byte |
| `tachometer_lower_threshold_rpm` | `0x074` | RPM, stored as RPM / 60 |

DC Output #1 `+12V`:

| `fru set` field | Address | Units |
|---|---:|---|
| `dc1_output_info` | `0x07A` | raw byte |
| `dc1_nominal_mv` | `0x07B..0x07C` | mV, stored in 10 mV units |
| `dc1_negative_voltage_limit_mv` | `0x07D..0x07E` | mV, stored in 10 mV units |
| `dc1_positive_voltage_limit_mv` | `0x07F..0x080` | mV, stored in 10 mV units |
| `dc1_ripple_noise_mv` | `0x081..0x082` | mV |
| `dc1_min_current_ma` | `0x083..0x084` | mA |
| `dc1_max_current_ma` | `0x085..0x086` | mA |

DC Output #2 `+12Vsb`:

| `fru set` field | Address | Units |
|---|---:|---|
| `dc2_output_info` | `0x08C` | raw byte |
| `dc2_nominal_mv` | `0x08D..0x08E` | mV, stored in 10 mV units |
| `dc2_negative_voltage_limit_mv` | `0x08F..0x090` | mV, stored in 10 mV units |
| `dc2_positive_voltage_limit_mv` | `0x091..0x092` | mV, stored in 10 mV units |
| `dc2_ripple_noise_mv` | `0x093..0x094` | mV |
| `dc2_min_current_ma` | `0x095..0x096` | mA |
| `dc2_max_current_ma` | `0x097..0x098` | mA |

## Typical Workflow

1. Connect the I2C EEPROM/PMBus device to SDA GPIO 0, SCL GPIO 1 and GND.
2. Run `scan` and find device addresses.
3. Set addresses with `addr pmbus <hex>` and `addr eeprom <hex>`.
4. Inspect current data with `params`, `status` and `fru read eeprom`.
5. Change required FRU fields with `fru set`.
6. Validate with `fru checksum`.
7. Write with `writefru` and verify with `verifyfru`.
