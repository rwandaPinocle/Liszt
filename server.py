import json
import date
import re
import sqlite3
import os

# TODO: Add support for letter hash ids

class Database:
    def __init__(self, filename='data.db'):
        self.filename = filename
        self.db = sqlite3.connect(self.filename)
        if not os.path.exists():
            self.initializeDb()

        self.boardIdx = 0

        self.actions = {
            'current-board': self.currentBoard,
            'add-card': self.addCard,
            'add-list': self.addList,
            'add-board': self.addBoard,

            'move-card': '',
            'move-list': '',
            'move-board': '',

            'del-card': '',
            'del-list': '',
            'del-board': '',
        }
        return

    def initializeDb(self):
        sql = 'CREATE TABLE boards (title text, idx integer)'
        self.db.execute(sql)

        sql = 'CREATE TABLE lists (title text, idx integer, board integer)'
        self.db.execute(sql)

        sql = '''CREATE TABLE cards
            (title text, idx integer, dueDate integer, list integer)'''
        self.db.execute(sql)

        sql = "INSERT INTO boards VALUES ('Personal', 0)"
        self.db.execute(sql)

        sql = 'INSERT INTO lists VALUES (?, ?)'
        values = [('To do', 0), ('Doing', 1), ('Done', 2)]
        self.db.executemany(sql, values)
        self.db.commit()
        return

    def execute(self, command):
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
        result = op(command.split())
        return result

    def parse(self, command):
        return

    def addCard(self, command):
        '''
        add-card "card title" to "list title"
        add-card 111 to 142
        add-card afs to sfj
        '''
        pat = r'add-card ("?.*"?) to ("?.*"+)'
        match = re.match(pat, command)
        cardTitle = match.group(1)
        listStr = match.group(2)

        if '"' in listStr:
            listTitle = listStr.strip('"')
            sql = f"SELECT ROWID FROM lists WHERE title={listTitle}"
            listId = self.db.execute(sql).fetchone()[0]
        elif listStr.isDigit():
            sql = f"SELECT ROWID FROM lists WHERE ROWID={listStr}"
            listId = self.db.execute(sql).fetchone()[0]
        else:
            raise NotImplementedError('Alphabetical ids not supported yet')

        sql = f'SELECT MAX(index) FROM cards WHERE name={listId}'
        newIdx = self.db.execute(sql).fetchone()[0] + 1

        values = (cardTitle, newIdx, -1, listId)
        sql = f'INSERT INTO cards VALUES {values}'
        self.db.execute(sql)
        self.commit()
        return

    def addList(self, command):
        '''
        add-list "List title"
        '''
        pat = r'add-list (".*")'
        match = regex.match(pat, command)
        newListTitle = match.group(1).strip('"')

        sql = f"SELECT ROWID FROM boards WHERE title={contextData['board']}"
        boardId = self.db.execute(sql).fetchone()[0]

        sql = f'SELECT MAX(index) FROM lists WHERE name={boardId}'
        newIdx = self.db.execute(sql).fetchone()[0] + 1

        values = (newListTitle, newIdx, -1, boardId)
        sql = f'INSERT INTO lists VALUES {values}'
        self.db.execute(sql)
        self.commit()
        return

    def addBoard(self, contextData, argStr, tree):
        argStr.strip()
        newBoardTitle = argStr.strip('"')

        sql = 'SELECT MAX(index) FROM boards'
        newIdx = self.db.execute(sql).fetchone()[0] + 1

        values = (newBoardTitle, newIdx)
        sql = f'INSERT INTO boards VALUES {values}'
        self.db.execute(sql)
        self.commit()
        return


