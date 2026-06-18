FRU_IMAGE = bytes([
    0x01, 0x01, 0x00, 0x00, 0x03, 0x0B, 0x00, 0xF0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x08, 0x19, 0xC7, 0x41, 0x53, 0x50, 0x4F,
    0x57, 0x45, 0x52, 0xCF, 0x55, 0x31, 0x41, 0x2D, 0x44, 0x31, 0x36, 0x30, 0x30, 0x2D, 0x47, 0x2D,
    0x31, 0x31, 0x20, 0xC5, 0x20, 0x20, 0x20, 0x20, 0x20, 0xC3, 0x31, 0x2E, 0x30, 0xD6, 0x44, 0x30,
    0x31, 0x31, 0x36, 0x30, 0x30, 0x45, 0x35, 0x34, 0x39, 0x39, 0x39, 0x39, 0x20, 0x20, 0x20, 0x20,
    0x20, 0x20, 0x20, 0x20, 0xC0, 0xC0, 0xC1, 0x39, 0x00, 0x02, 0x18, 0x58, 0x8E, 0x40, 0x06, 0x40,
    0x06, 0x23, 0x05, 0x10, 0x27, 0x9C, 0x31, 0x20, 0x4E, 0xC0, 0x5D, 0x2F, 0x3F, 0x0C, 0x1A, 0x40,
    0xC6, 0x00, 0x40, 0x06, 0x85, 0x01, 0x02, 0x0D, 0x82, 0x6E, 0x01, 0xB0, 0x04, 0x74, 0x04, 0xEC,
    0x04, 0x78, 0x00, 0xE8, 0x03, 0xFF, 0xFF, 0x01, 0x82, 0x0D, 0xC3, 0xAD, 0x82, 0xB0, 0x04, 0x74,
    0x04, 0xEC, 0x04, 0x78, 0x00, 0x64, 0x00, 0xB8, 0x0B, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
])

PAGE_SIZE = 16

if len(FRU_IMAGE) < 0x100:
    FRU_IMAGE += bytes([0] * (0x100 - len(FRU_IMAGE)))

# Work on a mutable copy
BASE_IMAGE = bytearray(FRU_IMAGE)

PRODUCT_AREA_START = 0x018
PRODUCT_AREA_END = 0x058
PRODUCT_FIELDS_START = 0x01B
PRODUCT_CHECKSUM_OFFSET = 0x057

PRODUCT_FIELD_ORDER = [
    "manufacturer",
    "product_name",
    "part_number",
    "product_version",
    "serial_number",
    "asset_tag",
    "fru_file_id",
]

PRODUCT_VALUES = {
    "manufacturer": "GENERIC",
    "product_name": "CRPS-PSU",
    "part_number": "",
    "product_version": "1.0",
    "serial_number": "CRPS0000000000",
    "asset_tag": "",
    "fru_file_id": "",
}

PRODUCT_FIELD_LOCATIONS = {}

NUMERIC_FIELDS = {
    "overall_capacity_w": ("word", 0x05D, 1),
    "peak_va": ("word", 0x05F, 1),
    "inrush_current_a": ("byte", 0x061, 1),
    "inrush_interval_ms": ("byte", 0x062, 1),
    "low_input_voltage_range_1_mv": ("word", 0x063, 10),
    "high_input_voltage_range_1_mv": ("word", 0x065, 10),
    "low_input_voltage_range_2_mv": ("word", 0x067, 10),
    "high_input_voltage_range_2_mv": ("word", 0x069, 10),
    "low_input_frequency_hz": ("byte", 0x06B, 1),
    "high_input_frequency_hz": ("byte", 0x06C, 1),
    "ac_dropout_tolerance_ms": ("byte", 0x06D, 1),
    "power_supply_flags": ("byte", 0x06E, 1),
    "peak_wattage_hold_up_raw": ("word", 0x06F, 1),
    "combined_wattage_selectors": ("byte", 0x071, 1),
    "total_combined_wattage_w": ("word", 0x072, 1),
    "tachometer_lower_threshold_raw": ("byte", 0x074, 1),
    "dc1_output_info": ("byte", 0x07A, 1),
    "dc1_nominal_mv": ("word", 0x07B, 10),
    "dc1_negative_voltage_limit_mv": ("word", 0x07D, 10),
    "dc1_positive_voltage_limit_mv": ("word", 0x07F, 10),
    "dc1_ripple_noise_mv": ("word", 0x081, 1),
    "dc1_min_current_ma": ("word", 0x083, 1),
    "dc1_max_current_ma": ("word", 0x085, 1),
    "dc2_output_info": ("byte", 0x08C, 1),
    "dc2_nominal_mv": ("word", 0x08D, 10),
    "dc2_negative_voltage_limit_mv": ("word", 0x08F, 10),
    "dc2_positive_voltage_limit_mv": ("word", 0x091, 10),
    "dc2_ripple_noise_mv": ("word", 0x093, 1),
    "dc2_min_current_ma": ("word", 0x095, 1),
    "dc2_max_current_ma": ("word", 0x097, 1),
}

