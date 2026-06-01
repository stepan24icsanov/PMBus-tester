# Тестер I2C/SMBus/PMBus

Русский | [English](README_en.md)

Тестер для опроса серверных блоков питания стандарта CRPS и других устройств I2C/SMBus/PMBus. Проект рассчитан на Raspberry Pi Pico с MicroPython и управляется через интерактивный CLI по USB CDC.

## Характеристики

- Платформа: Raspberry Pi Pico / RP2040
- Язык: MicroPython
- I2C по умолчанию: 50 кГц
- SDA: GPIO 0
- SCL: GPIO 1
- GND: общий с тестируемым устройством
- Управление: терминал через виртуальный COM-порт

## Загрузка на Pico

Для загрузки файлов из `Source` в корень файловой системы Pico используется `upload_to_pico.bat`.

Установите `mpremote`:

```text
py -m pip install mpremote
```

Пример загрузки на устройство с портом `COM3`:

```text
upload_to_pico.bat COM3
```

## Основные команды CLI

```text
help                         показать список команд
exit                         выйти из CLI
scan                         просканировать I2C-шину
showaddr                     показать текущие адреса PMBus и EEPROM
addr pmbus <hex>             задать адрес PMBus-устройства
addr eeprom <hex>            задать адрес EEPROM
i2c freq                     показать частоту I2C
i2c freq <hz>                задать частоту I2C
read <reg> <len>             прочитать байты из регистра
write <reg> <val1> ...       записать байты в регистр
readpec <reg> <len>          чтение с PEC
writepec <reg> <val1> ...    запись с PEC
params                       вывести основные параметры блока питания
status                       вывести декодированные статусы
check <cmd>                  проверить поддержку PMBus-команды
```

## GPIO

GPIO 0 и GPIO 1 заняты I2C-шиной.

```text
gpio free                    показать свободные и занятые GPIO
gpio use <pin> in [pullup|pulldown|none] [as <name>]
gpio use <pin> out [0|1] [as <name>]
gpio name <pin> <name>
gpio read <pin>
gpio write <pin> <0|1>
gpio release <pin>
```

## FRU EEPROM

В проекте есть базовый 256-байтный FRU-образ для CRPS-блока питания. Строковые поля по умолчанию нейтральные:

```text
manufacturer   GENERIC
product_name   CRPS-PSU
serial_number  CRPS0000000000
```

Строковые Product Info поля упаковываются как FRU Type/Length + данные. При изменении длинной строки следующие Product Info поля сдвигаются автоматически. Если строка или суммарный Product Info Area не помещаются, команда выдаст ошибку, а старое значение сохранится.

Checksum пересчитываются автоматически:

- Product Info checksum `0x057` после изменения строковых Product Info полей.
- MultiRecord checksum для MR1, MR2, MR3 после изменения параметров питания.

### Команды FRU

```text
fru fields                    список всех записываемых FRU-полей с адресами
fru read                      декодировать все поля текущего FRU-образа в RAM
fru read eeprom               прочитать EEPROM и декодировать все поля
fru set <field> <value>       изменить одно поле в RAM-образе
fru checksum                  проверить checksum текущего RAM-образа
writefru                      записать текущий RAM-образ в EEPROM
verifyfru                     сравнить EEPROM с текущим RAM-образом
```

Пример:

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

Изменения через `fru set` живут в RAM текущей сессии. В EEPROM они попадают только после `writefru`.

### Карта памяти FRU

Общая структура EEPROM:

| Область | Адрес | Длина | Назначение |
|---|---:|---:|---|
| Common Header | `0x000..0x007` | 8 B | Версия FRU, смещения областей, checksum |
| Internal Use Area | `0x008..0x017` | 16 B | Зарезервировано, заполнено нулями |
| Product Info Area | `0x018..0x057` | 64 B | Производитель, имя FRU, версия, серийный номер, checksum |
| MultiRecord Area | `0x058..0x098` | 65 B | Power Supply Info и два DC Output record |
| Unused Area | `0x099..0x0FF` | 103 B | Не используется |

Product Info Area:

| Поле | Адрес |
|---|---:|
| Format Version | `0x018` |
| Area Length | `0x019` |
| Language Code | `0x01A` |
| Manufacturer | переменно, начиная с `0x01B` |
| Product Name | переменно |
| Part Number | переменно |
| Product Version | переменно |
| Serial Number | переменно |
| Asset Tag | переменно |
| FRU File ID | переменно |
| No More Fields marker | переменно |
| Product checksum | `0x057` |

Power Supply Info record:

| Поле `fru set` | Адрес | Единицы |
|---|---:|---|
| `overall_capacity_w` | `0x05D..0x05E` | W |
| `peak_va` | `0x05F..0x060` | raw/VA |
| `inrush_current_a` | `0x061` | A |
| `inrush_interval_ms` | `0x062` | ms |
| `low_input_voltage_range_1_mv` | `0x063..0x064` | mV, хранится шагом 10 mV |
| `high_input_voltage_range_1_mv` | `0x065..0x066` | mV, хранится шагом 10 mV |
| `low_input_voltage_range_2_mv` | `0x067..0x068` | mV, хранится шагом 10 mV |
| `high_input_voltage_range_2_mv` | `0x069..0x06A` | mV, хранится шагом 10 mV |
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
| `tachometer_lower_threshold_rpm` | `0x074` | RPM, хранится как RPM / 60 |

DC Output #1 `+12V`:

| Поле `fru set` | Адрес | Единицы |
|---|---:|---|
| `dc1_output_info` | `0x07A` | raw byte |
| `dc1_nominal_mv` | `0x07B..0x07C` | mV, хранится шагом 10 mV |
| `dc1_negative_voltage_limit_mv` | `0x07D..0x07E` | mV, хранится шагом 10 mV |
| `dc1_positive_voltage_limit_mv` | `0x07F..0x080` | mV, хранится шагом 10 mV |
| `dc1_ripple_noise_mv` | `0x081..0x082` | mV |
| `dc1_min_current_ma` | `0x083..0x084` | mA |
| `dc1_max_current_ma` | `0x085..0x086` | mA |

DC Output #2 `+12Vsb`:

| Поле `fru set` | Адрес | Единицы |
|---|---:|---|
| `dc2_output_info` | `0x08C` | raw byte |
| `dc2_nominal_mv` | `0x08D..0x08E` | mV, хранится шагом 10 mV |
| `dc2_negative_voltage_limit_mv` | `0x08F..0x090` | mV, хранится шагом 10 mV |
| `dc2_positive_voltage_limit_mv` | `0x091..0x092` | mV, хранится шагом 10 mV |
| `dc2_ripple_noise_mv` | `0x093..0x094` | mV |
| `dc2_min_current_ma` | `0x095..0x096` | mA |
| `dc2_max_current_ma` | `0x097..0x098` | mA |

## Рекомендуемый порядок работы

1. Подключить I2C EEPROM/PMBus-устройство к SDA GPIO 0, SCL GPIO 1 и GND.
2. Выполнить `scan` и найти адреса устройств.
3. Задать адреса через `addr pmbus <hex>` и `addr eeprom <hex>`.
4. Проверить текущие данные через `params`, `status`, `fru read eeprom`.
5. Изменить нужные FRU-поля через `fru set`.
6. Проверить `fru checksum`.
7. Записать `writefru` и проверить `verifyfru`.
