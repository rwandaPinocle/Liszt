from dataclasses import dataclass, field
from typing import List, Dict, Callable, Tuple
import asyncio
import sys

from blessed import Terminal
import curses

from menu import Menu
from consts import term
from focus import Focus
from dataElements import Board, Card, CardList


if __name__ == '__main__':
    with term.fullscreen(), term.hidden_cursor():
        focus = Focus(term)

        testBoards = [Board(idx, str(idx)*5) for idx in range(30)]
        area = (0, 20, 0, 20)
        boardMenu = Menu("Boards", *area, focus, items=testBoards)

        testLists = [CardList(idx, str(idx)*3, testBoards[0])
                     for idx in range(30)]
        area = (21, 20, 0, 20)
        listMenu = Menu("Lists", *area, focus, items=testLists)

        focus.setCurrent(boardMenu)
        focus.addKeyObjPair('B', boardMenu)
        focus.addKeyObjPair('L', listMenu)

        actors = [focus, boardMenu, listMenu]
        loop = asyncio.get_event_loop()
        for actor in actors:
            loop.create_task(actor.eventLoop())

        loop.run_forever()
