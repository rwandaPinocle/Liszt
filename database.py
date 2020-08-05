import json
import re
import sqlite3
import os
# TODO: Add support for letter hash ids

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
            'current-board': self.currentBoard,
            'add-card': self.addCard,
            'add-list': self.addList,
            'add-board': self.addBoard,

            'show-list': self.showList,
            'show-board': self.showBoard,

            'move-card': '',
            'move-list': '',
            'move-board': '',

            'del-card': '',
            'del-list': '',
            'del-board': '',
        }
        return

    def close(self):
        self.db.close()

    def initializeDb(self):
        print('initializing db')
        sql = 'CREATE TABLE boards (title text, idx integer)'
        self.db.execute(sql)

        sql = 'CREATE TABLE lists (title text, idx integer, board integer)'
        self.db.execute(sql)

        sql = '''CREATE TABLE cards
            (title text, idx integer, dueDate integer, list integer)'''
        self.db.execute(sql)

        sql = "INSERT INTO boards VALUES ('Personal', 0)"
        self.db.execute(sql)

        sql = 'SELECT ROWID FROM boards WHERE title="Personal"'
        bId = self.db.execute(sql).fetchone()[0]

        sql = 'INSERT INTO lists VALUES (?, ?, ?)'
        values = [('To do', 0, bId), ('Doing', 1, bId), ('Done', 2, bId)]
        self.db.executemany(sql, values)
        self.db.commit()
        return

    def runCommand(self, command):
        '''
        Executes a command on the datatree
        Commands are split into a context string and an action
        Supported:
            current-board
            add-card "Card Title" to board
            add-list "List Title"
            add-board "Board Title"
            show-list "List title"
            show-board
            show-boards
        '''
        action = command.split()[0]

        # Get correct action
        action.strip()
        op = self.actions[action.split()[0]]

        # Run command
        result = op(command)
        self.db.commit()
        return result

    def currentBoard(self, command):
        '''
        current-board
        '''
        sql = '''
            SELECT title
            FROM boards
            ORDER BY idx ASC
            '''
        result = list(self.db.execute(sql))
        boardName = result[self.boardIdx][0]
        return boardName

    def currentBoardId(self, command):
        '''
        current-board-id
        '''
        sql = '''
            SELECT ROWID
            FROM boards
            ORDER BY idx ASC
            '''
        result = list(self.db.execute(sql))
        boardName = result[self.boardIdx][0]
        return boardName

    def addCard(self, command):
        '''
        add-card "card title" to "list title"
        add-card 111 to 142
        add-card afs to sfj
        '''
        pat = r'add-card (".*"|.*) to (".*"|.*)'
        match = re.match(pat, command)
        cardTitle = match.group(1)
        listStr = match.group(2)

        if '"' in listStr:
            print(1)
            listTitle = listStr.strip('"')
            print('cardTitle', cardTitle)
            print('listTitle', listTitle)
            sql = f'''
                SELECT ROWID
                FROM lists
                WHERE title='{listTitle}'
                AND board={self.currentBoardId('')}
            '''
            print(sql)
            listId = self.db.execute(sql).fetchone()[0]
        elif listStr.isdigit():
            print(2)
            sql = f'''
                SELECT ROWID
                FROM lists
                WHERE ROWID={listStr}'''
            listId = self.db.execute(sql).fetchone()[0]
        else:
            raise NotImplementedError('Alphabetical ids not supported yet')

        print(3)
        sql = f'''
            SELECT MAX(idx)
            FROM cards
            WHERE list='{listId}'
            '''
        maxIdx = self.db.execute(sql).fetchone()[0]
        if maxIdx is None:
            maxIdx = -1
        newIdx = maxIdx + 1

        print(4)
        values = (cardTitle, newIdx, -1, listId)
        sql = f'INSERT INTO cards VALUES {values}'
        self.db.execute(sql)
        self.db.commit()
        return

    def addList(self, command):
        '''
        add-list "List title"
        '''
        pat = r'add-list (".*")'
        match = re.match(pat, command)
        newListTitle = match.group(1).strip('"')

        sql = "SELECT ROWID FROM boards"
        boardId = list(self.db.execute(sql))[self.boardIdx][0]

        sql = f"SELECT MAX(idx) FROM lists WHERE name='{boardId}'"
        maxIdx = self.db.execute(sql).fetchone()[0]
        if maxIdx is None:
            maxIdx = -1
        newIdx = maxIdx + 1

        values = (newListTitle, newIdx, boardId)
        sql = f'INSERT INTO lists(title, idx, board) VALUES {values}'
        self.db.execute(sql)
        self.commit()
        return

    def addBoard(self, command):
        '''
        add-board "Board title"
        '''
        pat = r'add-board (".*")'
        match = re.match(pat, command)
        newBoardTitle = match.group(1).strip('"')

        sql = 'SELECT MAX(index) FROM boards'
        maxIdx = self.db.execute(sql).fetchone()[0]
        if maxIdx is None:
            maxIdx = -1
        newIdx = maxIdx + 1

        values = (newBoardTitle, newIdx)
        sql = f'INSERT INTO boards(title, idx) VALUES {values}'
        self.db.execute(sql)
        self.commit()
        return

    def showList(self, command):
        '''
        show-list "List title"
        show-list 123
        '''
        pat = r'show-list ("?.*"?)'
        match = re.match(pat, command)
        listStr = match.group(1)

        if '"' in listStr:
            listTitle = listStr.strip('"')
            sql = f"SELECT ROWID FROM lists WHERE title='{listTitle}'"
        elif listStr.isdigit():
            sql = f"SELECT ROWID FROM lists WHERE ROWID={listStr}"
        else:
            raise NotImplementedError('Alphabetical ids not supported yet')

        listId = self.db.execute(sql).fetchone()[0]

        sql = f'''
            SELECT ROWID, title, dueDate
            FROM cards
            WHERE list={listId}
            ORDER BY idx ASC'''
        cards = self.db.execute(sql)
        result = 'Id\tDue\tTitle\n'
        for card in cards:
            result += f'{card[0]}\t{card[2]}\t{card[1]}\n'
        return result

    def showBoard(self, command):
        '''
        show-board
        '''
        pat = r'show-board ("?.*"?)'
        match = re.match(pat, command)

        if match is None:
            sql = '''
                SELECT ROWID
                FROM boards
                ORDER BY idx ASC'''
            boardId = list(self.db.execute(sql))[self.boardIdx][0]

        elif '"' in match.group(1):
            boardStr = match.group(1)
            boardTitle = boardStr.strip('"')
            sql = f"SELECT ROWID FROM boards WHERE title='{boardTitle}'"

        elif match.group(1).isdigit():
            boardStr = match.group(1)
            boardTitle = boardStr.strip('"')
            sql = f"SELECT ROWID FROM boards WHERE ROWID='{boardTitle}'"

        else:
            raise NotImplementedError('Alphabetical ids not supported yet')

        boardId = self.db.execute(sql).fetchone()[0]

        sql = f'''
            SELECT ROWID, title, idx
            FROM lists
            WHERE board={boardId}
            ORDER BY idx ASC
            '''
        lists = self.db.execute(sql)
        result = 'Id\tTitle\tCards\n'
        for _list in lists:
            sql = f"SELECT ROWID FROM cards WHERE list='{_list[0]}'"
            cardCount = len(list(self.db.execute(sql)))
            result += f'{_list[0]}\t{_list[1]}\t{cardCount}\n'
        return result