SPECIAL_FIELDS = {
    "peak_wattage_w",
    "hold_up_s",
    "tachometer_lower_threshold_rpm",
}

FIELD_DESCRIPTIONS = {
    "manufacturer": "Product Info: Manufacturer, ASCII, variable length inside 0x01B..0x056.",
    "product_name": "Product Info: Product Name / FRU name, ASCII, variable length inside 0x01B..0x056.",
    "part_number": "Product Info: Part/Model Number, ASCII, variable length inside 0x01B..0x056.",
    "product_version": "Product Info: Product Version, ASCII, variable length inside 0x01B..0x056.",
    "serial_number": "Product Info: Serial Number, ASCII, variable length inside 0x01B..0x056.",
    "asset_tag": "Product Info: Asset Tag, ASCII, variable length inside 0x01B..0x056.",
    "fru_file_id": "Product Info: FRU File ID, ASCII, variable length inside 0x01B..0x056.",
    "overall_capacity_w": "Power Supply Info: overall capacity, W, word at 0x05D..0x05E.",
    "peak_va": "Power Supply Info: peak VA / peak value, word at 0x05F..0x060.",
    "inrush_current_a": "Power Supply Info: inrush current, A, byte at 0x061.",
    "inrush_interval_ms": "Power Supply Info: inrush interval, ms, byte at 0x062.",
    "low_input_voltage_range_1_mv": "Power Supply Info: low input voltage range 1, mV, stored in 10 mV units at 0x063..0x064.",
    "high_input_voltage_range_1_mv": "Power Supply Info: high input voltage range 1, mV, stored in 10 mV units at 0x065..0x066.",
    "low_input_voltage_range_2_mv": "Power Supply Info: low input voltage range 2, mV, stored in 10 mV units at 0x067..0x068.",
    "high_input_voltage_range_2_mv": "Power Supply Info: high input voltage range 2, mV, stored in 10 mV units at 0x069..0x06A.",
    "low_input_frequency_hz": "Power Supply Info: low input frequency, Hz, byte at 0x06B.",
    "high_input_frequency_hz": "Power Supply Info: high input frequency, Hz, byte at 0x06C.",
    "ac_dropout_tolerance_ms": "Power Supply Info: AC dropout tolerance, ms, byte at 0x06D.",
    "power_supply_flags": "Power Supply Info: flags byte at 0x06E.",
    "peak_wattage_hold_up_raw": "Power Supply Info: raw peak wattage / hold-up packed word at 0x06F..0x070.",
    "peak_wattage_w": "Power Supply Info: low 12 bits of 0x06F..0x070, peak wattage in W.",
    "hold_up_s": "Power Supply Info: high 4 bits of 0x06F..0x070, hold-up time in seconds.",
    "combined_wattage_selectors": "Power Supply Info: combined wattage output selectors, byte at 0x071.",
    "total_combined_wattage_w": "Power Supply Info: total combined wattage, W, word at 0x072..0x073.",
    "tachometer_lower_threshold_raw": "Power Supply Info: raw tachometer lower threshold, byte at 0x074.",
    "tachometer_lower_threshold_rpm": "Power Supply Info: tachometer lower threshold, RPM, stored as RPM / 60 at 0x074.",
    "dc1_output_info": "DC Output #1 +12V: output info byte at 0x07A.",
    "dc1_nominal_mv": "DC Output #1 +12V: nominal voltage, mV, stored in 10 mV units at 0x07B..0x07C.",
    "dc1_negative_voltage_limit_mv": "DC Output #1 +12V: negative voltage limit, mV, stored in 10 mV units at 0x07D..0x07E.",
    "dc1_positive_voltage_limit_mv": "DC Output #1 +12V: positive voltage limit, mV, stored in 10 mV units at 0x07F..0x080.",
    "dc1_ripple_noise_mv": "DC Output #1 +12V: ripple and noise, mV, word at 0x081..0x082.",
    "dc1_min_current_ma": "DC Output #1 +12V: minimum current draw, mA, word at 0x083..0x084.",
    "dc1_max_current_ma": "DC Output #1 +12V: maximum current draw, mA, word at 0x085..0x086.",
    "dc2_output_info": "DC Output #2 +12Vsb: output info byte at 0x08C.",
    "dc2_nominal_mv": "DC Output #2 +12Vsb: nominal voltage, mV, stored in 10 mV units at 0x08D..0x08E.",
    "dc2_negative_voltage_limit_mv": "DC Output #2 +12Vsb: negative voltage limit, mV, stored in 10 mV units at 0x08F..0x090.",
    "dc2_positive_voltage_limit_mv": "DC Output #2 +12Vsb: positive voltage limit, mV, stored in 10 mV units at 0x091..0x092.",
    "dc2_ripple_noise_mv": "DC Output #2 +12Vsb: ripple and noise, mV, word at 0x093..0x094.",
    "dc2_min_current_ma": "DC Output #2 +12Vsb: minimum current draw, mA, word at 0x095..0x096.",
    "dc2_max_current_ma": "DC Output #2 +12Vsb: maximum current draw, mA, word at 0x097..0x098.",
}

