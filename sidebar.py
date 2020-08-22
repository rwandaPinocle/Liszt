import io
import csv
from PySide2.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QDockWidget,
    QWidget,
    QTableView,
    QHBoxLayout,
    QVBoxLayout,
    QTreeView,
    QListView,
    QLineEdit,
    QAbstractItemView,
)
from PySide2.QtGui import (
    Qt,
    QStandardItemModel,
    QStandardItem,
)
from PySide2.QtCore import (
    QFile,
    Signal,
    Slot,
)


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
        self.setDragDropMode(QAbstractItemView.DragDrop)
        return

    def sendListId(self, modelIdx):
        item = modelIdx.model().itemFromIndex(modelIdx)
        if type(item) == List:
            listid = int(item.rowid)
            self.listClicked.emit(listid)
        return


class SidebarModel(QStandardItemModel):
    cardChanged = Signal()

    def __init__(self, db):
        QStandardItemModel.__init__(self, parent=None)
        self.db = db
        self.refresh()
        return

    def refresh(self):
        rootNode = self.invisibleRootItem()
        for board in getBoards(self.db):
            rootNode.appendRow(board)
            for _list in getLists(self.db, board.rowid):
                board.appendRow(_list)
        return

    def dropMimeData(self, data, action, row, column, parent):
        target = self.itemFromIndex(parent)
        if type(target) == List and 'CARD' in data.text():
            cardid = data.text().split('=')[-1]
            cmd = f'move card {cardid} to {target.rowid}'
            self.db.runCommand(cmd)
            self.cardChanged.emit()
            return True
        else:
            return False

    def mimeTypes(self):
        return ['text/plain']





