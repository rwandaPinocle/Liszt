from dataclasses import dataclass, field
from typing import List, Dict, Callable, Tuple
from blessings import Terminal
import curses

EXIT = 'exit'
NO_EXIT = 'no_exit'

term = Terminal()


class Focus:
    '''
    The Focus object tracks when screen object has the focus.
    It captures keypresses and forwards them to the currently focused object.
    '''
    def __init__(self, win, currentObj):
        self.win = win
        self.currentObj = currentObj

    def handleKey(self):
        try:
            key = self.win.getkey()
        except Exception:
            return NO_EXIT
        if key == 'q':
            return EXIT
        with term.hidden_cursor():
            self.currentObj.process(key)
        

@dataclass
class DataElement:
    key: int
    name: str


def noOp():
    return


def viewIdxs(totalSize, showCount, idx):
    minIdx = min(totalSize - showCount - 1, idx)
    maxIdx = minIdx + showCount
    return (minIdx, maxIdx)


# TODO: Change color based on focus
@dataclass
class Menu:
    title: str
    top: int
    height: int
    left: int
    width: int
    items: List[DataElement]
    currentIdx: int = 0

    def clear(self):
        for row in range(self.height):
            move = term.move(row, self.left)
            space = ' ' * self.width
            print(f'{move}{space}')
        return

    def draw(self):
        self.clear()
        move = term.move(self.left, self.top)
        text = f'{self.title[:self.width]}'
        text = f'{text:^{self.width}}'
        print(f'{move}{term.yellow_underline(text)}')

        totalSize = len(self.items)
        showCount = self.height - 1
        idx = self.currentIdx
        minIdx, maxIdx = viewIdxs(totalSize, showCount, idx)
        for delta, item in enumerate(self.items[minIdx:maxIdx+1]):
            lPad = ' '
            if item == self.items[self.currentIdx]:
                name = item.name[:self.width]
                name = term.magenta(f'{lPad + name:<{self.width}}')
            else:
                name = item.name[:self.width]
                name = term.blue(f'{lPad + name:<{self.width}}')

            row = self.top + delta + 1
            move = term.move(row, self.left)
            # print(f'{move}{" "*self.width}')
            print(f'{move}{name}')
        return

    def process(self, msg):
        if msg == 'j':
            self.currentIdx += 1
        if msg == 'k':
            self.currentIdx -= 1

        self.currentIdx = max(min(self.currentIdx, len(self.items) - 1), 0)
        self.draw()
        return


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


def main(win):
    win.nodelay(True)
    win.clear()

    testItems = [Card(idx, str(idx)*5) for idx in range(5)]
    testMenu = Menu("Boards", 0, 20, 0, 20, testItems)
    focus = Focus(win, testMenu)
    done = False
    while not done:
        result = focus.handleKey()
        if result == EXIT:
            done = True
curses.wrapper(main)
