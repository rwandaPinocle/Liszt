import json
import re
import sqlite3
import os
import time
# TODO: Add support for letter hash ids

S_QUOTE = "'"
D_QUOTE = '"'


def encodeForDB(content):
    content = content.replace('\t', ' '*4)
    content = content.replace('\n', '<|NEWLINE|>')
    content = content.replace(S_QUOTE, S_QUOTE*2)
    return content


def decodeFromDB(content):
    content = content.replace('<|NEWLINE|>', '\n')
    content = content.replace(S_QUOTE*2, S_QUOTE)
    return content


class Database:
    def __init__(self, filename='data.db'):
        self.filename = filename
        if not os.path.exists(filename):
            self.db = sqlite3.connect(self.filename)
            self.initializeDb()
        else:
            self.db = sqlite3.connect(self.filename)

        self.boardIdx = 0

        self.actions = {
            'where': self.where,
            'goto': self.goto,

            'add-card': self.addCard,
            'add-list': self.addList,
            'add-board': self.addBoard,
            'add-button': self.addButton,

            'set-card-content': self.setCardContent,
            'get-card-content': self.getCardContent,

            'set-due-date': self.setDueDate,
            'get-due-date': self.getDueDate,
            'set-due-in': self.setDueIn,
            'move-due-cards': self.moveDueCards,

            'show-cards': self.showCards,
            'show-lists': self.showLists,
            'show-boards': self.showBoards,
            'show-buttons': self.showButtons,

            'get-button': self.getButton,

            'rename-button': self.renameButton,
            'rename-board': self.renameBoard,
            'rename-list': self.renameList,
            'rename-card': self.renameCard,

            'move-card': self.moveCard,
            'move-list': self.moveList,

            'shift-card': self.shiftCard,
            'shift-list': self.shiftList,
            'shift-board': self.shiftBoard,

            'delete-card': self.delCard,
            'delete-list': self.delList,
            'delete-board': self.delBoard,
            'delete-button': self.delButton,
        }
        return

    def close(self):
        self.db.close()

    def initializeDb(self):
        print('initializing db')
        sqlLines = [
            'CREATE TABLE boards (title text, idx integer)',
            'CREATE TABLE lists (title text, idx integer, board integer)',
            '''CREATE TABLE cards
                (title text,
                 idx integer,
                 dueDate integer,
                 list integer,
                 content text)''',
            'CREATE TABLE buttons (name text, command text, idx integer)',
            "INSERT INTO boards VALUES ('Personal', 0)",
            """INSERT INTO buttons VALUES
                ('Delete card', 'delete-card $CARD', 0)""",
            "INSERT INTO lists VALUES ('To do', 0, 1)",
            "INSERT INTO lists VALUES ('Doing', 1, 1)",
            "INSERT INTO lists VALUES ('Done', 2, 1)",
        ]
        for sql in sqlLines:
            self.db.execute(sql)

        self.db.commit()
        return

    def runCommand(self, cmd):
        '''
        Executes a command on the datatree
        '''
        items = self.actions.items()
        op = next(func for verb, func in items if cmd.startswith(verb))

        # Run command
        result = op(cmd)
        self.db.commit()
        return result

    def where(self, command):
        '''
        where
        '''
        sql = 'SELECT title FROM boards ORDER BY idx ASC'
        result = list(self.db.execute(sql))
        boardName = result[self.boardIdx][0]
        return boardName

    def goto(self, command):
        '''
        goto 123
        goto "board name"
        '''
        argPat = r'goto (?P<boardStr>".+"|\d+)'
        match = re.match(argPat, command)
        boardId = self.getBoardId(match.group('boardStr'))
        sql = f'''
            SELECT idx, title FROM boards WHERE ROWID = {boardId}
        '''
        idx, title = self.db.execute(sql).fetchone()
        self.boardIdx = idx
        return f'Current board: {title}'

    def getAllBoardIds(self):
        sql = 'SELECT ROWID FROM boards'
        boardIds = [i[0] for i in self.db.execute(sql)]
        return boardIds 

    def getAllListIds(self):
        sql = 'SELECT ROWID FROM lists'
        listIds = [i[0] for i in self.db.execute(sql)]
        return listIds 

    def cullOrphans(self):
        boardIds = self.getAllBoardIds()
        boardIdStr = ','.join(str(bid) for bid in boardIds)
        boardIdStr = f'({boardIdStr})'
        sql = f'''
            DELETE FROM lists
            WHERE board NOT IN {boardIdStr}
        '''
        self.db.execute(sql)

        listIds = self.getAllListIds()
        listIdStr = ','.join(str(bid) for bid in listIds)
        listIdStr = f'({listIdStr})'
        sql = f'''
            DELETE FROM cards
            WHERE list NOT IN {listIdStr}
        '''
        self.db.execute(sql)
        return

    def getCurrentBoardId(self):
        '''
        current-board-id
        '''
        sql = 'SELECT ROWID FROM boards ORDER BY idx ASC'
        boards = list(self.db.execute(sql))
        boardName = boards[self.boardIdx][0]
        return boardName

    def getListId(self, listStr, boardId=-1):
        if boardId == -1:
            boardId = self.getCurrentBoardId()

        if D_QUOTE in listStr:
            listTitle = encodeForDB(listStr.strip(D_QUOTE))
            sql = f'''
                SELECT ROWID
                FROM lists
                WHERE title='{listTitle}'
                AND board={boardId}
            '''
            listId = self.db.execute(sql).fetchone()[0]
        elif listStr.isdigit():
            sql = f'''
                SELECT ROWID
                FROM lists
                WHERE ROWID={listStr}'''
            listId = self.db.execute(sql).fetchone()[0]
        else:
            raise NotImplementedError('Alphabetical ids not supported yet')
        return listId

    def getBoardId(self, boardStr):
        if D_QUOTE in boardStr:
            boardTitle = boardStr.strip(D_QUOTE)
            sql = f'''
                SELECT ROWID
                FROM boards
                WHERE title='{boardTitle}'
            '''
            boardId = self.db.execute(sql).fetchone()[0]
        elif boardStr.isdigit():
            sql = f'''
                SELECT ROWID
                FROM boards
                WHERE ROWID={boardStr}'''
            boardId = self.db.execute(sql).fetchone()[0]
        else:
            raise NotImplementedError('Alphabetical ids not supported yet')
        return boardId

    def getMaxIdx(self, table, field='', fieldVal=''):
        if field and fieldVal:
            sql = f'''
                SELECT MAX(idx)
                FROM {table}
                WHERE {field}={fieldVal}
                '''
        else:
            sql = f'SELECT MAX(idx) FROM {table}'
        maxIdx = self.db.execute(sql).fetchone()[0]

        if maxIdx is None:
            maxIdx = -1
        newIdx = maxIdx + 1
        return newIdx

    def reindex(self, table, field='', fieldVal=''):
        if field and fieldVal:
            sql = f'''
                SELECT ROWID
                FROM {table}
                WHERE {field}={fieldVal}
                ORDER BY idx ASC
            '''
        else:
            sql = f'''
                SELECT ROWID
                FROM {table}
                ORDER BY idx ASC
            '''

        rows = self.db.execute(sql)
        for idx, row in enumerate(rows):
            rowId = row[0]
            sql = f'''
                UPDATE {table}
                SET idx = {idx}
                WHERE ROWID = {rowId}
            '''
            self.db.execute(sql)
        return

    def addCard(self, command):
        '''
        add-card "card title":"description":123 to 123
        add-card "card title":"description":123 to "list title"
        '''
        # Get card title and list title
        pat = r'add-card "(.*)":"(.*)":([\d-]*) to (".*"|.*)'
        match = re.match(pat, command)
        cardTitle = match.group(1)
        descStr = match.group(2)
        dueDate = match.group(3)
        listStr = match.group(4)

        # Get new index
        listId = self.getListId(listStr)
        newIdx = self.getMaxIdx('cards', 'list', listId)

        # Insert list into table
        values = (cardTitle, newIdx, dueDate, listId, descStr)
        sql = '''
            INSERT INTO cards(title, idx, dueDate, list, content)
            VALUES (?, ?, ?, ?, ?)
        '''
        self.db.execute(sql, values)
        return

    def addList(self, command):
        '''
        add-list "List title" to 123
        '''
        # Parse command string
        pat = r'add-list "(.*)" to (\d*)'
        match = re.match(pat, command)
        newListTitle = match.group(1)
        boardId = match.group(2)

        # Get new index
        newIdx = self.getMaxIdx('lists', 'board', boardId)

        # Insert list into table
        values = (newListTitle, newIdx, boardId)
        sql = f'INSERT INTO lists(title, idx, board) VALUES {values}'
        self.db.execute(sql)
        return

    def addBoard(self, command):
        '''
        add-board "Board title"
        '''
        # Parse command string
        pat = r'add-board "(.*)"'
        match = re.match(pat, command)
        newBoardTitle = match.group(1).strip('"')

        # Get new index
        newIdx = self.getMaxIdx('boards')

        # Insert board into table
        values = (newBoardTitle, newIdx)
        sql = f'INSERT INTO boards(title, idx) VALUES {values}'
        self.db.execute(sql)
        return

    def addButton(self, command):
        '''
        add-button "Button title" "command"
        '''
        # Parse command string
        pat = r'add-button "(.*)" "(.*)"'
        match = re.match(pat, command)
        newButtonName = match.group(1).strip('"')
        newButtonCommand = match.group(2).strip('"')

        # Get new index
        newIdx = self.getMaxIdx('buttons')

        # Insert button into table
        values = (newButtonName, newButtonCommand, newIdx)
        sql = f'INSERT INTO buttons(name, command, idx) VALUES {values}'
        self.db.execute(sql)
        return

    def setCardContent(self, command):
        '''
        set-card-content 123 to "content"
        '''
        pat = r'set-card-content (\d*) "(.*)"'
        match = re.match(pat, command)
        cardId = match.group(1)
        content = match.group(2).strip('"')
        content = content.replace('\t', ' '*4)
        content = content.replace('\n', '<|NEWLINE|>')

        sql = f'''
            UPDATE cards
            SET content = '{content}'
            WHERE ROWID = {cardId}
        '''
        self.db.execute(sql)
        return

    def getCardContent(self, command):
        '''
        get-card-content 123
        '''
        pat = r'get-card-content (\d*)'
        match = re.match(pat, command)
        cardId = match.group(1)

        sql = f'''
            SELECT content
            FROM cards
            WHERE ROWID = {cardId}
        '''
        self.db.execute(sql)
        return

    def setDueIn(self, command):
        '''
        set-due-in 123 12d/w/m/y
        '''
        pat = r'set-due-in (\d+) (\d+d|\d+w|\d+m|\d+y)'
        match = re.match(pat, command)
        cardId = match.group(1)
        interval = match.group(2)

        num = int(interval[:-1])
        unit = interval[-1]

        coefMap = {
            'd': 24*60*60,
            'w': 24*60*60*7,
            'm': 24*60*60*30,
            'y': 24*60*60*365,
        }
        coef = coefMap[unit]
        dueDate = (num*coef) + int(time.time())

        sql = f'''
            UPDATE cards
            SET dueDate = {dueDate}
            WHERE ROWID = {cardId}
        '''
        self.db.execute(sql)
        return

    def setDueDate(self, command):
        '''
        set-due-date 123 1234561234
        '''
        pat = r'set-due-date (\d+) (\d+|-1)'
        match = re.match(pat, command)
        cardId = match.group(1)
        dueDate = match.group(2)

        sql = f'''
            UPDATE cards
            SET dueDate = {dueDate}
            WHERE ROWID = {cardId}
        '''
        self.db.execute(sql)
        return

    def getDueDate(self, command):
        '''
        get-due-date 123
        '''
        pat = r'get-due-date (\d*)'
        match = re.match(pat, command)
        cardId = match.group(1)

        sql = f'''
            SELECT dueDate
            FROM cards
            WHERE ROWID = {cardId}
        '''
        self.db.execute(sql)
        return

    def moveDueCards(self, command):
        '''
        move-due-cards 123,123,123 to 123
        '''
        pat = r'move-due-cards ([\d,]+) to (\d+)'
        match = re.match(pat, command)
        sourceListIds = match.group(1)
        destListId = match.group(2)
        today = int(time.time())

        sql = f'''
            UPDATE cards
            SET list = {destListId}
            WHERE list IN ({sourceListIds})
            AND dueDate < {today}
            AND dueDate > 0
        '''
        self.db.execute(sql)
        self.reindex('cards', 'list', destListId)
        return 

    def renameButton(self, command):
        '''
        rename-button 123 "Button title" "command"
        '''
        # Parse command string
        pat = r'rename-button (\d*) "(.*)" "(.*)"'
        match = re.match(pat, command)

        buttonId = match.group(1)
        buttonTitle = match.group(2)
        buttonCommand = match.group(3)

        sql = f'''
            UPDATE buttons
            SET name = '{buttonTitle}',
                command = '{buttonCommand}'
            WHERE ROWID = {buttonId}
            '''
        self.db.execute(sql)

    def renameBoard(self, command):
        '''
        rename-board 123 "board title"
        '''
        # Parse command string
        pat = r'rename-board (\d*) "(.*)"'
        match = re.match(pat, command)

        boardId = match.group(1)
        boardTitle = match.group(2)

        sql = f'''
            UPDATE boards
            SET title = '{boardTitle}'
            WHERE ROWID = {boardId}
            '''
        self.db.execute(sql)

    def renameList(self, command):
        '''
        rename-list 123 "list title"
        '''
        # Parse command string
        pat = r'rename-list (\d*) "(.*)"'
        match = re.match(pat, command)

        listId = match.group(1)
        listTitle = match.group(2)

        sql = f'''
            UPDATE lists
            SET title = '{listTitle}'
            WHERE ROWID = {listId}
            '''
        self.db.execute(sql)

    def renameCard(self, command):
        '''
        rename-card 123 "Card title"
        '''
        # Parse command string
        pat = r'rename-card (\d*) "(.*)"'
        match = re.match(pat, command)

        cardId = match.group(1)
        cardTitle = match.group(2)

        sql = f'''
            UPDATE cards
            SET title = '{cardTitle}'
            WHERE ROWID = {cardId}
            '''
        self.db.execute(sql)

    def showCards(self, command):
        '''
        show-cards "List title"
        show-cards 123
        '''
        pat = r'show-cards (".*"|\d*)'
        match = re.match(pat, command)

        # Get list id
        listStr = match.group(1)
        listId = self.getListId(listStr)

        # Get cards in the list
        sql = f'''
            SELECT ROWID, title, dueDate, content
            FROM cards
            WHERE list={listId}
            ORDER BY idx ASC'''
        cards = self.db.execute(sql)

        # Show results
        result = 'id\tdue\ttitle\tcontent\n'
        for card in cards:
            result += f'{card[0]}\t{card[2]}\t{card[1]}\t{card[3] or ""}\n'
        return result

    def showLists(self, command):
        '''
        show-lists
        show-lists "board name"
        show-lists 123
        '''
        pat = r'show-lists (".*"|\d*)'
        match = re.match(pat, command)

        # Get the board id
        if match is None:
            sql = 'SELECT ROWID FROM boards ORDER BY idx ASC'
            boardId = list(self.db.execute(sql))[self.boardIdx][0]
        else:
            boardStr = match.group(1)
            boardId = self.getBoardId(boardStr)

        # Get the lists in that board
        sql = f'''
            SELECT ROWID, title, idx
            FROM lists
            WHERE board={boardId}
            ORDER BY idx ASC
            '''
        lists = self.db.execute(sql)

        # Show the results
        result = 'id\ttitle\tcards\n'
        for _list in lists:
            sql = f"SELECT ROWID FROM cards WHERE list='{_list[0]}'"
            cardCount = len(list(self.db.execute(sql)))
            result += f'{_list[0]}\t{_list[1]}\t{cardCount}\n'
        return result

    def showBoards(self, command):
        '''
        show-boards
        '''
        sql = '''
            SELECT ROWID, title
            FROM boards
            ORDER BY idx ASC
        '''
        boards = list(self.db.execute(sql))

        result = 'id\ttitle\n'
        for board in boards:
            result += f'{board[0]}\t{board[1]}\n'
        return result

    def showButtons(self, command):
        '''
        show-buttons
        '''
        sql = '''
            SELECT ROWID, name, command
            FROM buttons
            ORDER BY idx ASC
        '''
        buttons = list(self.db.execute(sql))

        result = 'id\tname\tcommand\n'
        for button in buttons:
            result += f'{button[0]}\t{button[1]}\t{button[2]}\n'
        return result

    def getButton(self, command):
        '''
        get-button
        '''
        argPat = r'get-button (\d*)'
        match = re.match(argPat, command)

        buttonId = match.group(1)
        sql = f'''
            SELECT command
            FROM buttons
            WHERE ROWID = {buttonId}
        '''
        command = self.db.execute(sql).fetchone()[0]
        return command

    def listsInBoard(self, boardId):
        sql = f'''SELECT ROWID FROM lists
                WHERE board = {boardId} ORDER BY idx ASC'''
        listsInBoard = [r[0] for r in self.db.execute(sql)]
        return listsInBoard

    def moveCard(self, command):
        '''
        move-card 123 to "list title"
        move-card 123 to "list title" in "board title"
        move-card 123 to 132
        move-card 123 to next
        move-card 123 to prev
        '''
        argPat = r'move-card (?P<cardStr>".+"|\d+)'
        argPat += r' to (?P<listDstStr>".+"|\d+|next|prev)'
        argPat += r'(?: in (?P<boardStr>".+"|\d+))?'
        match = re.match(argPat, command)

        cardId = match.group('cardStr')

        if match.group('boardStr'):
            boardId = self.getBoardId(match.group('boardStr'))
        else:
            boardId = self.getCurrentBoardId()

        if 'next' in match.group('listDstStr'):
            sql = f'SELECT list FROM cards WHERE ROWID = {cardId}'
            currentListId = self.db.execute(sql).fetchone()[0]
            listsInBoard = self.listsInBoard(boardId)

            listIdx = listsInBoard.index(currentListId)
            nextListIdx = min(listIdx + 1, len(listsInBoard) - 1)
            listDstId = listsInBoard[nextListIdx]

        elif 'prev' in match.group('listDstStr'):
            sql = f'SELECT list FROM cards WHERE ROWID = {cardId}'
            currentListId = self.db.execute(sql).fetchone()[0]
            listsInBoard = self.listsInBoard(boardId)

            listIdx = listsInBoard.index(currentListId)
            prevListIdx = max(listIdx - 1, 0)
            listDstId = listsInBoard[prevListIdx]

        else:
            listDstId = self.getListId(match.group('listDstStr'), boardId)

        self.reindex('cards', 'list', listDstId)
        newIdx = self.getMaxIdx('cards', 'list', listDstId)
        sql = f'''
            UPDATE cards
            SET list = {listDstId},
                idx = {newIdx}
            WHERE ROWID = {cardId}
        '''
        self.db.execute(sql)
        return

    def moveList(self, command):
        '''
        move-list "list title" to "board title"
        move-list 123 to 123
        '''
        argPat = r'move-list (?P<listStr>".+"|\d+) to (?P<boardStr>".+"|\d+)'
        match = re.match(argPat, command)

        listId = self.getListId(match.group('listStr'))
        boardId = self.getBoardId(match.group('boardStr'))
        sql = f'''
            UPDATE lists
            SET board = {boardId}
            WHERE ROWID = {listId}
        '''
        self.db.execute(sql)
        return

    def shiftCard(self, command):
        '''
        shift-card <cardid> to <index>
        shift-card 123 to 0
        '''
        argPat = r'shift-card (\d+) to (\d+|-\d+)'
        match = re.match(argPat, command)
        cardId = match.group(1)
        newIndex = int(match.group(2))

        sql = f'SELECT list FROM cards WHERE ROWID = {cardId}'
        listId = self.db.execute(sql).fetchone()[0]

        # Reindex card in case of corrupted indexes
        self.reindex('cards', 'list', listId)

        sql = f'SELECT idx FROM cards WHERE ROWID = {cardId}'
        result = self.db.execute(sql).fetchone()
        oldIndex = int(result[0])

        sign = '-' if newIndex > oldIndex else '+'
        sql = f'''
            UPDATE cards SET idx = idx {sign} 1
            WHERE {min(oldIndex, newIndex)} <= idx
            AND idx <= {max(oldIndex, newIndex)}
            AND list = {listId}
        '''
        self.db.execute(sql)

        sql = f'''
            UPDATE cards
            SET idx = {newIndex}
            WHERE ROWID = {cardId}
        '''
        self.db.execute(sql)
        return

    def shiftList(self, command):
        '''
        shift-list <listid> to <index>
        shift-list 123 to 0
        '''
        argPat = r'shift-list (\d+) to (\d+|-\d+)'
        match = re.match(argPat, command)
        listId = match.group(1)
        newIndex = int(match.group(2))

        sql = f'SELECT board FROM lists WHERE ROWID = {listId}'
        boardId = self.db.execute(sql).fetchone()[0]

        # Reindex lists in case of corrupted indexes
        self.reindex('lists', 'board', boardId)

        sql = f'''
            SELECT idx FROM lists WHERE ROWID = {listId}
        '''
        result = self.db.execute(sql).fetchone()
        oldIndex = int(result[0])

        sign = '-' if newIndex > oldIndex else '+'
        sql = f'''
            UPDATE lists SET idx = idx {sign} 1
            WHERE {min(oldIndex, newIndex)} <= idx
            AND idx <= {max(oldIndex, newIndex)}
            AND board = {boardId}
        '''
        self.db.execute(sql)

        sql = f'''
            UPDATE lists
            SET idx = {newIndex}
            WHERE ROWID = {listId}
        '''
        self.db.execute(sql)
        return

    def shiftBoard(self, command):
        '''
        shift-board <boardid> to <index>
        shift-board 123 to 0
        '''
        argPat = r'shift-board (\d+) to (\d+|-\d+)'
        match = re.match(argPat, command)
        boardId = match.group(1)
        newIndex = int(match.group(2))

        # Reindex lists in case of corrupted indexes
        self.reindex('boards')

        sql = f'''
            SELECT idx FROM boards WHERE ROWID = {boardId}
        '''
        result = self.db.execute(sql).fetchone()
        oldIndex = int(result[0])

        sign = '-' if newIndex > oldIndex else '+'
        sql = f'''
            UPDATE boards SET idx = idx {sign} 1
            WHERE {min(oldIndex, newIndex)} <= idx
            AND idx <= {max(oldIndex, newIndex)}
        '''
        self.db.execute(sql)

        sql = f'''
            UPDATE boards
            SET idx = {newIndex}
            WHERE ROWID = {boardId}
        '''
        self.db.execute(sql)
        return

    def delCard(self, command):
        '''
        delete-card 123
        '''
        argPat = r'delete-card (?P<cardId>\d+)'
        match = re.match(argPat, command)
        cardId = match.group('cardId')
        sql = f'''
            DELETE FROM cards
            WHERE ROWID = {cardId}
        '''
        self.db.execute(sql)
        return

    def delList(self, command):
        '''
        delete-list 123
        '''
        argPat = r'delete-list (?P<listId>\d+)'
        match = re.match(argPat, command)
        listId = match.group('listId')
        sql = f'''
            DELETE FROM lists
            WHERE ROWID = {listId}
        '''
        self.db.execute(sql)
        self.cullOrphans()
        return

    def delBoard(self, command):
        '''
        delete-board 123
        '''
        argPat = r'delete-board (?P<boardId>\d+)'
        match = re.match(argPat, command)
        boardId = match.group('boardId')
        sql = f'''
            DELETE FROM boards
            WHERE ROWID = {boardId}
        '''
        self.db.execute(sql)
        self.cullOrphans()
        return

    def delButton(self, command):
        '''
        delete-button 123
        '''
        pat = r'delete-button (\d*)'
        match = re.match(pat, command)
        boardId = match.group(1)
        sql = f'''
            DELETE FROM buttons
            WHERE ROWID = {boardId}
        '''
        self.db.execute(sql)
        return
