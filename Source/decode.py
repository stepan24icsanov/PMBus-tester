import struct


def decode_linear_format(lsb, msb):
    raw = (msb << 8) | lsb
    n_raw = (raw >> 11) & 0x1F
    N = n_raw - 32 if n_raw & 0x10 else n_raw
    y_raw = raw & 0x7FF
    Y = y_raw - 2048 if y_raw & 0x400 else y_raw
    return Y * (2 ** N)


def linear16_to_float(raw: int, exponent: int) -> float:
    """
    Преобразует значение из формата Linear16 (16-бит) в float.
    :param raw: 16-битное значение (uint16_t), читаемое из PMBus
    :param exponent: знаковый 8-битный экспонент (обычно фиксированный для команды)
    :return: преобразованное число float
    """
    if raw & 0x8000:  # знак мантиссы
        raw = -((~raw + 1) & 0xFFFF)

    return raw * (2 ** exponent)

