import json
import sys

from formats.akao import FinalFantasy6SPC

with open(sys.argv[1], 'rb') as f:
    spc = FinalFantasy6SPC(f)

print(json.dumps(spc.ram.tracks))