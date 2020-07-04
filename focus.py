import sys
import asyncio

from consts import term, EXIT, COROUTINE_SLEEP


class Focus:
    '''
    The Focus object tracks when screen object has the focus.
    It captures keypresses and forwards them to the currently focused object.
    '''
    def __init__(self, term):
        self.currentObj = None
        self.keyObjMap = {}

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

    async def eventLoop(self):
        while True:
            result = self.handleKey()
            if result == EXIT:
                sys.exit()
            await asyncio.sleep(COROUTINE_SLEEP)
