"""Strict wire format for two-axis legacy and four-axis joystick telemetry."""


def _validate_axis(value):
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
        or value > 65535
    ):
        raise ValueError("joystick axes must be integers from 0 to 65535")


def encode_joystick(*axes):
    if len(axes) not in (2, 4):
        raise ValueError("joystick packets must contain two or four axes")
    for value in axes:
        _validate_axis(value)
    return ",".join(str(value) for value in axes).encode("ascii")


def decode_joystick(payload):
    if not isinstance(payload, bytes) or len(payload) > 32:
        raise ValueError("joystick packet must be at most 32 bytes")
    try:
        text = payload.decode("ascii")
    except UnicodeError:
        raise ValueError("joystick packet must contain ASCII text")

    fields = text.split(",")
    if len(fields) not in (2, 4) or any(not field.isdigit() for field in fields):
        raise ValueError(
            "joystick packet must contain two or four comma-separated integers"
        )

    axes = tuple(int(field) for field in fields)
    for value in axes:
        _validate_axis(value)
    return axes
