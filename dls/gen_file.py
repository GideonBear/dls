from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from typing import TYPE_CHECKING, MutableMapping, TypeVar, Union

from .chip import Chip, Pin


if TYPE_CHECKING:
    T = TypeVar('T')

    JSON = Union[Mapping[str, JSON], Sequence[JSON], str, int, float, bool, None]
    JSONObj = Mapping[str, JSON]


def remove_duplicates(lst: list[T]) -> list[T]:
    new = []
    for a in lst:
        if a not in new:
            new.append(a)
    return new


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
        savedComponentChips=tuple(gen_chip_datas(chip)),
    )


def gen_chip_datas(trunk_chip: Chip) -> Iterator[JSONObj]:
    chips: list[Chip] = [trunk_chip]
    stack1: list[Chip] = [trunk_chip]
    while stack1:
        chip = stack1.pop()
        if not isinstance(chip.inputs, int):
            children = remove_duplicates(
                [pin.chip for pin in chip.inputs if pin.chip and pin.chip not in chips]
            )
            chips.extend(children)
            stack1.extend(children)
    for chip in chips:
        yield dict(
            chipName=chip.name,
            inputPins=get_pin_datas(chip.inputs, chips, is_input=True),
            outputPins=get_pin_datas(chip.outputs, chips, is_input=False),
        )


def get_pin_datas(
    pins: Iterable[Pin] | int,
    chips: Sequence[Chip],
    is_input: bool,
) -> Sequence[JSONObj]:
    datas: Iterator[MutableMapping[str, JSON]]
    if isinstance(pins, int):
        datas = (
            dict(
                parentChipIndex=-1,
                parentChipOutputIndex=-1,
            )
            for _ in range(pins)
        )
    else:
        datas = (
            dict(
                name=pin.name,
                parentChipIndex=chips.index(pin.chip) if pin.chip is not None else -1,
                parentChipOutputIndex=pin.index if pin.index is not None else -1,
                wireType=pin.wire_type,
            )
            for pin in pins
        )
    return [
        (data, not is_input and (
            data.pop('parentChipIndex'), data.pop('parentChipOutputIndex')
        ))[0]
        for data in datas
    ]
