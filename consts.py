from blessed import Terminal

EXIT = 'exit'
NO_EXIT = 'no_exit'

COROUTINE_SLEEP = 0.01

term = Terminal()

styleFBg = term.on_blue
styleUfBg = term.on_black
styleTxt = term.white
styleFTitle = term.underline_black_on_blue
styleUfTitle = term.underline_blue_on_black
styleSelectTxt = term.black_on_green
