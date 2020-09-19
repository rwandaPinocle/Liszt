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
    result = db.runCommand('show-boards')
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
    result = db.runCommand(f'show-lists {boardId}')
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
        self.rowid = int(rowid)
        self.setText(f'({rowid})  {name}')


class List(QStandardItem):
    def __init__(self, name, rowid):
        QStandardItem.__init__(self)
        self.name = name
        self.rowid = int(rowid)
        self.setText(f'({rowid})  {name}')


class BoardContextMenu(QMenu):
    renameBoardClick = Signal()
    deleteBoardClick = Signal()
    addListToBoardClick = Signal()

    def __init__(self, parent=None):
        QMenu.__init__(self)
        action = self.addAction('Rename')
        action.triggered.connect(lambda x: self.renameBoardClick.emit())
        
        action = self.addAction('Delete')
        action.triggered.connect(lambda x: self.deleteBoardClick.emit())

        action = self.addAction('Add List')
        action.triggered.connect(lambda x: self.addListToBoardClick.emit())

        self.setStyleSheet('''
            QMenu {
                background-color: #2e2e2e;
                color: #cccccc;
            };
        ''')


class ListContextMenu(QMenu):
    renameListClick = Signal()
    deleteListClick = Signal()

    def __init__(self, parent=None):
        QMenu.__init__(self)
        action = self.addAction('Rename')
        action.triggered.connect(lambda x: self.renameListClick.emit())

        action = self.addAction('Delete')
        action.triggered.connect(lambda x: self.deleteListClick.emit())

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
    addList = Signal(str, int)

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
        self.setWordWrap(True)

        self.renameListDialog = RenameDialog('New List Name')
        self.renameBoardDialog = RenameDialog('New Board Name')

        self.setupContextMenus()
        return

    def setupContextMenus(self):
        self.boardMenu = BoardContextMenu()
        self.boardMenu.renameBoardClick.connect(self.onRenameBoardClick)
        self.boardMenu.deleteBoardClick.connect(self.onDeleteBoardClick)
        self.boardMenu.addListToBoardClick.connect(self.onAddListToBoardClick)

        self.listMenu = ListContextMenu()
        self.listMenu.renameListClick.connect(self.onRenameListClick)
        self.listMenu.deleteListClick.connect(self.onDeleteListClick)

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

    @Slot()
    def onRenameListClick(self):
        listIndex = self.selectedIndexes()[0]
        item = listIndex.model().itemFromIndex(listIndex)
        titleText = "Rename List"
        labelText = "New Name:"
        newName, ok = QInputDialog().getText(self, titleText, labelText)
        if ok:
            self.renameList.emit(newName, int(item.rowid))
        return

    @Slot()
    def onDeleteListClick(self):
        listIndex = self.selectedIndexes()[0]
        item = listIndex.model().itemFromIndex(listIndex)
        titleText = "Delete List"
        labelText = f'To delete, type "{item.name}"'
        confirm, ok = QInputDialog().getText(self, titleText, labelText)
        if ok and confirm == item.name:
            self.deleteList.emit(item.rowid)
        return

    @Slot()
    def onRenameBoardClick(self):
        boardIndex = self.selectedIndexes()[0]
        item = boardIndex.model().itemFromIndex(boardIndex)
        titleText = "Rename Board"
        labelText = "New Name:"
        newName, ok = QInputDialog().getText(self, titleText, labelText)
        if ok:
            self.renameBoard.emit(newName, item.rowid)
        return

    @Slot()
    def onDeleteBoardClick(self):
        boardIndex = self.selectedIndexes()[0]
        item = boardIndex.model().itemFromIndex(boardIndex)
        titleText = "Delete Board"
        labelText = f'To delete, type "{item.name}"'
        confirm, ok = QInputDialog().getText(self, titleText, labelText)
        if ok and confirm == item.name:
            self.deleteBoard.emit(item.rowid)
        return

    @Slot()
    def onAddListToBoardClick(self):
        boardIndex = self.selectedIndexes()[0]
        item = boardIndex.model().itemFromIndex(boardIndex)
        titleText = "New List"
        labelText = "Name:"
        newName, ok = QInputDialog().getText(self, titleText, labelText)
        if ok:
            self.addList.emit(newName, item.rowid)
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
            self.listClicked.emit(int(item.rowid))
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
            cmd = f'move-card {cardId} to {target.rowid}'
            self.db.runCommand(cmd)
            self.cardChanged.emit()
            return True
        else:
            return False

    def mimeTypes(self):
        return ['text/plain']

    @Slot(str, int)
    def onRenameList(self, name, rowid):
        cmd = f'rename-list {rowid} "{name}"'
        self.db.runCommand(cmd)
        self.refresh()
        return

    @Slot(str, int)
    def onRenameBoard(self, name, rowid):
        cmd = f'rename-board {rowid} "{name}"'
        self.db.runCommand(cmd)
        self.refresh()
        return

    @Slot(int)
    def onDeleteList(self, rowid):
        cmd = f'delete-list {rowid}'
        self.db.runCommand(cmd)
        self.refresh()
        return

    @Slot(int)
    def onDeleteBoard(self, rowid):
        cmd = f'delete-board {rowid}'
        self.db.runCommand(cmd)
        self.refresh()
        return

    @Slot(str, int)
    def onAddList(self, name, boardid):
        cmd = f'add-list "{name}" to {boardid}'
        self.db.runCommand(cmd)
        self.refresh()
        return
