from dataclasses import dataclass, field
from typing import List


@dataclass
class DataElement:
    key: int
    name: str


@dataclass
class Card(DataElement):
    content: str = ''


@dataclass
class Board(DataElement):
    lists: List['CardList'] = field(default_factory=list)


@dataclass
class CardList(DataElement):
    board: Board
    cards: List[Card] = field(default_factory=list)
