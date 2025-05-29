from io import BytesIO
from struct import unpack

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

OPCODES_V2 = {
    0xD2: "EVENT_TEMPO",
    0xD3: "EVENT_TEMPO_FADE",
    0xD4: "EVENT_VOLUME",
    0xD5: "EVENT_VOLUME_FADE",
    0xD6: "EVENT_PAN",
    0xD7: "EVENT_PAN_FADE",
    0xD8: "EVENT_ECHO_VOLUME",
    0xD9: "EVENT_ECHO_VOLUME_FADE",
    0xDA: "EVENT_TRANSPOSE_ABS",
    0xDB: "EVENT_PITCH_SLIDE_ON",
    0xDC: "EVENT_PITCH_SLIDE_OFF",
    0xDD: "EVENT_TREMOLO_ON",
    0xDE: "EVENT_TREMOLO_OFF",
    0xDF: "EVENT_VIBRATO_ON",
    0xE0: "EVENT_VIBRATO_OFF",
    0xE1: "EVENT_NOISE_FREQ",
    0xE2: "EVENT_NOISE_ON",
    0xE3: "EVENT_NOISE_OFF",
    0xE4: "EVENT_PITCHMOD_ON",
    0xE5: "EVENT_PITCHMOD_OFF",
    0xE6: "EVENT_ECHO_FEEDBACK_FIR",
    0xE7: "EVENT_ECHO_ON",
    0xE8: "EVENT_ECHO_OFF",
    0xE9: "EVENT_PAN_LFO_ON",
    0xEA: "EVENT_PAN_LFO_OFF",
    0xEB: "EVENT_OCTAVE",
    0xEC: "EVENT_OCTAVE_UP",
    0xED: "EVENT_OCTAVE_DOWN",
    0xEE: "EVENT_LOOP_START",
    0xEF: "EVENT_LOOP_END",
    0xF0: "EVENT_LOOP_BREAK",
    0xF1: "EVENT_GOTO",
    0xF2: "EVENT_SLUR_ON",
    0xF3: "EVENT_PROGCHANGE",
    0xF4: "EVENT_VOLUME_ENVELOPE",
    0xF5: "EVENT_SLUR_OFF",
    0xF6: "EVENT_UNKNOWN2",
    0xF7: "EVENT_TUNING",
    0xF8: "EVENT_END",
    0xF9: "EVENT_END",
    0xFA: "EVENT_END",
    0xFB: "EVENT_END",
    0xFC: "EVENT_END",
    0xFD: "EVENT_END",
    0xFE: "EVENT_END",
    0xFF: "EVENT_END",
}

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


