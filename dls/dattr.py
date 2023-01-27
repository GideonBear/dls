from collections.abc import Iterable
from typing import TypeVar, Generic


Tv = TypeVar('Tv')


class Dattr(Generic[Tv]):

    d: dict[str, Tv]

    def __init__(self, d: dict[str, Tv]):
        self.__dict__['d'] = d

    def __getattr__(self, item: str) -> Tv:
        return self.d[item]

    def __setattr__(self, key: str, value: Tv) -> None:
        self.d[key] = value

    def keys(self) -> Iterable[str]:
        return self.d.keys()
