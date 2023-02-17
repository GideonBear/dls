from __future__ import annotations

import argparse
import json
from collections import defaultdict
from collections.abc import Sequence, Mapping, Callable, MutableSequence
from math import isnan
from pathlib import Path
from typing import cast, TypeVar, overload

from pandas import read_csv, DataFrame as DF

from .chip import Chip, Pin
from .gen_file import gen_data


T = TypeVar('T')
TF = TypeVar('TF')


class Args(argparse.Namespace):
    instructions_file: Path
    output_pins_file: Path
    debug: bool


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
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Show debugging data',
    )

    return parser.parse_args(namespace=Args())


def extract_instructions(
    file: Path
) -> dict[int, Sequence[Sequence[str]]]:
    df = read_csv(file)
    return {
        row['Instruction dec']:
        (
            get_output_pins(row['cycle1']),
            get_output_pins(row['cycle2']),
            get_output_pins(row['cycle3']),
        )
        for index, row
        in df.iterrows()
    }


def process_instructions(
    instructions: dict[int, Sequence[Sequence[str]]]
) -> Sequence[dict[int, Sequence[str]]]:
    df = DF(instructions)
    return cast(
        Sequence[dict[int, Sequence[str]]],
        df.to_dict(orient='records')
    )


def create_output_input_map(
    instructions: dict[int, Sequence[str]],
    output_pins: Sequence[str]
) -> Sequence[Sequence[int] | None]:
    output_input_map = defaultdict(list)
    for i, outputs in instructions.items():
        for output in outputs:
            output_input_map[output_pins.index(output)].append(i)
    return intmap_to_list(
        output_input_map,
        length=len(output_pins),
    )

@overload
def intmap_to_list(
    mapping: Mapping[int, T],
    length: int,
) -> Sequence[T | None]: ...
@overload
def intmap_to_list(
    mapping: Mapping[int, T],
    length: int,
    filler: TF,
) -> Sequence[T | TF]: ...
def intmap_to_list(
    mapping: Mapping[int, T],
    length: int,
    filler=None,
) -> Sequence[T | TF]:
    return [mapping.get(i, filler) for i in range(length)]


def get_output_pins(s: str) -> Sequence[str]:
    if isinstance(s, float):
        assert isnan(s)
        names = []
    else:
        names = s.split(' ')
    return names


def extract_output_pins(file: Path) -> Sequence[str]:
    df = read_csv(file)
    return df['Naam'].to_list()


def pad(
    l: list[T],
    length: int,
    filler_factory: Callable[[], T],
) -> Sequence[T]:
    return l + [filler_factory() for _ in range(length - len(l))]


def main() -> None:
    args = parse_args()

    outfiles = [Path(f'SEQUENCER{i}.txt') for i in range(1, 4)]

    output_pins = extract_output_pins(args.output_pins_file)
    instructions = extract_instructions(args.instructions_file)
    processed_instructionss = process_instructions(instructions)
    assert len(processed_instructionss) == 3, len(processed_instructionss)
    output_input_maps = [
        create_output_input_map(processed_instructions, output_pins)
        for processed_instructions
        in processed_instructionss
    ]

    if args.debug:
        from pprint import pprint
        pprint(instructions)
        pprint(processed_instructionss)
        pprint(output_input_maps)

    inpss = [
        [
            Chip.input(Pin(name=f'instruction {i}'))
            for i
            in range(4)
        ]
        for _ in range(1, 4)
    ]

    un_inpss = [
        Chip('BIN4UNY', inps, 16)
        for inps
        in inpss
    ]

    oroutss = [
        [
            Chip('MOR16', (
                16
                if output_input is None
                else pad([
                    un_inps[15 - j]
                    for j
                    in output_input
                ], 16, Pin)
            ), 0)
            for output_input
            in output_input_map
        ]
        for output_input_map, un_inps
        in zip(output_input_maps, un_inpss)
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
