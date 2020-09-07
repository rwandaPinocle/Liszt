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
from buttonTray import ButtonTray
from center import CardView, CardModel


class NewCardTextBox(QLineEdit):
    newCardRequested = Signal(str, int)
    getCurrentList = Signal(list)
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
        listIdContainer = []
        self.getCurrentList.emit(listIdContainer)
        listId = listIdContainer[0]

        self.newCardRequested.emit(text, listId)
        self.cardAdded.emit(listId)
        self.setText('')
        return


class MainWidget(QWidget):
    def __init__(self, db, parent=None):
        QWidget.__init__(self)
        self.db = db
        self.cardView = CardView(db)
        self.newCardTextBox = NewCardTextBox()

        mainLayout = QHBoxLayout()

        self.sidebarView = SidebarView()
        mainLayout.addWidget(self.sidebarView)

        centralLayout = QVBoxLayout()
        centralLayout.addWidget(self.newCardTextBox)
        centralLayout.addWidget(self.cardView)
        mainLayout.addLayout(centralLayout)

        self.buttonTray = ButtonTray(db)
        mainLayout.addWidget(self.buttonTray)

        self.setLayout(mainLayout)

        self.setupSidebar()
        self.setupCardView()
        self.setupNewCardTextBox()
        self.setupButtonTray()
        return

    def setupNewCardTextBox(self):
        self.newCardTextBox.getCurrentList.connect(self.cardModel.currentList)
        self.newCardTextBox.newCardRequested.connect(self.makeNewCard)
        self.newCardTextBox.cardAdded.connect(self.cardModel.showListCards)
        return

    def setupSidebar(self):
        self.sidebarModel = SidebarModel(db)
        self.sidebarView.setModel(self.sidebarModel)
        self.sidebarModel.rowsInserted.connect(self.sidebarView.expandAll)
        return

    def setupCardView(self):
        self.cardModel = CardModel(self.db)
        self.cardView.setModel(self.cardModel)
        self.sidebarView.listClicked.connect(self.cardModel.showListCards)
        self.sidebarModel.cardChanged.connect(self.cardModel.refresh)
        self.sidebarView.expandAll()
        return

    def setupButtonTray(self):
        self.buttonTray.buttonPressed.connect(self.cardModel.refresh)
        self.buttonTray.buttonPressed.connect(self.sidebarModel.refresh)
        self.buttonTray.getCurrentList.connect(self.cardModel.currentList)
        self.buttonTray.getSelectedCards.connect(self.cardView.selectedCards)
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
    mainWin.setFixedSize(1000, 800)
    mainWin.show()
    sys.exit(app.exec_())
