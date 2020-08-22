import io
import csv

from PySide2.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QVBoxLayout,
    QDockWidget,
    QWidget,
    QTableView,
    QHBoxLayout,
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
    QMimeData,
    QByteArray,
    Signal,
    Slot,
)


def getCards(db, listid):
    result = db.runCommand(f'show cards {listid}')
    cards = []
    with io.StringIO(result) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            card = Card(row['title'], row['id'])
            cards.append(card)
    return cards


class Card(QStandardItem):
    def __init__(self, name, rowid):
        QStandardItem.__init__(self)
        self.name = name
        self.rowid = rowid
        self.setText(name)


class CardView(QListView):
    def __init__(self, db, parent=None):
        QListView.__init__(self)
        self.db = db
        self.setStyleSheet('''
                QListView {
                    background-color: #2e2e2e;
                    color: #cccccc;
                };
                ''')
        self.setDragDropMode(QAbstractItemView.DragDrop)
        return


class CardModel(QStandardItemModel):
    def __init__(self, db):
        QStandardItemModel.__init__(self, parent=None)
        self.db = db
        self.listId = -1
        return

    @Slot()
    def refresh(self):
        self.clear()
        for card in reversed(getCards(self.db, self.listId)):
            self.appendRow(card)
        return
    
    @Slot(int)
    def showListCards(self, listId):
        self.listId = listId
        self.refresh()
        return

    @Slot()
    def currentList(self):
        return self.listId

    def mimeData(self, indexes):
        result = QMimeData()
        rowid = self.itemFromIndex(indexes[0]).rowid
        result.setText(f'CARD={rowid}')
        return result
