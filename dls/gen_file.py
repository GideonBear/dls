from __future__ import annotations

from collections.abc import Iterator, Sequence, Iterable, Mapping
from typing import TYPE_CHECKING, Union

from .chip import Chip, Pin


if TYPE_CHECKING:
    JSON = Union[Mapping[str, JSON], Sequence[JSON], str, int, float, bool, None]
    JSONObj = Mapping[str, JSON]


def gen_data(
    chip: Chip,
    name: str,
    folder: int = 6,  # 6 = ROM
) -> JSONObj:
    return dict(
        Data=dict(
            name=name,
            Colour=dict(r=1.0, g=0.0, b=0.0, a=1.0),
            NameColour=dict(r=1.0, g=1.0, b=1.0, a=1.0),
            FolderIndex=folder,
            scale=0.1,
        ),
        ChipDependecies=[],  # spelling error
        savedComponentChips=tuple(gen_chip_datas(chip))
    )


def gen_chip_datas(trunk_chip: Chip) -> Iterator[JSONObj]:
    chips: list[Chip] = []
    stack1: list[Chip] = [trunk_chip]
    q2: list[Chip] = [trunk_chip]
    while stack1:
        chip = stack1.pop()
        print(f'Processing {chip}')
        if chip in chips:
            continue
        chips.append(chip)
        children = [pin.chip for pin in chip.inputs if pin.chip]
        print(f'Extending both with {children=}')
        stack1.extend(children)
        q2.extend(children)
    print('Entering queue 2')
    for chip in q2:
        print(f'Processing {chip}')
        yield dict(
            chipName=chip.name,
            inputPins=get_pin_datas(chip.inputs, chips),
            outputPins=(
                get_pin_datas(chip.outputs, chips)
                if not isinstance(chip.outputs, int)
                else [{} for _ in range(chip.outputs)]
            ),
        )


def get_pin_datas(pins: Iterable[Pin], chips: Sequence[Chip]) -> list[JSONObj]:
    return [
        dict(
            name=pin.name,  # None -> null
            parentChipIndex=chips.index(pin.chip) if pin.chip else None,
            parentChipOutputIndex=pin.index,
            wireType=pin.wire_type,  # None -> null
        )
        for pin
        in pins
    ]
