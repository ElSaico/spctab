from collections import namedtuple
from datetime import datetime
from io import BytesIO
from struct import unpack
from typing import BinaryIO

SPC_MAGIC = b"SNES-SPC700 Sound File Data v0.30\x1a\x1a"


class ID666:
    def __init__(
        self,
        title,
        game,
        dumper,
        comments,
        date,
        playtime,
        fade,
        artist,
        disable_default_channel,
        emulator,
    ):
        self.title = title.strip(b"\x00").decode("UTF-8")
        self.game = game.strip(b"\x00").decode("UTF-8")
        self.dumper = dumper.strip(b"\x00").decode("UTF-8")
        self.comments = comments.strip(b"\x00").decode("UTF-8")
        try:
            self.date = datetime.strptime(date.strip(b"\x00").decode(), "YYYYMMDD")
        except ValueError:
            self.date = None
        self.playtime = int(playtime.strip(b"\x00"))
        self.fade = int(fade.strip(b"\x00"))
        self.artist = artist.strip(b"\x00").decode("UTF-8")
        self.disable_default_channel = disable_default_channel
        self.emulator = emulator


Registers = namedtuple("Registers", "pc a x y psw sp")


class SPC:
    def __init__(self, f: BinaryIO):
        self.magic = f.read(35)
        if self.magic != SPC_MAGIC:
            raise Exception("Invalid SPC file header")
        self.id666_flag = f.read(1)
        self.version_minor = ord(f.read(1))
        if self.version_minor != 30:
            raise Exception(
                f"Invalid SPC file version: expected 30, got {self.version_minor}"
            )
        self.registers = Registers._make(unpack("<H5B2x", f.read(9)))
        self.id666 = ID666(*unpack("32s32s16s32s11s3s5s32s?B45x", f.read(210)))
        self.raw_ram = BytesIO(f.read(65536))
        self.dsp_registers = f.read(128)
        f.read(64)
        self.extra_ram = f.read(64)
