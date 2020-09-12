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
        return


class EditButton(QPushButton):
    def __init__(self, buttonId):
        QPushButton.__init__(self, 'edit')
        self.setStyleSheet('''
            QPushButton {
                background-color: #2e2e2e;
                color: #cccccc;
                max-width: 40px;
            };
        ''')
        return


class EditDialog(QDialog):
    buttonEditsSaved = Signal(str, str, int)

    def __init__(self):
        QDialog.__init__(self)
        self.buttonId = -1
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

        self.nameTextEdit = QLineEdit()
        self.nameTextEdit.setStyleSheet('''
            QLineEdit {
                background-color: #2a2a2a;
                color: #cccccc;
            }; ''')
        nameLayout.addWidget(self.nameTextEdit)
        self.layout.addLayout(nameLayout)

        commandLayout = QHBoxLayout()

        commandLabel = QLabel('Command:')
        commandLabel.setStyleSheet('QLabel { color: #cccccc; };')
        commandLayout.addWidget(commandLabel)

        self.commandTextEdit = QLineEdit()
        self.commandTextEdit.setStyleSheet('''
            QLineEdit {
                background-color: #2a2a2a;
                color: #cccccc;
            }; ''')
        commandLayout.addWidget(self.commandTextEdit)
        self.layout.addLayout(commandLayout)

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
        self.layout.addLayout(buttonLayout)
        return

    def showWithText(self, name, cmd, buttonId=-1):
        self.buttonId = buttonId
        self.commandTextEdit.setText(cmd)
        self.nameTextEdit.setText(name)
        self.show()
        return

    @Slot()
    def handleSave(self):
        cmdText = self.commandTextEdit.text()
        nameText = self.nameTextEdit.text()
        self.buttonEditsSaved.emit(nameText, cmdText, self.buttonId)
        self.close()
        return


class ButtonRow(QWidget):
    dispatchAction = Signal(int)
    editButtonPressed = Signal(str, str, int)

    def __init__(self, title, buttonId, command, parent=None):
        QWidget.__init__(self)
        self.layout = QHBoxLayout()
        self.actionButton = ActionButton(title, buttonId)
        self.actionButton.pressed.connect(self.handleActionButton)
        self.editButton = EditButton(buttonId)
        self.editButton.pressed.connect(self.sendEditInfo)

        self.buttonTitle = title
        self.command = command
        self.buttonId = buttonId

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

    @Slot()
    def sendEditInfo(self):
        self.editButtonPressed.emit(self.buttonTitle, self.command, self.buttonId)
        return

    @Slot()
    def handleActionButton(self):
        self.dispatchAction.emit(self.buttonId)
        return


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
        self.editDialog.buttonEditsSaved.connect(self.handleEditChanges)

        self.content.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.showButtons()
        self.buttons = []

        self.buttonPressed.connect(self.showButtons)
        return

    @Slot()
    def showButtons(self):
        layout = QVBoxLayout()
        result = self.db.runCommand('show buttons')
        self.buttonRows = []
        contentHeight = 0
        buttonHeight = 50
        with io.StringIO(result) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                buttonName = row['name']
                buttonId = int(row['id'])
                buttonCmd = self.db.runCommand(f'get button {buttonId}')

                buttonRow = ButtonRow(row['name'], buttonId, buttonCmd)
                print('Making button ', row['name'])
                buttonRow.dispatchAction.connect(self.actionButtonPressed)
                buttonRow.editButtonPressed.connect(self.editDialog.showWithText)

                self.buttonRows.append(buttonRow)
                layout.addWidget(buttonRow)
                contentHeight += buttonHeight

        self.additionButton = QPushButton('New Button')
        layout.addWidget(self.additionButton)
        contentHeight += buttonHeight

        self.content.setLayout(layout)
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

    @Slot(str, str, int)
    def handleEditChanges(self, name, command, buttonId):
        if buttonId == -1:
            command = f'update button {buttonId} "{name}" "{command}"'
        else:
            command = f'add button "{name}" "{command}"'
        print('run command')
        self.db.runCommand(command)
        print('showing buttons')
        self.showButtons()
        return

