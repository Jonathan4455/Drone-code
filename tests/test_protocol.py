import unittest

from protocol import decode_joystick, encode_joystick


class ProtocolTests(unittest.TestCase):
    def test_round_trip(self):
        self.assertEqual(decode_joystick(encode_joystick(0, 65535)), (0, 65535))

    def test_four_axis_round_trip(self):
        axes = (0, 12345, 54321, 65535)
        self.assertEqual(decode_joystick(encode_joystick(*axes)), axes)

    def test_decodes_legacy_two_axis_packet(self):
        self.assertEqual(decode_joystick(b"123,456"), (123, 456))

    def test_rejects_wrong_shape(self):
        for payload in (b"", b"1", b"1,2,3", b"1,2,3,4,5", b"1,"):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    decode_joystick(payload)

    def test_rejects_out_of_range_values(self):
        for payload in (
            b"-1,2",
            b"65536,2",
            b"1,65536",
            b"1,2,3,65536",
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    decode_joystick(payload)

    def test_rejects_non_ascii_or_oversized_packets(self):
        for payload in (b"\xff,1", b"1" * 33):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    decode_joystick(payload)

    def test_encoder_rejects_non_integer_values(self):
        with self.assertRaises(ValueError):
            encode_joystick(1.5, 2)
        with self.assertRaises(ValueError):
            encode_joystick(1, 2, 3)
        with self.assertRaises(ValueError):
            encode_joystick(1, 2, 3, True)


if __name__ == "__main__":
    unittest.main()
