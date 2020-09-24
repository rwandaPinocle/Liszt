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


def getCards(db, listId):
    if listId == -1:
        return []
    result = db.runCommand(f'show-cards {listId}')
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
        self.itemType = 'CARD'
        self.name = name
        self.rowid = rowid
        self.setText(name)

    def __str__(self):
        return f'{self.itemType} {self.rowid} {self.name}'


class CardView(QListView):
    def __init__(self, db, parent=None):
        QListView.__init__(self)
        self.db = db
        self.setStyleSheet('''
                QListView {
                    font-size: 16pt;
                    background-color: #2e2e2e;
                    color: #cccccc;
                };
                ''')
        self.setWordWrap(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setSpacing(7)
        return


    @Slot(list)
    def selectedCards(self, cardList):
        indexes = self.selectedIndexes()
        for idx in indexes:
            cardModel = self.model().itemFromIndex(idx)
            cardId = cardModel.rowid
            cardList.append(cardId)
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
        try:
            for card in reversed(getCards(self.db, self.listId)):
                self.appendRow(card)
        except TypeError:
            pass
        return
    
    @Slot(int)
    def showListCards(self, listId):
        self.listId = listId
        self.refresh()
        return

    @Slot(list)
    def currentList(self, listidContainer):
        listidContainer.append(self.listId)
        return

    def mimeData(self, indexes):
        result = QMimeData()
        item = self.itemFromIndex(indexes[0])
        result.setText(f'{item.itemType}={item.rowid}')
        return result
