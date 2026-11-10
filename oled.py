import framebuf


class SSD1306:
    def __init__(self, i2c, address=0x3C, width=128, height=64):
        if width != 128 or height != 64:
            raise ValueError("This lightweight driver supports 128x64 displays")
        self.i2c = i2c
        self.address = address
        self.width = width
        self.height = height
        self.buffer = bytearray(width * height // 8)
        self.framebuffer = framebuf.FrameBuffer(
            self.buffer, width, height, framebuf.MONO_VLSB
        )
        self._initialize()

    def _command(self, value):
        self.i2c.writeto(self.address, bytes((0x00, value)))

    def _initialize(self):
        for command in (
            0xAE,
            0xD5,
            0x80,
            0xA8,
            0x3F,
            0xD3,
            0x00,
            0x40,
            0x8D,
            0x14,
            0x20,
            0x00,
            0xA1,
            0xC8,
            0xDA,
            0x12,
            0x81,
            0xCF,
            0xD9,
            0xF1,
            0xDB,
            0x40,
            0xA4,
            0xA6,
            0x2E,
            0xAF,
        ):
            self._command(command)
        self.fill(0)
        self.show()

    def fill(self, color):
        self.framebuffer.fill(color)

    def text(self, value, x, y, color=1):
        self.framebuffer.text(value, x, y, color)

    def show(self):
        for command in (0x21, 0x00, self.width - 1, 0x22, 0x00, 7):
            self._command(command)
        for offset in range(0, len(self.buffer), 32):
            self.i2c.writeto(
                self.address, b"\x40" + self.buffer[offset : offset + 32]
            )

    def deinit(self):
        self._command(0xAE)
