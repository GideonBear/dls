from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from dataclasses import dataclass
from operator import attrgetter
from typing import TYPE_CHECKING, Literal


if TYPE_CHECKING:
    from typing_extensions import Self


class BetterRepr:
    def __repr__(self) -> str:
        nodef_f_vals = (
            (f.name, attrgetter(f.name)(self))
            for f in dataclasses.fields(self)
            if attrgetter(f.name)(self) != f.default
        )

        nodef_f_repr = ', '.join(f'{name}={value}' for name, value in nodef_f_vals)
        return f'{self.__class__.__name__}({nodef_f_repr})'


@dataclass(eq=False, repr=False)
class Chip(BetterRepr):
    name: str
    inputs: Sequence[Pin] | int
    outputs: Sequence[Pin] | int

    def __getitem__(self, index: int) -> Pin:
        return Pin(self, index)

    @classmethod
    def input(cls, pin: Pin) -> Pin:
        return cls('SIGNAL IN', [], [pin])[0]

    @classmethod
    def output(cls, pin: Pin) -> Self:
        return cls('SIGNAL OUT', [pin], [])


@dataclass(eq=False, repr=False)
class Pin(BetterRepr):
    # implicit-optional doesn't work?
    chip: Chip | None = None
    index: int | None = None
    name: str | None = None
    wire_type: Literal[0, 1, 2, 3] | None = None
