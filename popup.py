from typing import Callable
from dataclasses import dataclass


@dataclass
class Popup:
    top: int
    bot: int
    left: int
    right: int
    text: str
    onClose: Callable


@dataclass
class PopupInput:
    def process(self, msg):
        pass
