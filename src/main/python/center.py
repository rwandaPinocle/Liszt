import io
import csv
import datetime

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
    QDialog,
    QTextEdit,
    QPushButton,
    QCalendarWidget,
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
    QModelIndex,
    QDate,
    Qt,
    Signal,
    Slot,
)

from database import decodeFromDB, encodeForDB


def getCards(db, listId):
    if listId == -1:
        return []
    result = db.runCommand(f'show-cards {listId}')
    cards = []
    with io.StringIO(result) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for idx, row in enumerate(reader):
            card = Card(
                row['title'],
                int(row['id']),
                idx,
                row['content'],
                int(row['due']))
            cards.append(card)
    return cards


def toLocalTime(sec):
    # Seconds since epoch to local time
    dateInfo = datetime.datetime.fromtimestamp(sec)
    result = dateInfo.strftime('%A, %d %b %Y')
    return result

# TODO: Create a json serialization of Card, List, and Board


class Card(QStandardItem):
    def __init__(self, name, rowid, idx, content, dueDate):
        QStandardItem.__init__(self)
        self.itemType = 'CARD'
        self.name = decodeFromDB(name)
        self.content = decodeFromDB(content)
        self.dueDate = int(dueDate)
        self.rowid = int(rowid)
        suffix = ''
        if self.content:
            suffix += ' *'
        if self.dueDate > 0:
            dateInfo = datetime.datetime.fromtimestamp(dueDate)
            suffix += f" (Due: {dateInfo.strftime('%A, %d %b %Y')})"
        self.setText(self.name + suffix)
        self.idx = int(idx)

    def __str__(self):
        return f'{self.itemType}::{self.rowid}::{self.idx}::{self.name}'


