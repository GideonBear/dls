from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal


if TYPE_CHECKING:
    from typing_extensions import Self


@dataclass(eq=False)
class Chip:
    name: str
    inputs: Sequence[Pin] | int
    outputs: Sequence[Pin] | int

    def __getitem__(self, index: int) -> Pin:
        return Pin(self, index)

    @classmethod
    def input(cls, pin: Pin) -> Self:
        return cls('SIGNAL IN', [], [pin])

    @classmethod
    def output(cls, pin: Pin) -> Self:
        return cls('SIGNAL OUT', [pin], [])


@dataclass(eq=False)
class Pin:
    # implicit-optional doesn't work?
    chip: Chip | None = None
    index: int | None = None
    name: str | None = None
    wire_type: Literal[0, 1, 2, 3] | None = None
