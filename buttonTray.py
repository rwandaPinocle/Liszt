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
    def __init__(self, title, parent=None):
        QPushButton.__init__(self, title)
        self.title = title
        self.setStyleSheet('''
            QPushButton {
                font-size: 11pt;
                background-color: #2e2e2e;
                color: #cccccc;
                max-width: 145px;
                min-width: 145px;
            };
        ''')
        return


class EditButton(QPushButton):
    def __init__(self):
        QPushButton.__init__(self, 'Edit')
        self.setStyleSheet('''
            QPushButton {
                font-size: 10pt;
                background-color: #2e2e2e;
                color: #cccccc;
                max-width: 30px;
            };
        ''')
        return


class DeleteButton(QPushButton):
    def __init__(self):
        QPushButton.__init__(self, 'Del')
        self.setStyleSheet('''
            QPushButton {
                font-size: 10pt;
                background-color: #2e2e2e;
                color: #cccccc;
                max-width: 30px;
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

    @Slot()
    @Slot(str, str, int)
    def showWithText(self, name='', cmd='', buttonId=-1):
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
    delButtonPressed = Signal(int)
    editButtonPressed = Signal(str, str, int)

    def __init__(self, title, buttonId, command, parent=None):
        QWidget.__init__(self)
        self.layout = QHBoxLayout()
        self.actionButton = ActionButton(title)
        self.actionButton.pressed.connect(self.handleActionButton)
        self.editButton = EditButton()
        self.editButton.pressed.connect(self.sendEditInfo)
        self.delButton = DeleteButton()
        self.delButton.pressed.connect(self.handleDeleteButton)

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
        self.layout.addWidget(self.delButton)
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        return

    @Slot()
    def handleDeleteButton(self):
        self.delButtonPressed.emit(self.buttonId)

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
                min-width: 250px;
                max-width: 250px
            };
        ''')
        self.verticalScrollBar().setStyleSheet('''
            QScrollBar:vertical {
                background: #2e2e2e;
            };
        ''')

        self.editDialog = EditDialog()
        self.editDialog.buttonEditsSaved.connect(self.handleEditChanges)

        self.showButtons()
        self.buttons = []

        self.buttonPressed.connect(self.showButtons)
        return

    @Slot()
    def showButtons(self):
        self.content = TrayContent()
        layout = QVBoxLayout()
        result = self.db.runCommand('show-buttons')
        self.buttonRows = []
        contentHeight = 0
        buttonHeight = 50
        with io.StringIO(result) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                buttonName = row['name']
                buttonId = int(row['id'])
                buttonCmd = self.db.runCommand(f'get-button {buttonId}')

                buttonRow = ButtonRow(buttonName, buttonId, buttonCmd)
                buttonRow.dispatchAction.connect(self.handleActionButton)
                buttonRow.editButtonPressed.connect(
                        self.editDialog.showWithText)
                buttonRow.delButtonPressed.connect(self.handleDeleteButton)

                self.buttonRows.append(buttonRow)
                layout.addWidget(buttonRow)
                contentHeight += buttonHeight

        self.additionButton = QPushButton('New Button')
        self.additionButton.pressed.connect(self.handleAdditionButton)
        layout.addWidget(self.additionButton)
        contentHeight += buttonHeight

        self.content.setLayout(layout)
        self.content.setMinimumSize(220, contentHeight)
        self.content.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setWidget(self.content)
        return

    @Slot(int)
    def handleDeleteButton(self, buttonId):
        cmd = f'delete-button {buttonId}'
        self.db.runCommand(cmd)
        self.showButtons()
        return


    @Slot()
    def handleAdditionButton(self):
        self.editDialog.showWithText()
        return

    @Slot(int)
    def handleActionButton(self, buttonId):
        buttonCmd = self.db.runCommand(f'get-button {buttonId}')
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
        if buttonId != -1:
            command = f'rename-button {buttonId} "{name}" "{command}"'
        else:
            command = f'add-button "{name}" "{command}"'
        self.db.runCommand(command)
        self.showButtons()
        return

