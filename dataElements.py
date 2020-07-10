from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class DataElement:
    _id: Any
    name: str
    dateAdded: str


@dataclass
class Card(DataElement):
    parentId: Any
    content: str = ''
    dueDate: str = ''
    userData: Dict[str, Any] = field(default_factory=dict)


@dataclass
class _List(DataElement):
    parentId: Any


@dataclass
class Board(DataElement):
    desc: str
