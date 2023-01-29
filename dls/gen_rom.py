import json
import sys
from argparse import ArgumentParser, Namespace
from collections.abc import Sequence, Iterator
from pathlib import Path
from typing import TypeVar, NoReturn

from .chip import Chip, Pin
from .gen_file import gen_data


T = TypeVar('T')


def chunked(lst: Sequence[T], n: int) -> Iterator[Sequence[T]]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def bools(b: bytes) -> Sequence[bool]:
    assert len(b) == 2
    num = int(b.hex(), 16)
    bin_repr = bin(num)[2:].zfill(16)
    assert len(bin_repr) == 16, (bin_repr, len(bin_repr))
    res = [bool(int(bit)) for bit in bin_repr]
    assert len(res) == 16, (res, len(res))
    return res


def parse_args() -> Namespace:
    parser = ArgumentParser('gen_rom')
    parser.add_argument('bin_file', type=Path)
    parser.add_argument('-o', '--output', type=Path)
    return parser.parse_args()


def fatal(msg: str) -> NoReturn:
    print(msg)
    sys.exit(1)


def main() -> None:
    args = parse_args()
    inbin_raw: bytes = args.bin_file.read_bytes()
    if not len(inbin_raw) % 2 == 0:
        fatal('ERROR: Expected 16-bit chunks')
    inbin = [bools(inbin_raw[i:i+2]) for i in range(0, len(inbin_raw), 2)]
    assert all(len(chunk) == 16 for chunk in inbin), (
        f'post-processing 16-bit chunk check failed\n'
        f'{", ".join(str(len(x)) for x in inbin)}'
    )
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
            fatal('Too long; 16+ bit addresses are not supported yet. Ask the developer for more info.')
        new = []
        for first, second in chunked(open_outputs, 2):
            print(f'Found needed select for {first.name}, {second.name}')
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
