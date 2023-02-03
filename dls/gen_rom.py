import json
import sys
from argparse import ArgumentParser, Namespace
from collections.abc import Sequence, Iterator
from pathlib import Path
from typing import TypeVar, NoReturn

from .chip import Chip, Pin
from .gen_file import gen_data

from colorama import Fore


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
    parser.add_argument('-s', '--show-data', action='store_true')
    return parser.parse_args()


def fatal(msg: str) -> NoReturn:
    print(f'{Fore.LIGHTRED_EX}ERROR ENCOUNTERED:{Fore.RESET}')
    print(msg)
    sys.exit(1)


def main() -> None:
    print('Parsing args...')
    args = parse_args()

    print('Reading data...')
    if not args.bin_file.exists():
        fatal(f'Input file {args.bin_file} does not exist.')
    inbin_raw: bytes = args.bin_file.read_bytes()
    print('Processing data...')
    if not len(inbin_raw) % 2 == 0:
        fatal('Expected 16-bit chunks')
    inbin = [bools(inbin_raw[i:i+2]) for i in range(0, len(inbin_raw), 2)]
    assert all(len(chunk) == 16 for chunk in inbin), (
        f'post-processing 16-bit chunk check failed\n'
        f'{", ".join(str(len(x)) for x in inbin)}'
    )

    if args.show_data:
        for chunk in inbin:
            print(''.join('1' if bit else '0' for bit in chunk))
        sys.exit()

    print('Constructing chip tree...')
    outfile: Path = args.output or args.bin_file.with_name(args.bin_file.name.upper()).with_suffix('.txt')

    inp = Chip.input(Pin(name='Address', wire_type=3))[0]
    trash = Chip.input(Pin(name='Trash'))[0]

    on = Chip('ON', [trash], 1)[0]
    decoder = Chip('16 BIT DECODER', [inp], 16)

    open_outputs = [
        Chip(
            '16 BIT ENCODER',
            [on if bit else Pin() for bit in chunk],
            1,
        )
        for chunk in inbin
    ]
    open_outputs_len = len(open_outputs)

    curr_bit = 0
    while len(open_outputs) > 1:
        if curr_bit > 15:
            fatal('Too long; 16+ bit addresses are not supported yet. Contact the developer for more info.')
        new = []
        for chunk in chunked(open_outputs, 2):
            try:
                first, second = chunk
            except ValueError:
                fatal(
                    'Non-power-of-two lenght binary files are not supported yet. Contact the developer for more info.\n'
                    f'{open_outputs_len}\n'
                    'Consider padding the file.\n'
                    f'Encountered lenght {len(chunk)} chunk'
                )
            print(f'Found needed select for {first.name}, {second.name}')
            new.append(Chip('16SELECT', [first[0], second[0], decoder[15 - curr_bit]], 1))
        open_outputs = new
        curr_bit += 1

    selector_output, = open_outputs
    out = Chip.output(Pin(selector_output, 0, name='Out', wire_type=3))

    print('Generating json...')
    data = gen_data(out, outfile.with_suffix('').name)
    print(f'Writing json to {outfile}...')
    outfile.write_text(json.dumps(data, indent=4))

    print(f'{Fore.LIGHTGREEN_EX}Done.{Fore.RESET}')


if __name__ == '__main__':
    main()
