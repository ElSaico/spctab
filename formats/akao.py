from io import BytesIO
from struct import unpack

from formats.spc import SPC

NOTE_DURATIONS_V1 = [
    0xC0,
    0x90,
    0x60,
    0x48,
    0x40,
    0x30,
    0x24,
    0x20,
    0x18,
    0x10,
    0x0C,
    0x08,
    0x06,
    0x04,
    0x03,
]
NOTE_DURATIONS_V23 = [
    0xC0,
    0x90,
    0x60,
    0x40,
    0x48,
    0x30,
    0x20,
    0x24,
    0x18,
    0x10,
    0x0C,
    0x08,
    0x06,
    0x04,
    0x03,
]
NOTE_DURATIONS_V4 = [
    0xC0,
    0x60,
    0x40,
    0x48,
    0x30,
    0x20,
    0x24,
    0x18,
    0x10,
    0x0C,
    0x08,
    0x06,
    0x04,
    0x03,
]
NOTES_COMMON = ["C", "C#", "D", "E", "E#", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTES_V12 = NOTES_COMMON + ["REST", "TIE"]
NOTES_V34 = NOTES_COMMON + ["TIE", "REST"]
OPCODES_V4_COMMON = {
    196: "EVENT_VOLUME",
    197: "EVENT_VOLUME_FADE",
    198: "EVENT_PAN",
    199: "EVENT_PAN_FADE",
    200: "EVENT_PITCH_SLIDE",
    201: "EVENT_VIBRATO_ON",
    202: "EVENT_VIBRATO_OFF",
    203: "EVENT_TREMOLO_ON",
    204: "EVENT_TREMOLO_OFF",
    205: "EVENT_PAN_LFO_ON",
    206: "EVENT_PAN_LFO_OFF",
    207: "EVENT_NOISE_FREQ",
    208: "EVENT_NOISE_ON",
    209: "EVENT_NOISE_OFF",
    210: "EVENT_PITCHMOD_ON",
    211: "EVENT_PITCHMOD_OFF",
    212: "EVENT_ECHO_ON",
    213: "EVENT_ECHO_OFF",
    214: "EVENT_OCTAVE",
    215: "EVENT_OCTAVE_UP",
    216: "EVENT_OCTAVE_DOWN",
    217: "EVENT_TRANSPOSE_ABS",
    218: "EVENT_TRANSPOSE_REL",
    219: "EVENT_TUNING",
    220: "EVENT_PROGCHANGE",
    221: "EVENT_ADSR_AR",
    222: "EVENT_ADSR_DR",
    223: "EVENT_ADSR_SL",
    224: "EVENT_ADSR_SR",
    225: "EVENT_ADSR_DEFAULT",
    226: "EVENT_LOOP_START",
    227: "EVENT_LOOP_END",
    228: "EVENT_SLUR_ON",
    229: "EVENT_SLUR_OFF",
    230: "EVENT_LEGATO_ON",
    231: "EVENT_LEGATO_OFF",
    232: "EVENT_ONETIME_DURATION",
    233: "EVENT_JUMP_TO_SFX_LO",
    234: "EVENT_JUMP_TO_SFX_HI",
    235: "EVENT_END",
    236: "EVENT_END",
    237: "EVENT_END",
    238: "EVENT_END",
    239: "EVENT_END",
    240: "EVENT_TEMPO",
    241: "EVENT_TEMPO_FADE",
    242: "EVENT_ECHO_VOLUME",
    243: "EVENT_ECHO_VOLUME_FADE",
}


class AkaoV4RAM:
    def __init__(self, io: BytesIO, ram_offset: int, opcodes: dict[int, str]):
        io.seek(ram_offset)
        self.opcodes = opcodes
        self.raw = BytesIO(io.read(4096))
        self.addr_base, self.addr_end = unpack("<HH", self.raw.read(4))
        self.ptr = unpack("<8H", self.raw.read(16))
        self.ptr_dup = unpack("<8H", self.raw.read(16))
        self.tracks = [self.get_instructions(addr) for addr in self.ptr]

    def get_instructions(self, addr):
        self.raw.seek(addr - self.addr_base + 36)
        instructions = []
        while True:
            opcode = ord(self.raw.read(1))
            if opcode >= 0xC3:
                instruction = {"event": self.opcodes[opcode]}
                match instruction["event"]:
                    case "EVENT_PITCH_SLIDE":
                        instruction["length"], instruction["semitones"] = unpack(
                            "BB", self.raw.read(2)
                        )
                    case "EVENT_PAN_LFO_ON":
                        instruction["depth"], instruction["rate"] = unpack(
                            "BB", self.raw.read(2)
                        )
                    case "EVENT_VIBRATO_ON" | "EVENT_TREMOLO_ON":
                        (
                            instruction["delay"],
                            instruction["rate"],
                            instruction["depth"],
                        ) = unpack("BBB", self.raw.read(3))
                    case (
                        "EVENT_ECHO_VOLUME_FADE"
                        | "EVENT_ECHO_FEEDBACK_FADE"
                        | "EVENT_TEMPO_FADE"
                        | "EVENT_VOLUME_FADE"
                        | "EVENT_PAN_FADE"
                        | "EVENT_ECHO_FIR_FADE"
                    ):
                        instruction["length"], instruction["value"] = unpack(
                            "BB", self.raw.read(2)
                        )
                    case "EVENT_GOTO":
                        (instruction["addr"],) = unpack(">H", self.raw.read(2))
                    case "EVENT_LOOP_BREAK" | "EVENT_CPU_CONTROLED_JUMP_V2":
                        instruction["value"], instruction["addr"] = unpack(
                            ">BH", self.raw.read(3)
                        )
                    case (
                        "EVENT_VOLUME"
                        | "EVENT_VOLUME_ALT"
                        | "EVENT_MASTER_VOLUME"
                        | "EVENT_LOOP_START"
                        | "EVENT_PROGCHANGE"
                        | "EVENT_TUNING"
                        | "EVENT_NOISE_FREQ"
                        | "EVENT_ADSR_AR"
                        | "EVENT_ADSR_DR"
                        | "EVENT_ADSR_SL"
                        | "EVENT_ADSR_SR"
                        | "EVENT_JUMP_TO_SFX_LO"
                        | "EVENT_ONETIME_DURATION"
                        | "EVENT_PAN"
                        | "EVENT_TRANSPOSE_ABS"
                        | "EVENT_TEMPO"
                        | "EVENT_ECHO_VOLUME"
                        | "EVENT_JUMP_TO_SFX_HI"
                        | "EVENT_CPU_CONTROLED_SET_VALUE"
                        | "EVENT_OCTAVE"
                        | "EVENT_TRANSPOSE_REL"
                    ):
                        instruction["value"] = ord(self.raw.read(1))
            else:
                instruction = {
                    "event": "EVENT_NOTE",
                    "note": NOTES_V34[opcode // len(NOTE_DURATIONS_V4)],
                    "duration": NOTE_DURATIONS_V4[opcode % len(NOTE_DURATIONS_V4)],
                }
            instructions.append(instruction)
            if instruction["event"] in ["EVENT_GOTO", "EVENT_END"]:
                return instructions


class AkaoV4SPC(SPC):
    ram_offset: int
    opcodes: dict[int, str]

    def __init__(self, f):
        super().__init__(f)
        self.ram = AkaoV4RAM(self.raw_ram, self.ram_offset, self.opcodes)


class ChronoTriggerSPC(AkaoV4SPC):
    ram_offset = 8192
    opcodes = OPCODES_V4_COMMON | {
        244: "EVENT_MASTER_VOLUME",
        245: "EVENT_LOOP_BREAK",
        246: "EVENT_GOTO",
        247: "EVENT_ECHO_FEEDBACK_FADE",
        248: "EVENT_ECHO_FIR_FADE",
        249: "EVENT_CPU_CONTROLED_SET_VALUE",
        250: "EVENT_CPU_CONTROLED_JUMP_V2",
        251: "EVENT_PERC_ON",
        252: "EVENT_PERC_OFF",
        253: "EVENT_VOLUME_ALT",
        254: "EVENT_END",
        255: "EVENT_END",
    }


class FinalFantasy6SPC(AkaoV4SPC):
    ram_offset = 7168
    opcodes = OPCODES_V4_COMMON | {
        244: "EVENT_MASTER_VOLUME",
        245: "EVENT_LOOP_BREAK",
        246: "EVENT_GOTO",
        247: "EVENT_ECHO_FEEDBACK_FADE",
        248: "EVENT_ECHO_FIR_FADE",
        249: "EVENT_INC_CPU_SHARED_COUNTER",
        250: "EVENT_ZERO_CPU_SHARED_COUNTER",
        251: "EVENT_IGNORE_MASTER_VOLUME",
        252: "EVENT_CPU_CONTROLED_JUMP",
        253: "EVENT_END",
        254: "EVENT_END",
        255: "EVENT_END",
    }
