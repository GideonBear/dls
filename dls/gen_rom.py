import json
import sys
from argparse import ArgumentParser
from pathlib import Path

from .chip import Chip, Pin
from .gen_file import gen_data


parser = ArgumentParser('gen_rom')
parser.add_argument('bin_file', type=Path)
parser.add_argument('-o', '--output', type=Path)
args = parser.parse_args()

inbin_raw: bytes = args.bin_file.read_bytes()
if not len(inbin_raw) % 2 == 0:
    print('ERROR: Expected 16-bit chunks')
    sys.exit(1)
inbin = [inbin_raw[i:i+2] for i in range(0, len(inbin_raw), 2)]
print(f'Read data: {inbin}')

outfile: Path = args.output or args.bin_file.with_suffix('.txt').with_name(args.bin_file.name.upper())


inp = Chip.input(Pin(name='Address', wire_type=3))


out = Chip.output(Pin(..., 0, name='Out', wire_type=3))

data = gen_data(out, outfile.with_suffix('').name)
outfile.write_text(json.dumps(data, indent=4))