class AkaoRAM:
    ram_offset: int
    opcodes: dict[int, str]
    notes: list[str]
    note_durations: list[int]

    def __init__(self, io: BytesIO):
        io.seek(self.ram_offset)
        self.raw = BytesIO(io.read(4096))  # TODO does size differ between versions?

    def get_instructions(self, addr: int):
        self.raw.seek(addr)
        instructions = []
        min_opcode = min(self.opcodes)
        while True:
            opcode = ord(self.raw.read(1))
            if opcode >= min_opcode:
                instruction: dict[str, str | int] = {"event": self.opcodes[opcode]}
                match instruction["event"]:
                    case "EVENT_UNKNOWN2":
                        instruction["arg1"], instruction["arg2"] = unpack(
                            "BB", self.raw.read(2)
                        )
                    # V1: first parameter is short
                    case "EVENT_VOLUME_FADE" | "EVENT_PAN_FADE" | "EVENT_TEMPO_FADE":
                        instruction["length"], instruction["value"] = unpack(
                            "BB", self.raw.read(2)
                        )
                    case "EVENT_ECHO_VOLUME_FADE":
                        instruction["length"], instruction["value"] = unpack(
                            "Bb", self.raw.read(2)
                        )
                    # V1: the order of parameters is delay, length, semitones
                    case "EVENT_PITCH_SLIDE_ON":
                        (
                            instruction["semitones"],
                            instruction["delay"],
                            instruction["length"],
                        ) = unpack("bBB", self.raw.read(3))
                    case "EVENT_PITCH_SLIDE":
                        instruction["length"], instruction["semitones"] = unpack(
                            "Bb", self.raw.read(2)
                        )
                    case "EVENT_VIBRATO_ON" | "EVENT_TREMOLO_ON":
                        (
                            instruction["delay"],
                            instruction["rate"],
                            instruction["depth"],
                        ) = unpack("BBB", self.raw.read(3))
                    case "EVENT_PAN_LFO_ON":
                        instruction["depth"], instruction["rate"] = unpack(
                            "BB", self.raw.read(2)
                        )
                    case "EVENT_PAN_LFO_ON_WITH_DELAY":
                        (
                            instruction["delay"],
                            instruction["rate"],
                            instruction["depth"],
                        ) = unpack("BBB", self.raw.read(3))
                    case "EVENT_ECHO_FEEDBACK_FIR":
                        instruction["feedback"], instruction["fir"] = unpack(
                            "bB", self.raw.read(2)
                        )
                    case "EVENT_ECHO_FEEDBACK_FADE" | "EVENT_ECHO_FIR_FADE":
                        instruction["length"], instruction["value"] = unpack(
                            ">HB", self.raw.read(3)
                        )
                    case "EVENT_LOOP_BREAK" | "EVENT_CPU_CONTROLED_JUMP_V2":
                        instruction["value"], instruction["addr"] = unpack(
                            ">BH", self.raw.read(3)
                        )
                    case "EVENT_GOTO" | "EVENT_CPU_CONTROLED_JUMP":
                        (instruction["addr"],) = unpack(">H", self.raw.read(2))
                    case (
                        "EVENT_UNKNOWN1"
                        | "EVENT_NOP1"
                        | "EVENT_VOLUME"
                        | "EVENT_PAN"
                        | "EVENT_NOISE_FREQ"
                        | "EVENT_OCTAVE"
                        | "EVENT_TUNING"
                        | "EVENT_PROGCHANGE"
                        | "EVENT_VOLUME_ENVELOPE"
                        | "EVENT_GAIN_RELEASE"
                        | "EVENT_DURATION_RATE"
                        | "EVENT_ADSR_AR"
                        | "EVENT_ADSR_DR"
                        | "EVENT_ADSR_SL"
                        | "EVENT_ADSR_SR"
                        | "EVENT_LOOP_START"
                        | "EVENT_ONETIME_DURATION"
                        | "EVENT_JUMP_TO_SFX_LO"
                        | "EVENT_JUMP_TO_SFX_HI"
                        | "EVENT_PLAY_SFX"
                        | "EVENT_TEMPO"
                        | "EVENT_ECHO_VOLUME"
                        | "EVENT_MASTER_VOLUME"
                        | "EVENT_ECHO_FEEDBACK"
                        | "EVENT_ECHO_FIR"
                        | "EVENT_CPU_CONTROLED_SET_VALUE"
                        | "EVENT_IGNORE_MASTER_VOLUME_BY_PROGNUM"
                        | "EVENT_VOLUME_ALT"
                    ):
                        (instruction["value"],) = unpack("B", self.raw.read(1))
                    case "EVENT_TRANSPOSE_ABS" | "EVENT_TRANSPOSE_REL":
                        (instruction["value"],) = unpack("b", self.raw.read(1))
            else:
                instruction = {
                    "event": "EVENT_NOTE",
                    "note": self.notes[opcode // len(self.note_durations)],
                    "duration": self.note_durations[opcode % len(self.note_durations)],
                }
            instructions.append(instruction)
            if instruction["event"] in ["EVENT_GOTO", "EVENT_END"]:
                return instructions


class AkaoV2RAM(AkaoRAM):
    opcodes = OPCODES_V2
    notes = NOTES_V12
    note_durations = NOTE_DURATIONS_V23

    def __init__(self, io: BytesIO):
        super().__init__(io)
        self.ptr = unpack("<8H", self.raw.read(16))
        self.tracks = [self.get_instructions(addr) for addr in self.ptr]


class AkaoV4RAM(AkaoRAM):
    notes = NOTES_V34
    note_durations = NOTE_DURATIONS_V4

    def __init__(self, io: BytesIO):
        super().__init__(io)
        self.addr_base, self.addr_end = unpack("<HH", self.raw.read(4))
        self.ptr = unpack("<8H", self.raw.read(16))
        self.ptr_dup = unpack("<8H", self.raw.read(16))
        self.tracks = [
            self.get_instructions(addr - self.addr_base + 36) for addr in self.ptr
        ]


class ChronoTriggerRAM(AkaoV4RAM):
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


class FinalFantasy6RAM(AkaoV4RAM):
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