FIELD_ALIASES = {
    "man": "manufacturer",
    "product": "product_name",
    "name": "product_name",
    "version": "product_version",
    "ver": "product_version",
    "serial": "serial_number",
    "sn": "serial_number",
    "asset": "asset_tag",
    "file_id": "fru_file_id",
    "vout_nominal": "dc1_nominal_mv",
    "vout_max_ma": "dc1_max_current_ma",
    "vsb_nominal": "dc2_nominal_mv",
    "vsb_max_ma": "dc2_max_current_ma",
    "+12v_nominal_mv": "dc1_nominal_mv",
    "+12v_max_ma": "dc1_max_current_ma",
    "+12vsb_nominal_mv": "dc2_nominal_mv",
    "+12vsb_max_ma": "dc2_max_current_ma",
}


def normalize_field_name(name):
    field = name.strip().lower().replace("-", "_")
    return FIELD_ALIASES.get(field, field)


def field_names():
    names = list(PRODUCT_FIELD_ORDER) + list(NUMERIC_FIELDS.keys())
    names += list(SPECIAL_FIELDS)
    return sorted(names)


def field_help():
    return [(name, FIELD_DESCRIPTIONS.get(name, "")) for name in field_names()]


def _parse_number(value):
    if isinstance(value, (int, float)):
        return value
    text = str(value).strip().lower().replace(",", ".")
    for suffix in ("mv", "ma", "rpm", "hz", "ms", "w", "va", "a", "v"):
        if text.endswith(suffix):
            text = text[:-len(suffix)].strip()
            break
    if "." in text:
        return float(text)
    return int(text, 0)


