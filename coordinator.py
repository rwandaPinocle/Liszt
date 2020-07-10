import sys
import asyncio
import signal

from consts import term, EXIT, COROUTINE_SLEEP


class Coordinator:
    '''
    The Coordinator object handles keypresses and
    passes messages between actors.
    '''
    def __init__(self, term):
        self.currentObj = None
        self.keyObjMap = {}
        signal.signal(signal.SIGWINCH, self.onResize)

    def setCurrent(self, current):
        self.currentObj = current

    def addKeyObjPair(self, key, obj):
        self.keyObjMap[key] = obj

    def handleKey(self, key=None):
        with term.cbreak():
            key = term.inkey()
        if key == 'q':
            return EXIT
        self.currentObj = self.keyObjMap.get(key, self.currentObj)
        self.currentObj.process(key)

    def onResize(self, *args):
        for key, obj in self.keyObjMap.items():
            obj.draw()
        return

    async def eventLoop(self):
        while True:
            result = self.handleKey()
            if result == EXIT:
                sys.exit()
            await asyncio.sleep(COROUTINE_SLEEP)