class CardView(QListView):
    showCard = Signal(Card)

    def __init__(self, db, parent=None):
        QListView.__init__(self)
        self.db = db
        self.setStyleSheet('''
                QListView {
                    font-size: 16pt;
                    background-color: #2e2e2e;
                    color: #cccccc;
                }

                QListView::item {
                     padding: 10px;
                }
                ''')
        self.setWordWrap(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.doubleClicked.connect(self.onDoubleClick)
        return

    @Slot(QModelIndex)
    def onDoubleClick(self, index):
        card = self.model().itemFromIndex(index)
        self.showCard.emit(card)
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

    def dropMimeData(self, data, action, row, column, parent):
        result = False
        if 'CARD' in data.text():
            _, cardId, cardIdx, _ = data.text().split('::')
            cardId, cardIdx = int(cardId), int(cardIdx)
            row = self.rowCount() - row

            if row == cardIdx or (row - 1) == cardIdx:
                return True

            if cardIdx > row:
                newIdx = row
            else:
                newIdx = row - 1

            cmd = f'shift-card {cardId} to {newIdx}'
            self.db.runCommand(cmd)
            self.refresh()
            result = True
        return result

    def canDropMimeData(self, data, action, row, col, parent):
        isCard = 'CARD' in data.text()
        isBetweenCards = (row != -1 and self.itemFromIndex(parent) is None)
        return (isCard and isBetweenCards)

    def mimeData(self, indexes):
        result = QMimeData()
        item = self.itemFromIndex(indexes[0])
        result.setText(str(item))
        return result

    def mimeTypes(self):
        return ['text/plain']

    @Slot()
    def onCardEdited(self, title, content, dueDate, cardId):
        title = encodeForDB(title)
        content = encodeForDB(content)
        self.db.runCommand(f'rename-card {cardId} "{title}"')
        self.db.runCommand(f'set-card-content {cardId} "{content}"')
        self.db.runCommand(f'set-due-date {cardId} {dueDate}')
        self.refresh()
        return


class CardEditWidget(QDialog):
    cardEdited = Signal(str, str, int, int)  # (name, content, dueDate, id)

    def __init__(self):
        QDialog.__init__(self)
        self.setStyleSheet('''
            QDialog {
                background-color: #2e2e2e;
                color: #cccccc;
                min-width: 500px;
            };
        ''')

        self.cardTitle = ''
        self.dueDate = -1
        self.content = ''
        self.cardId = -1

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        nameLayout = self.makeNameLayout()
        self.layout.addLayout(nameLayout)

        dueDateLayout = self.makeDueDateLayout()
        self.layout.addLayout(dueDateLayout)

        contentLayout = self.makeContentLayout()
        self.layout.addLayout(contentLayout)

        buttonLayout = self.makeButtonLayout()
        self.layout.addLayout(buttonLayout)
        return

    def makeNameLayout(self):
        nameLayout = QHBoxLayout()

        nameLabel = QLabel('Title:')
        nameLabel.setStyleSheet('QLabel { color: #cccccc; };')
        nameLayout.addWidget(nameLabel)

        self.nameTextEdit = QLineEdit()
        self.nameTextEdit.setStyleSheet('''
            QLineEdit {
                background-color: #2a2a2a;
                color: #cccccc;
            }; ''')
        nameLayout.addWidget(self.nameTextEdit)
        return nameLayout

    def makeDueDateLayout(self):
        dueDateLayout = QVBoxLayout()
        rowLayout = QHBoxLayout()
        dateLabel = QLabel('Due Date:')
        dateLabel.setStyleSheet('QLabel { color: #cccccc; };')
        rowLayout.addWidget(dateLabel)
        dateLineEdit = QLineEdit()
        dateLineEdit.setStyleSheet('''
            QLineEdit {
                background-color: #2a2a2a;
                color: #cccccc;
            }; ''')
        if self.dueDate > 0:
            dateLineEdit.setText(toLocalTime(self.dueDate))
        else:
            dateLineEdit.setText('None')
        self.dateLineEdit = dateLineEdit

        calWidget = QCalendarWidget()
        calWidget.setStyleSheet('''
            QCalendarWidget QWidget {
                background-color: #2a2a2a;
                alternate-background-color: #303030;
                color: #cccccc;
            }
            QCalendarWidget QToolButton {
                background-color: #2a2a2a;
                alternate-background-color: #303030;
                color: #cccccc;
            }
            QCalendarWidget QAbstractItemView {
                background-color: #2a2a2a;
                alternate-background-color: #303030;
                color: #cccccc;
            } ''')
        calWidget.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        calWidget.clicked.connect(self.onCalendarClick)

        rowLayout.addWidget(dateLineEdit)
        dueDateLayout.addLayout(rowLayout)
        dueDateLayout.addWidget(calWidget)
        return dueDateLayout

    def makeContentLayout(self):
        contentLayout = QVBoxLayout()
        contentLabel = QLabel('Content:')
        contentLabel.setStyleSheet('QLabel { color: #cccccc; };')
        contentLayout.addWidget(contentLabel)

        self.contentEdit = QTextEdit()
        self.contentEdit.setStyleSheet('''
            QTextEdit {
                background-color: #2a2a2a;
                color: #cccccc;
            }; ''')
        contentLayout.addWidget(self.contentEdit)
        return contentLayout

    def makeButtonLayout(self):
        buttonLayout = QHBoxLayout()
        cancelButton = QPushButton('Cancel')
        cancelButton.setStyleSheet('''
            QPushButton {
                background-color: #2e2e2e;
                color: #cccccc;
            };
        ''')
        cancelButton.clicked.connect(self.close)

        saveButton = QPushButton('Save')
        saveButton.setStyleSheet('''
            QPushButton {
                background-color: #2e2e2e;
                color: #cccccc;
            };
        ''')
        saveButton.clicked.connect(self.handleSave)

        buttonLayout.addWidget(saveButton)
        buttonLayout.addWidget(cancelButton)
        return buttonLayout

    @Slot(Card)
    def showCard(self, card):
        self.cardTitle = card.name
        self.nameTextEdit.setText(card.name)
        self.dueDate = card.dueDate
        if self.dueDate > 0:
            self.dateLineEdit.setText(toLocalTime(self.dueDate))
        else:
            self.dateLineEdit.setText('None')
        self.content = card.content
        self.contentEdit.setPlainText(card.content)
        self.cardId = card.rowid
        self.show()
        return

    @Slot()
    def handleSave(self):
        self.close()
        self.content = self.contentEdit.toPlainText()
        self.cardTitle = self.nameTextEdit.text()
        self.cardEdited.emit(
                self.cardTitle, self.content,
                self.dueDate, self.cardId)
        return

    @Slot(QDate)
    def onCalendarClick(self, date):
        dateInfo = date.startOfDay(Qt.TimeSpec.LocalTime)
        self.dueDate = dateInfo.toSecsSinceEpoch()
        self.dateLineEdit.setText(toLocalTime(self.dueDate))