def _parse_field_number(field, value):
    number = _parse_number(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if field.endswith("_mv") and text.endswith("v") and not text.endswith("mv"):
            number = float(number) * 1000
        elif field.endswith("_ma") and text.endswith("a") and not text.endswith("ma"):
            number = float(number) * 1000
    return number


def _set_byte(offset, value):
    value = int(value)
    if value < 0 or value > 0xFF:
        raise ValueError("byte value out of range 0..255")
    BASE_IMAGE[offset] = value


def _decode_product_area(image):
    values = {}
    locations = {}
    offset = PRODUCT_FIELDS_START
    for field in PRODUCT_FIELD_ORDER:
        if offset >= PRODUCT_CHECKSUM_OFFSET:
            values[field] = ""
            continue
        type_len = image[offset]
        if type_len == 0xC1:
            values[field] = ""
            continue
        size = type_len & 0x3F
        data_offset = offset + 1
        if data_offset + size > PRODUCT_CHECKSUM_OFFSET:
            size = max(0, PRODUCT_CHECKSUM_OFFSET - data_offset)
        raw = bytes(image[data_offset:data_offset + size])
        values[field] = raw.decode("latin-1", "replace")
        locations[field] = (offset, data_offset, size)
        offset = data_offset + size
    return values, locations


def _refresh_product_cache(image=None):
    values, locations = _decode_product_area(BASE_IMAGE if image is None else image)
    if image is None:
        PRODUCT_VALUES.update(values)
        PRODUCT_FIELD_LOCATIONS.clear()
        PRODUCT_FIELD_LOCATIONS.update(locations)
    return values, locations


def _pack_product_area():
    offset = PRODUCT_FIELDS_START
    new_locations = {}
    BASE_IMAGE[PRODUCT_FIELDS_START:PRODUCT_CHECKSUM_OFFSET] = bytes(
        [0] * (PRODUCT_CHECKSUM_OFFSET - PRODUCT_FIELDS_START)
    )

    for field in PRODUCT_FIELD_ORDER:
        text = PRODUCT_VALUES.get(field, "")
        data = text.encode("latin-1", "replace")
        if len(data) > 0x3F:
            raise ValueError("{} is too long: max 63 bytes per FRU string field".format(field))
        if offset + 1 + len(data) > PRODUCT_CHECKSUM_OFFSET:
            raise ValueError("Product Info Area is full; '{}' does not fit".format(field))
        BASE_IMAGE[offset] = 0xC0 | len(data)
        data_offset = offset + 1
        BASE_IMAGE[data_offset:data_offset + len(data)] = data
        new_locations[field] = (offset, data_offset, len(data))
        offset = data_offset + len(data)

    if offset > PRODUCT_CHECKSUM_OFFSET:
        raise ValueError("Product Info Area has no space for end marker")
    BASE_IMAGE[offset] = 0xC1
    PRODUCT_FIELD_LOCATIONS.clear()
    PRODUCT_FIELD_LOCATIONS.update(new_locations)
    recompute_product_checksum()


def set_manufacturer(text):
    set_field("manufacturer", text)


def set_product_name(text):
    set_field("product_name", text)


def set_part_number(text):
    set_field("part_number", text)


def set_product_version(text):
    set_field("product_version", text)


def set_serial_number(text):
    set_field("serial_number", text)


def recompute_product_checksum():
    # Product Info Area: bytes 0x018..0x057, checksum at 0x057 computed over 0x018..0x056
    s = sum(BASE_IMAGE[0x018:0x057]) & 0xFF
    ch = (-s) & 0xFF
    BASE_IMAGE[0x057] = ch


def _set_word_le(offset, value):
    value = int(value)
    if value < 0 or value > 0xFFFF:
        raise ValueError("word value out of range 0..65535")
    BASE_IMAGE[offset] = value & 0xFF
    BASE_IMAGE[offset+1] = (value >> 8) & 0xFF


def _get_word_le(image, offset):
    return image[offset] | (image[offset + 1] << 8)


def _set_scaled_word(offset, value, scale):
    raw = int(round(float(value) / scale))
    _set_word_le(offset, raw)


def _raw_hex(image, offset, length):
    return " ".join("{:02X}".format(image[offset + i]) for i in range(length))


def _address_text(offset, length):
    if length == 1:
        return "0x{:03X}".format(offset)
    return "0x{:03X}..0x{:03X}".format(offset, offset + length - 1)


def _format_value(field, value, raw=None):
    if field.endswith("_mv"):
        return "{} mV ({:.3g} V)".format(value, value / 1000)
    if field.endswith("_ma"):
        return "{} mA ({:.3g} A)".format(value, value / 1000)
    if field.endswith("_w"):
        return "{} W".format(value)
    if field.endswith("_hz"):
        return "{} Hz".format(value)
    if field.endswith("_ms"):
        return "{} ms".format(value)
    if field.endswith("_a"):
        return "{} A".format(value)
    if field.endswith("_rpm"):
        return "{} RPM".format(value)
    if field == "power_supply_flags":
        return "0x{:02X}".format(value)
    if field in ("dc1_output_info", "dc2_output_info"):
        standby = (value >> 7) & 1
        output_number = value & 0x0F
        return "0x{:02X} (standby={}, output={})".format(value, standby, output_number)
    if field == "combined_wattage_selectors":
        return "0x{:02X} (v1={}, v2={})".format(value, (value >> 4) & 0x0F, value & 0x0F)
    if raw is not None and field.endswith("_raw"):
        return "0x{:0{}X}".format(value, len(raw.replace(" ", "")))
    return str(value)


def get_field_info(name, image=None):
    field = normalize_field_name(name)
    image = BASE_IMAGE if image is None else bytearray(image)

    if field in PRODUCT_FIELD_ORDER:
        values, locations = _refresh_product_cache(image)
        text = values.get(field, "")
        tl_offset, data_offset, size = locations.get(field, (None, None, 0))
        raw = _raw_hex(image, data_offset, size) if data_offset is not None and size else ""
        address = _address_text(data_offset, size) if data_offset is not None and size else "-"
        return {
            "name": field,
            "address": address,
            "raw": raw,
            "value": text,
            "description": FIELD_DESCRIPTIONS.get(field, ""),
        }

    if field == "peak_wattage_w" or field == "hold_up_s":
        raw_word = _get_word_le(image, 0x06F)
        value = raw_word & 0x0FFF if field == "peak_wattage_w" else (raw_word >> 12) & 0x0F
        raw = _raw_hex(image, 0x06F, 2)
        return {
            "name": field,
            "address": _address_text(0x06F, 2),
            "raw": raw,
            "value": _format_value(field, value, raw),
            "description": FIELD_DESCRIPTIONS.get(field, ""),
        }

    if field == "tachometer_lower_threshold_rpm":
        raw_value = image[0x074]
        value = raw_value * 60
        raw = _raw_hex(image, 0x074, 1)
        return {
            "name": field,
            "address": _address_text(0x074, 1),
            "raw": raw,
            "value": _format_value(field, value, raw),
            "description": FIELD_DESCRIPTIONS.get(field, ""),
        }

    if field not in NUMERIC_FIELDS:
        raise KeyError(field)

    kind, offset, scale = NUMERIC_FIELDS[field]
    length = 1 if kind == "byte" else 2
    raw_value = image[offset] if kind == "byte" else _get_word_le(image, offset)
    value = raw_value * scale
    raw = _raw_hex(image, offset, length)
    return {
        "name": field,
        "address": _address_text(offset, length),
        "raw": raw,
        "value": _format_value(field, value, raw),
        "description": FIELD_DESCRIPTIONS.get(field, ""),
    }


def field_values(image=None):
    return [get_field_info(name, image) for name in field_names()]


def set_peak_wattage_hold_up(peak_wattage_w=None, hold_up_s=None):
    raw = BASE_IMAGE[0x06F] | (BASE_IMAGE[0x070] << 8)
    peak = raw & 0x0FFF
    hold = (raw >> 12) & 0x0F
    if peak_wattage_w is not None:
        peak = int(_parse_number(peak_wattage_w))
    if hold_up_s is not None:
        hold = int(_parse_number(hold_up_s))
    if peak < 0 or peak > 0x0FFF:
        raise ValueError("peak wattage out of range 0..4095")
    if hold < 0 or hold > 0x0F:
        raise ValueError("hold-up time out of range 0..15")
    _set_word_le(0x06F, (hold << 12) | peak)
    recompute_multirecord_checksums()


def set_combined_wattage_selectors(voltage_1, voltage_2):
    v1 = int(_parse_number(voltage_1))
    v2 = int(_parse_number(voltage_2))
    if v1 < 0 or v1 > 0x0F or v2 < 0 or v2 > 0x0F:
        raise ValueError("combined wattage selectors must be 0..15")
    _set_byte(0x071, (v1 << 4) | v2)
    recompute_multirecord_checksums()


def set_field(name, value):
    field = normalize_field_name(name)

    if field in PRODUCT_FIELD_ORDER:
        previous = PRODUCT_VALUES.get(field, "")
        PRODUCT_VALUES[field] = str(value)
        try:
            _pack_product_area()
        except Exception:
            PRODUCT_VALUES[field] = previous
            _pack_product_area()
            raise
        return field

    if field == "peak_wattage_w":
        set_peak_wattage_hold_up(peak_wattage_w=value)
        return field
    if field == "hold_up_s":
        set_peak_wattage_hold_up(hold_up_s=value)
        return field
    if field == "tachometer_lower_threshold_rpm":
        rpm = float(_parse_number(value))
        _set_byte(0x074, int(round(rpm / 60)))
        recompute_multirecord_checksums()
        return field

    if field not in NUMERIC_FIELDS:
        raise KeyError(field)

    kind, offset, scale = NUMERIC_FIELDS[field]
    number = _parse_field_number(field, value)
    if kind == "byte":
        _set_byte(offset, number)
    elif kind == "word":
        _set_scaled_word(offset, number, scale)
    else:
        raise KeyError(field)
    recompute_multirecord_checksums()
    return field


def set_dc1_nominal_mv(mv):
    # store value in units of 10 mV at 0x07B..0x07C
    set_field("dc1_nominal_mv", mv)


def set_dc1_max_current_ma(ma):
    set_field("dc1_max_current_ma", ma)


def set_dc2_nominal_mv(mv):
    set_field("dc2_nominal_mv", mv)


def set_dc2_max_current_ma(ma):
    set_field("dc2_max_current_ma", ma)


def recompute_multirecord_checksums():
    # MR1 data bytes 0x05D..0x074, checksum at 0x05B
    s1 = sum(BASE_IMAGE[0x05D:0x075]) & 0xFF
    BASE_IMAGE[0x05B] = (-s1) & 0xFF
    # MR1 header 0x058..0x05B, checksum at 0x05C
    h1 = sum(BASE_IMAGE[0x058:0x05C]) & 0xFF
    BASE_IMAGE[0x05C] = (-h1) & 0xFF

    # MR2 data bytes 0x07A..0x086, checksum at 0x078
    s2 = sum(BASE_IMAGE[0x07A:0x087]) & 0xFF
    BASE_IMAGE[0x078] = (-s2) & 0xFF
    # MR2 header 0x075..0x078, checksum at 0x079
    h2 = sum(BASE_IMAGE[0x075:0x079]) & 0xFF
    BASE_IMAGE[0x079] = (-h2) & 0xFF

    # MR3 data bytes 0x08C..0x098, checksum at 0x08A
    s3 = sum(BASE_IMAGE[0x08C:0x099]) & 0xFF
    BASE_IMAGE[0x08A] = (-s3) & 0xFF
    # MR3 header 0x087..0x08A, checksum at 0x08B
    h3 = sum(BASE_IMAGE[0x087:0x08B]) & 0xFF
    BASE_IMAGE[0x08B] = (-h3) & 0xFF


def get_image():
    return bytes(BASE_IMAGE)


def validate_checksums():
    checks = {
        "common_header": ((0x000, 0x007), 0x007),
        "product_area": ((0x018, 0x057), 0x057),
        "mr1_data": ((0x05D, 0x075), 0x05B),
        "mr1_header": ((0x058, 0x05C), 0x05C),
        "mr2_data": ((0x07A, 0x087), 0x078),
        "mr2_header": ((0x075, 0x079), 0x079),
        "mr3_data": ((0x08C, 0x099), 0x08A),
        "mr3_header": ((0x087, 0x08B), 0x08B),
    }
    result = {}
    for name, (bounds, checksum_offset) in checks.items():
        start, end = bounds
        actual = BASE_IMAGE[checksum_offset]
        calc = (-sum(BASE_IMAGE[start:end])) & 0xFF
        result[name] = calc == actual and ((sum(BASE_IMAGE[start:end]) + actual) & 0xFF) == 0
    return result


def fru_chunks(page_size=PAGE_SIZE):
    img = get_image()
    for i in range(0, len(img), page_size):
        yield i, img[i:i+page_size]


_pack_product_area()
