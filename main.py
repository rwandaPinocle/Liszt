# This Python file uses the following encoding: utf-8
import sys
import csv
import io

from PySide2.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QVBoxLayout,
    QDockWidget,
    QWidget,
    QTableView,
    QHBoxLayout,
    QVBoxLayout,
    QTreeView,
    QListView,
    QLineEdit,
)
from PySide2.QtCore import (
    QFile,
    Signal,
    Slot,
)
from PySide2.QtUiTools import QUiLoader
from PySide2.QtGui import (
    Qt,
    QStandardItemModel,
    QStandardItem,
)

from database import Database


class Board(QStandardItem):
    def __init__(self, name, rowid):
        QStandardItem.__init__(self)
        self.name = name
        self.rowid = rowid
        self.setText(f'{rowid}  {name}')


class List(QStandardItem):
    def __init__(self, name, rowid):
        QStandardItem.__init__(self)
        self.name = name
        self.rowid = rowid
        self.setText(f'{rowid}  {name}')


class Card(QStandardItem):
    def __init__(self, name, rowid):
        QStandardItem.__init__(self)
        self.name = name
        self.rowid = rowid
        self.setText(f'{rowid}\t{name}')


class SidebarView(QTreeView):
    listClicked = Signal(int)

    def __init__(self, parent=None):
        QTreeView.__init__(self)

        self.setStyleSheet('''
                QTreeView {
                    background-color: #2e2e2e;
                    color: #cccccc;
                    min-width: 200px;
                    max-width: 200px
                };
                ''')

        self.header().hide()
        self.clicked.connect(self.sendListId)
        return

    def sendListId(self, modelIdx):
        item = modelIdx.model().itemFromIndex(modelIdx)
        if type(item) == List:
            listid = int(item.rowid)
            self.listClicked.emit(listid)
        return


class SidebarModel(QStandardItemModel):
    def __init__(self):
        QStandardItemModel.__init__(self, parent=None)
        return


class CardView(QListView):
    def __init__(self, parent=None):
        QListView.__init__(self)
        self.db = db
        self.setStyleSheet('''
                QListView {
                    background-color: #2e2e2e;
                    color: #cccccc;
                };
                ''')
        return

class CardModel(QStandardItemModel):
    def __init__(self, db):
        QStandardItemModel.__init__(self, parent=None)
        self.db = db
        return

    @Slot(int)
    def showListCards(self, listId):
        print('recieved showListCards:', listId)
        self.clear()
        for card in getCards(self.db, listId):
            self.appendRow(card)
        return


def getBoards(db):
    result = db.runCommand('show boards')
    boards = []
    with io.StringIO(result) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            board = Board(row['title'], row['id'])
            boards.append(board)
    return boards


def getLists(db, boardId):
    result = db.runCommand(f'show lists {boardId}')
    lists = []
    with io.StringIO(result) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            _list = List(row['title'], row['id'])
            lists.append(_list)
    return lists


def getCards(db, listid):
    result = db.runCommand(f'show cards {listid}')
    cards = []
    with io.StringIO(result) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            card = Card(row['title'], row['id'])
            cards.append(card)
    return cards
'''
Upon hitting return, add the card to the db and refresh the display
'''


class NewCardTextBox(QLineEdit):
    # TODO: Connect this signal
    newCard = Signal(str)

    def __init__(self):
        QLineEdit.__init__(self)
        self.returnPressed.connect(self.handleReturn)
        return

    def handleReturn(self):
        text = self.text()
        self.sendNewCardText.emit(text)
        self.setText("Enter new card name here...")
        return


class MainWidget(QWidget):
    def __init__(self, db, parent=None):
        QWidget.__init__(self)
        self.db = db
        self.cardView = CardView()
        self.sidebarView = SidebarView()
        self.newCardTextBox = QLineEdit()

        sidebarLayout = QVBoxLayout()
        sidebarLayout.addWidget(self.sidebarView)
        sidebarLayout.addWidget(self.newCardTextBox)

        mainLayout = QHBoxLayout()
        mainLayout.addWidget(self.sidebarView)
        mainLayout.addWidget(self.cardView)
        self.setLayout(mainLayout)

        self.setupSidebar()
        self.setupCardView()
        self.setupNewCardTextBox()
        return

    def setupNewCardTextBox(self):
        return

    def setupSidebar(self):
        self.sidebarModel = SidebarModel()
        rootNode = self.sidebarModel.invisibleRootItem()
        self.sidebarView.setModel(self.sidebarModel)

        for board in getBoards(self.db):
            rootNode.appendRow(board)
            for _list in getLists(self.db, board.rowid):
                board.appendRow(_list)
        return

    def setupCardView(self):
        self.cardModel = CardModel(self.db)
        self.cardView.setModel(self.cardModel)
        self.sidebarView.listClicked.connect(self.cardModel.showListCards)
        return


class LisztWindow(QMainWindow):
    def __init__(self, db, parent=None):

        QMainWindow.__init__(self)
        self.setStyleSheet('''
                QMainWindow {
                    background-color: #212121;
                }
        ''')
        mainWidget = MainWidget(db)
        self.setCentralWidget(mainWidget)
        self.setWindowTitle('Liszt')
        return


if __name__ == "__main__":
    app = QApplication([])
    db = Database()
    mainWin = LisztWindow(db)
    mainWin.setFixedSize(600, 400)
    mainWin.show()
    sys.exit(app.exec_())
