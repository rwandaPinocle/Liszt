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
    QMenu,
    QInputDialog,
)
from PySide2.QtGui import (
    Qt,
    QStandardItemModel,
    QStandardItem,
    QCursor,
)
from PySide2.QtCore import (
    QFile,
    QPoint,
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
    if boardId == -1:
        return []
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
        self.setText(f'({rowid})  {name}')


class List(QStandardItem):
    def __init__(self, name, rowid):
        QStandardItem.__init__(self)
        self.name = name
        self.rowid = rowid
        self.setText(f'({rowid})  {name}')


class BoardContextMenu(QMenu):
    renameBoard = Signal()
    deleteBoard = Signal()
    addListToBoard = Signal()

    def __init__(self, parent=None):
        QMenu.__init__(self)
        action = self.addAction('Rename')
        action.triggered.connect(lambda x: self.renameBoard.emit())
        
        action = self.addAction('Delete')
        action.triggered.connect(lambda x: self.deleteBoard.emit())

        action = self.addAction('Add List')
        action.triggered.connect(lambda x: self.addListToBoard.emit())

        self.setStyleSheet('''
            QMenu {
                background-color: #2e2e2e;
                color: #cccccc;
            };
        ''')


class ListContextMenu(QMenu):
    renameBoard = Signal()
    deleteBoard = Signal()

    def __init__(self, parent=None):
        QMenu.__init__(self)
        action = self.addAction('Rename')
        action.triggered.connect(lambda x: self.renameBoard.emit())

        action = self.addAction('Delete')
        action.triggered.connect(lambda x: self.deleteBoard.emit())

        self.setStyleSheet('''
            QMenu {
                background-color: #2e2e2e;
                color: #cccccc;
            };
        ''')


class RenameDialog(QInputDialog):
    def __init__(self, labelText, parent=None):
        QInputDialog.__init__(self, parent=parent)
        self.setInputMode(QInputDialog.TextInput)
        self.setLabelText(labelText)
        return

    def showWithSuggestion(self, suggestion):
        self.setTextValue(suggestion)
        return


class SidebarView(QTreeView):
    listClicked = Signal(int)
    readyForUpdate = Signal()
    renameList = Signal(str, int)
    renameBoard = Signal(str, int)
    deleteList = Signal(int)
    deleteBoard = Signal(int)
    addList = Signal(str)

    def __init__(self, parent=None):
        QTreeView.__init__(self, parent=parent)

        self.setStyleSheet('''
                QTreeView {
                    font-size: 14pt;
                    background-color: #2e2e2e;
                    color: #cccccc;
                    min-width: 200px;
                    max-width: 200px
                };
                ''')

        self.header().hide()
        self.clicked.connect(self.sendListId)
        self.setDragDropMode(QAbstractItemView.DragDrop)

        self.renameListDialog = RenameDialog('New List Name')
        self.renameBoardDialog = RenameDialog('New Board Name')

        self.setupContextMenus()
        return

    def setupContextMenus(self):
        self.boardMenu = BoardContextMenu()
        self.listMenu = ListContextMenu()

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(
                self.onCustomContextMenuRequested)
        return

    def sendListId(self, modelIdx):
        item = modelIdx.model().itemFromIndex(modelIdx)
        if type(item) == List:
            listid = int(item.rowid)
            self.listClicked.emit(listid)
        return

    # TODO: Fill these out and connect them to the context menus
    @Slot()
    def onRenameList(self):
        return

    @Slot()
    def onDeleteList(self):
        return

    @Slot()
    def onRenameBoard(self):
        return

    @Slot()
    def onDeleteBoard(self):
        return

    @Slot()
    def onAddListToBoard(self):
        return

    @Slot(QPoint)
    def onCustomContextMenuRequested(self, point):
        index = self.indexAt(point)
        item = self.model().itemFromIndex(index)
        globalPoint = self.viewport().mapToGlobal(point)
        if type(item) == Board:
            self.boardMenu.exec_(globalPoint)
        elif type(item) == List:
            self.listMenu.exec_(globalPoint)
        return


class SidebarModel(QStandardItemModel):
    cardChanged = Signal()

    def __init__(self, db):
        QStandardItemModel.__init__(self, parent=None)
        self.db = db
        self.refresh()
        return

    def refresh(self):
        self.clear()
        rootNode = self.invisibleRootItem()
        for board in getBoards(self.db):
            rootNode.appendRow(board)
            for _list in getLists(self.db, board.rowid):
                board.appendRow(_list)
        return

    def dropMimeData(self, data, action, row, column, parent):
        target = self.itemFromIndex(parent)
        if type(target) == List and 'CARD' in data.text():
            cardId = data.text().split('=')[-1]
            cmd = f'move card {cardId} to {target.rowid}'
            self.db.runCommand(cmd)
            self.cardChanged.emit()
            return True
        else:
            return False

    def mimeTypes(self):
        return ['text/plain']
