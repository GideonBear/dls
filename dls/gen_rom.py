import json
import sys
from argparse import ArgumentParser, Namespace
from collections.abc import Sequence, Iterator
from pathlib import Path
from typing import TypeVar

from .chip import Chip, Pin
from .gen_file import gen_data


T = TypeVar('T')


def chunks(lst: Sequence[T], n: int) -> Iterator[Sequence[T]]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def bools(b: bytes) -> Sequence[bool]:
    return [bool(int(bit)) for bit in bin(int(b.hex(), 16))[2:]]


def parse_args() -> Namespace:
    parser = ArgumentParser('gen_rom')
    parser.add_argument('bin_file', type=Path)
    parser.add_argument('-o', '--output', type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    inbin_raw: bytes = args.bin_file.read_bytes()
    if not len(inbin_raw) % 2 == 0:
        print('ERROR: Expected 16-bit chunks')
        sys.exit(1)
    inbin = [bools(inbin_raw[i:i+2]) for i in range(0, len(inbin_raw), 2)]
    bits = len(inbin).bit_length()
    print(f'Read data')

    outfile: Path = args.output or args.bin_file.with_name(args.bin_file.name.upper()).with_suffix('.txt')

    inp = Chip.input(Pin(name='Address', wire_type=3))

    on = Chip('NOT', 1, 1)[0]
    decoder = Chip('16 BIT DECODER', [inp[0]], 16)

    open_outputs = [
        Chip(
            '16 BIT ENCODER',
            [on if bit else Pin() for bit in chunk],
            1,
        )
        for chunk in inbin
    ]

    curr_bit = 0
    while len(open_outputs) > 1:
        if curr_bit > 15:
            raise ValueError('Data too long')
        new = []
        for first, second in chunks(open_outputs, 2):
            new.append(Chip('16SELECT', [first[0], second[0], decoder[curr_bit]], 1))
        open_outputs = new
        curr_bit += 1

    selector_output, = open_outputs
    out = Chip.output(Pin(selector_output, 0, name='Out', wire_type=3))

    data = gen_data(out, outfile.with_suffix('').name)
    outfile.write_text(json.dumps(data, indent=4))

    print('Done.')


if __name__ == '__main__':
    main()
