import json
import date
import re
import sqlite3
import os


def parseContext(context):
    pattern = r'with \(([A-Za-z0-9]*)/([A-Za-z0-9]*)/([A-Za-z0-9]*)\)'
    match = re.match(pattern, context)
    contextData = {
        'board': match.group(1),
        'list': match.group(2),
        'card': match.group(3),
    }
    return contextData


class Database:
    def __init__(self, filename='data.db'):
        self.filename = filename
        self.db = sqlite3.connect(self.filename)
        if not os.path.exists():
            self.initializeDb()
            
        self.actions = {
            'new-card': self.newCard,
            'new-list': self.newList,
            'new-board': self.newBoard,

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
            with (board title/list title/card title): new-card (Card Title)
            with (board title/list title/card title): new-list (List Title)
            with (board title/list title/card title): new-board (Board Title)
            with (board title/list title/card title): show-card
            with (board title/list title/card title): show-list
            with (board title/list title/card title): show-board
            with (board title/list title/card title): show-boards
            
            # with (board title/list title/card title): move-card (List Title)
            # with (personal/to do/-): new-list "Ignore"
        '''
        context, action = command.split(':')
        contextData = parseContext(context)       

        # Get correct action
        action.strip()
        op = self.actions[action.split()[0]]
        op(contextData, action)
        return

    def parse(self, command):
        return

    def newCard(self, contextData, argStr):
        argStr.strip()
        newCardTitle = argStr.strip('"')

        sql = f"SELECT ROWID FROM lists WHERE title={contextData['list']}"
        listId = self.db.execute(sql).fetchone()[0]

        sql = f'SELECT MAX(index) FROM cards WHERE name={listId}'
        newIdx = self.db.execute(sql).fetchone()[0] + 1

        values = (newCardTitle, newIdx, -1, listId)
        sql = f'INSERT INTO cards VALUES {values}'
        self.db.execute(sql)
        self.commit()
        return

    def newList(self, contextData, argStr):
        argStr.strip()
        newListTitle = argStr.strip('"')

        sql = f"SELECT ROWID FROM boards WHERE title={contextData['board']}"
        boardId = self.db.execute(sql).fetchone()[0]

        sql = f'SELECT MAX(index) FROM lists WHERE name={boardId}'
        newIdx = self.db.execute(sql).fetchone()[0] + 1

        values = (newListTitle, newIdx, -1, boardId)
        sql = f'INSERT INTO lists VALUES {values}'
        self.db.execute(sql)
        self.commit()
        return

    def newBoard(self, contextData, argStr, tree):
        argStr.strip()
        newBoardTitle = argStr.strip('"')

        sql = 'SELECT MAX(index) FROM boards'
        newIdx = self.db.execute(sql).fetchone()[0] + 1

        values = (newBoardTitle, newIdx)
        sql = f'INSERT INTO boards VALUES {values}'
        self.db.execute(sql)
        self.commit()
        return


