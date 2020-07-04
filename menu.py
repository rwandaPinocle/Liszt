from dataclasses import dataclass, field
from typing import List
import asyncio

from blessed import Terminal

from consts import (
    styleFBg,
    styleUfBg,
    styleTxt,
    styleFTitle,
    styleUfTitle,
    styleSelectTxt,
    COROUTINE_SLEEP,
    term)
from dataElements import DataElement
from focus import Focus


def viewIdxs(totalSize, showCount, idx):
    minIdx = min(totalSize - showCount - 1, idx - (showCount//2))
    minIdx = max(minIdx, 0)

    maxIdx = minIdx + showCount
    return (minIdx, maxIdx)


@dataclass
class Menu:
    title: str
    top: int
    height: int
    left: int
    width: int
    focus: Focus
    items: List[DataElement] = field(default_factory=list)
    currentIdx: int = 0
    drawFlag: bool = False

    def hasFocus(self):
        return self.focus.currentObj == self

    def clear(self):
        for row in range(self.height):
            move = term.move(row + self.top, self.left)
            style = styleFBg if self.hasFocus() else styleUfBg

            space = style(' ' * self.width)
            print(f'{move}{space}')
        return

    def makeTitleStr(self):
        style = styleFTitle if self.hasFocus() else styleUfTitle
        move = term.move(self.top, self.left)

        trimmedName = f'{self.title[:self.width]}'
        alignedName = f'{trimmedName:^{self.width}}'
        title = f'{move}{style(alignedName)}'
        return title

    def makeItemStrs(self):
        totalSize = len(self.items)
        showCount = self.height - 1

        idx = self.currentIdx
        minIdx, maxIdx = viewIdxs(totalSize, showCount, idx)

        result = ''
        for delta, item in enumerate(self.items[minIdx:maxIdx+1]):
            isSelected = (item == self.items[self.currentIdx])
            style = styleSelectTxt if isSelected else styleTxt

            padSize = 1
            trimmedName = item.name[:self.width-padSize]
            padding = ' ' * padSize
            plainText = f'{padding}{trimmedName:<{self.width}}'
            styledText = style(plainText)

            row = self.top + delta + 1  # + 1 because of title
            move = term.move(row, self.left)
            result += f'{move}{styledText}\n'
        return result

    def draw(self):
        self.clear()
        print(self.makeTitleStr())
        print(self.makeItemStrs())
        self.drawFlag = False
        return

    async def eventLoop(self):
        self.draw()
        hadFocus = False

        while True:
            focusChange = self.hasFocus() != hadFocus
            self.drawFlag = self.drawFlag or focusChange

            if self.drawFlag:
                self.draw()

            hadFocus = self.hasFocus()
            await asyncio.sleep(COROUTINE_SLEEP)
        return

    def process(self, msg):
        if not msg:
            return
        if msg == 'j':
            self.currentIdx += 1
        if msg == 'k':
            self.currentIdx -= 1

        self.currentIdx = max(min(self.currentIdx, len(self.items) - 1), 0)
        self.drawFlag = True
        return
