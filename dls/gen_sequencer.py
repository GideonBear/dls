from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from math import isnan
from pathlib import Path

from pandas import read_csv

from .chip import Chip, Pin
from .gen_file import gen_data


class Args(argparse.Namespace):
    instructions_file: Path
    output_pins_file: Path


def parse_args() -> Args:
    parser = argparse.ArgumentParser('gen_sequencer')

    parser.add_argument(
        'instructions_file',
        type=Path,
    )
    parser.add_argument(
        'output_pins_file',
        type=Path,
    )

    return parser.parse_args(namespace=Args())


def bools(num: int) -> Sequence[bool]:
    bin_repr = bin(num)[2:].zfill(4)
    assert len(bin_repr) == 4, (bin_repr, len(bin_repr))
    res = tuple(bool(int(bit)) for bit in bin_repr)
    assert len(res) == 4, (res, len(res))
    return res


def extract_instructions(file: Path, output_pins: list[str]) -> dict[Sequence[bool], tuple[Sequence[int], Sequence[int], Sequence[int]]]:
    df = read_csv(file)
    return {
        bools(row['Instruction dec']):
        (
            get_output_pins(row['cycle1'], output_pins),
            get_output_pins(row['cycle2'], output_pins),
            get_output_pins(row['cycle3'], output_pins),
        )
        for index, row
        in df.iterrows()
    }


def get_output_pins(s: str, output_pins: list[str]) -> Sequence[int]:
    if isinstance(s, float):
        assert isnan(s)
        names = []
    else:
        names = s.split(' ')
    return [output_pins.index(name) for name in names]


def extract_output_pins(file: Path) -> list[str]:
    df = read_csv(file)
    return df['Naam'].to_list()


def main() -> None:
    args = parse_args()

    outfiles = [Path(f'SEQUENCER{i}.txt') for i in range(1, 4)]

    output_pins = extract_output_pins(args.output_pins_file)
    instructions = extract_instructions(args.instructions_file, output_pins)

    inps = [
        Chip.input(Pin(name=f'instruction {i}'))
        for i
        in range(4)
    ]

    un_inpss = [
        Chip('BIN4UNY', inps, 16)
        for i
        in range(4)
    ]

    oroutss = [
        [
            Chip('MOR16', 16, 0)  # TODO: 16 -> [...]
            for j
            in range(16)
        ]
        for i
        in range(4)
    ]

    outss = [
        [
            Chip.output(Pin(orout, 0, name=name))
            for name, orout
            in zip(output_pins, orouts)
        ]
        for i, orouts
        in enumerate(oroutss)
    ]

    print('Generating json...')
    datas = [gen_data(outs, outfile.with_suffix('').name) for outs, outfile in zip(outss, outfiles)]
    print(f'Writing json to {", ".join(map(str, outfiles))}...')
    [outfile.write_text(json.dumps(data, indent=4)) for data, outfile in zip(datas, outfiles)]


if __name__ == '__main__':
    main()
