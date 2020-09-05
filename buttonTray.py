
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
    QScrollArea,
    QPushButton,
    QStylePainter,
    QStyleOption,
)
from PySide2.QtGui import (
    Qt,
    QStandardItemModel,
    QStandardItem,
    QPainter,
    QPalette,
)
from PySide2.QtCore import (
    QFile,
    QMimeData,
    QByteArray,
    Signal,
    Slot,
)
from PySide2 import QtCore


class ActionButton(QPushButton):
    def __init__(self, title, action, parent=None):
        QPushButton.__init__(self, title)
        self.title = title
        self.action = action
        self.setStyleSheet('''
            QPushButton {
                background-color: #2e2e2e;
                color: #cccccc;
                max-width: 125px;
                min-width: 125px;
            };
        ''')
        return


class EditButton(QPushButton):
    def __init__(self):
        return


class ButtonRow(QWidget):
    def __init__(self, title, action, parent=None):
        QWidget.__init__(self)
        self.layout = QHBoxLayout()
        self.actionButton = QPushButton(title)
        self.editButton = QPushButton('edit')

        self.editButton.setStyleSheet('''
            QPushButton {
                background-color: #2e2e2e;
                color: #cccccc;
                max-width: 40px;
            };
        ''')

        self.setStyleSheet('''
            QWidget {
                background-color: #2e2e2e;
            };
        ''')

        self.layout.addWidget(self.actionButton)
        self.layout.addWidget(self.editButton)
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        return

    '''
    def paintEvent(self, event):
        painter = QStylePainter(self)
        option = QStyleOption()
        palette = self.palette()
        return
    '''



class ButtonTray(QScrollArea):
    def __init__(self, db, parent=None):
        QScrollArea.__init__(self)
        self.setStyleSheet('''
            QScrollArea {
                background-color: #2e2e2e;
                color: #cccccc;
                min-width: 220px;
                max-width: 220px
            };

        ''')
        self.verticalScrollBar().setStyleSheet('''
            QScrollBar:vertical {
                background: #2e2e2e;
            };
        ''')
        self.content = QWidget()
        self.content.setMinimumSize(200, 2000)
        self.content.setStyleSheet('''
            QWidget {
                background-color: #2e2e2e;
                color: #cccccc;
            };
        ''')
        self.setWidget(self.content)

        self.layout = QVBoxLayout()
        self.content.setLayout(self.layout)
        #self.setLayout(self.layout)

        self.showButtons()
        self.buttons = []
        #self.setMinimumSize(200, 1000)
        self.content.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        return

    def showButtons(self):
        self.buttons = []
        for i in range(50):
            buttonRow = ButtonRow(f'Button {i}', '')
            self.buttons.append(buttonRow)
            self.layout.addWidget(buttonRow)
        return

    @Slot()
    def adjustSize(self, rowCount):
        return


