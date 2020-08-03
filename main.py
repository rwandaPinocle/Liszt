# This Python file uses the following encoding: utf-8
import sys
import os


from PySide2.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QVBoxLayout,
    QDockWidget,
    QWidget,
    QTableView,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
)
from PySide2.QtCore import QFile
from PySide2.QtUiTools import QUiLoader
from PySide2.QtGui import Qt


class Sidebar(QTreeWidget):
    def __init__(self, parent=None):
        QTreeWidget.__init__(self)

        self.setStyleSheet('''
                QTreeWidget {
                    background-color: #2e2e2e;
                    color: #cccccc;
                    min-width: 200px;
                    max-width: 200px
                };
                ''')

        self.setColumnCount(1)
        self.header().hide()
        items = []
        for i in range(10):
            items.append(QTreeWidgetItem(None, [f'item: {i}']))
        self.insertTopLevelItems(0, items)

        self.header = QTreeWidgetItem(None, ['Boards'])
        self.setHeaderItem(self.header)

        return


class CardView(QTableView):
    def __init__(self, parent=None):
        QTableView.__init__(self)
        self.setStyleSheet('''
                QTableView {
                    background-color: #2e2e2e;
                    color: #cccccc;
                };
                ''')
        return


class MainWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self)
        self.sidebar = Sidebar()
        self.cardView = CardView()

        mainLayout = QHBoxLayout()
        mainLayout.addWidget(self.sidebar)
        mainLayout.addWidget(self.cardView)
        self.setLayout(mainLayout)
        return


class LisztWindow(QMainWindow):
    def __init__(self, parent=None):

        QMainWindow.__init__(self)
        self.setStyleSheet('''
                QMainWindow {
                    background-color: #212121;
                }
        ''')
        mainWidget = MainWidget()
        self.setCentralWidget(mainWidget)
        self.setWindowTitle('Liszt')
        return


if __name__ == "__main__":
    app = QApplication([])
    mainWin = LisztWindow()
    mainWin.show()
    sys.exit(app.exec_())
