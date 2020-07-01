from dataclasses import dataclass
from blessings import Terminal
import curses

class Focus:
    pass

class BoardMenu:
    pass

class ListMenu:
    pass

class CardMenu:
    pass

class CardView:
    pass


def main(win):
    term = Terminal()
    win.nodelay(True)
    win.clear()
    text = ''
    row = 0
    print('')
    while True:
        try:
            key = win.getkey()
        except:
            continue
        if key == 'q':
            break
        if key == '\n':
            text = ''
            row += 1
        text += key
        print(term.move(row, 0))
        print(text, end=' ')
            
curses.wrapper(main)
