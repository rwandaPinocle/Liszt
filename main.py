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
    QAbstractItemView,
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
from sidebar import SidebarView, SidebarModel, Board, List
from center import CardView, CardModel


class NewCardTextBox(QLineEdit):
    newCardRequested = Signal(str, int)
    getCurrentList = Signal()
    cardAdded = Signal(int)

    def __init__(self):
        QLineEdit.__init__(self)
        self.returnPressed.connect(self.handleReturn)
        self.setStyleSheet('''
            QLineEdit {
                background-color: #2a2a2a;
                color: #cccccc;
            }; ''')
        return

    def handleReturn(self):
        text = self.text()
        listid = self.getCurrentList.emit()
        self.newCardRequested.emit(text, listid)
        self.cardAdded.emit(listid)
        self.setText('')
        return


class MainWidget(QWidget):
    def __init__(self, db, parent=None):
        QWidget.__init__(self)
        self.db = db
        self.cardView = CardView(db)
        self.sidebarView = SidebarView()
        self.newCardTextBox = NewCardTextBox()

        centralLayout = QVBoxLayout()
        centralLayout.addWidget(self.newCardTextBox)
        centralLayout.addWidget(self.cardView)

        mainLayout = QHBoxLayout()
        mainLayout.addWidget(self.sidebarView)
        mainLayout.addLayout(centralLayout)
        self.setLayout(mainLayout)

        self.setupSidebar()
        self.setupCardView()
        self.setupNewCardTextBox()
        return

    def setupNewCardTextBox(self):
        self.newCardTextBox.getCurrentList.connect(self.cardModel.currentList)
        self.newCardTextBox.newCardRequested.connect(self.makeNewCard)
        self.newCardTextBox.cardAdded.connect(self.cardModel.showListCards)
        return

    def setupSidebar(self):
        self.sidebarModel = SidebarModel(db)
        self.sidebarView.setModel(self.sidebarModel)
        return

    def setupCardView(self):
        self.cardModel = CardModel(self.db)
        self.cardView.setModel(self.cardModel)
        self.sidebarView.listClicked.connect(self.cardModel.showListCards)
        self.sidebarModel.cardChanged.connect(self.cardModel.refresh)
        return

    @Slot(str, int)
    def makeNewCard(self, text, listid):
        self.db.runCommand(f'add card "{text}" to {listid}')
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
