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
    action = Signal(int)

    def __init__(self, title, buttonId, parent=None):
        QPushButton.__init__(self, title)
        self.title = title
        self.buttonId = buttonId
        self.setStyleSheet('''
            QPushButton {
                background-color: #2e2e2e;
                color: #cccccc;
                max-width: 125px;
                min-width: 125px;
            };
        ''')
        self.clicked.connect(self.dispatchAction)
        return
    
    @Slot()
    def dispatchAction(self):
        self.action.emit(self.buttonId)
        return


class EditButton(QPushButton):
    editPressed = Signal(int)

    def __init__(self, buttonId):
        QPushButton.__init__(self, 'edit')
        self.buttonId = buttonId
        self.setStyleSheet('''
            QPushButton {
                background-color: #2e2e2e;
                color: #cccccc;
                max-width: 40px;
            };
        ''')
        self.pressed.connect(self.handlePress)
        return

    @Slot()
    def handlePress(self):
        self.editPressed.emit(self.buttonId)
        return


class EditDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.setStyleSheet('''
            QDialog {
                background-color: #2e2e2e;
                color: #cccccc;
                min-width: 500px;
            };
        ''')
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        nameLayout = QHBoxLayout()

        nameLabel = QLabel('Name:')
        nameLabel.setStyleSheet('QLabel { color: #cccccc; };')
        nameLayout.addWidget(nameLabel)

        nameEdit = QLineEdit()
        nameEdit.setStyleSheet('''
            QLineEdit {
                background-color: #2a2a2a;
                color: #cccccc;
            }; ''')
        nameLayout.addWidget(nameEdit)
        self.layout.addLayout(nameLayout)

        commandLayout = QHBoxLayout()

        commandLabel = QLabel('Command:')
        commandLabel.setStyleSheet('QLabel { color: #cccccc; };')
        commandLayout.addWidget(commandLabel)

        commandEdit = QLineEdit()
        commandEdit.setStyleSheet('''
            QLineEdit {
                background-color: #2a2a2a;
                color: #cccccc;
            }; ''')
        commandLayout.addWidget(commandEdit)
        self.layout.addLayout(commandLayout)

        buttonLayout = QHBoxLayout()
        cancelButton = QPushButton('Cancel')
        cancelButton.setStyleSheet('''
            QPushButton {
                background-color: #2e2e2e;
                color: #cccccc;
            };
        ''')
        saveButton = QPushButton('Save')
        saveButton.setStyleSheet('''
            QPushButton {
                background-color: #2e2e2e;
                color: #cccccc;
            };
        ''')
        buttonLayout.addWidget(saveButton)
        buttonLayout.addWidget(cancelButton)
        self.layout.addLayout(buttonLayout)
        return


class ButtonRow(QWidget):
    def __init__(self, title, buttonId, parent=None):
        QWidget.__init__(self)
        self.layout = QHBoxLayout()
        self.actionButton = ActionButton(title, buttonId)
        self.editButton = EditButton(buttonId)

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


class TrayContent(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.setStyleSheet('''
            QWidget {
                background-color: #2e2e2e;
                color: #cccccc;
            };
        ''')
        return


class ButtonTray(QScrollArea):
    getSelectedCards = Signal(list)
    getCurrentList = Signal(list)
    buttonPressed = Signal()

    def __init__(self, db, parent=None):
        QScrollArea.__init__(self)
        self.db = db
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
        self.content = TrayContent()
        self.setWidget(self.content)

        self.editDialog = EditDialog()
        self.additionButton = QPushButton('New Button')

        self.showButtons()
        self.buttons = []
        self.content.setAttribute(QtCore.Qt.WA_StyledBackground, True)

        self.buttonPressed.connect(self.showButtons)
        return

    @Slot()
    def showButtons(self):
        self.layout = QVBoxLayout()
        result = self.db.runCommand('show buttons')
        self.buttonRows = []
        contentHeight = 0
        buttonHeight = 50
        with io.StringIO(result) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                buttonRow = ButtonRow(row['name'], int(row['id']))
                buttonRow.actionButton.action.connect(self.actionButtonPressed)
                buttonRow.editButton.editPressed.connect(self.editButtonPressed)
                self.buttonRows.append(buttonRow)
                self.layout.addWidget(buttonRow)
                contentHeight += buttonHeight

        self.layout.addWidget(self.additionButton)
        contentHeight += buttonHeight

        self.content.setLayout(self.layout)
        self.content.setMinimumSize(220, contentHeight)
        return

    @Slot(int)
    def actionButtonPressed(self, buttonId):
        buttonCmd = self.db.runCommand(f'get button {buttonId}')
        selectedCards = []
        currentList = []

        self.getSelectedCards.emit(selectedCards)
        self.getCurrentList.emit(currentList)

        if '$CARD' in buttonCmd:
            for card in selectedCards:
                newCmd = str(buttonCmd)
                newCmd = newCmd.replace('$CARD', str(card))
                newCmd = newCmd.replace('$LIST', str(currentList[0]))
                self.db.runCommand(newCmd)
        else:
            newCmd = str(buttonCmd)
            newCmd.replace('$LIST', str(currentList[0]))
            self.db.runCommand(newCmd)
        self.buttonPressed.emit()
        return

    @Slot(int)
    def editButtonPressed(self, buttonId):
        self.editDialog.show()       
        return

    @Slot()
    def additionButtonPressed(self):
        return

