from dataclasses import dataclass, field
from typing import List, Dict, Callable, Tuple
import asyncio
import sys

from blessed import Terminal
import curses

from menu import Menu
from consts import term, sidebarWidth
from coordinator import Coordinator
from dataElements import Board, Card, _List


if __name__ == '__main__':
    with term.fullscreen(), term.hidden_cursor():
        coord = Coordinator(term)

        testBoards = [Board(idx, str(idx)*5, '') for idx in range(30)]
        area = (
            lambda: 0,
            lambda: term.height//2,
            lambda: 0,
            lambda: sidebarWidth,
        )
        boardMenu = Menu("Boards", *area, coord, items=testBoards)

        # TODO: Update liszt.py to use updated element types
        testLists = [_List(idx, str(idx)*3, testBoards[0])
                     for idx in range(30)]
        area = (
            lambda: (term.height//2),
            lambda: term.height - term.height//2 -  1,
            lambda: 0,
            lambda: sidebarWidth,
        )
        listMenu = Menu("Lists", *area, coord, items=testLists)

        testCards = [Card(idx, str(idx)*3, str(idx)*3)
                     for idx in range(100)]
        area = (
            lambda: 0,
            lambda: term.height - 1,
            lambda: sidebarWidth + 1,
            lambda: term.width - sidebarWidth - 1,
        )
        cardMenu = Menu("Cards", *area, coord, items=testCards)

        coord.setCurrent(boardMenu)
        coord.addKeyObjPair('B', boardMenu)
        coord.addKeyObjPair('L', listMenu)
        coord.addKeyObjPair('C', cardMenu)

        actors = [coord, boardMenu, listMenu, cardMenu]
        loop = asyncio.get_event_loop()
        for actor in actors:
            loop.create_task(actor.eventLoop())

        loop.run_forever()
