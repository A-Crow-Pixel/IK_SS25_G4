"""
Modern Client Dialogs
Using rrd_widgets components to implement modern appearance
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                               QPlainTextEdit, QLabel, QFrame, QTableWidgetItem,
                               QLineEdit, QTextEdit, QListWidget, QSpacerItem, QSizePolicy, QComboBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont

# Import rrd_widgets modern components
from rrd_widgets import (SimpleButton_1, SimpleButton_2, SimpleLineEdit_1, 
                         ComboBoxWidget, TipsWidget, TipsStatus)


class ModernConnectToServerDialog(QDialog):
    """Modern Connect to Server Dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi()
        self.setModernStyle()
    
    def setupUi(self):
        """Setup UI Layout"""
        self.setObjectName("Dialog")
        self.resize(350, 520)
        self.setWindowTitle("Connect to Server")
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Title area
        title_label = QLabel("Server Connection")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 0px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # UDP broadcast button area
        udp_layout = QHBoxLayout()
        udp_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        self.udpButton = SimpleButton_1()
        self.udpButton.setParams(
            text="Send UDP Broadcast",
            full_color=QColor(0, 129, 140),
            font_anim_start_color=QColor(0, 129, 140),
            font_anim_finish_color=QColor(255, 255, 255),
            border_radius=8
        )
        self.udpButton.setFixedHeight(35)
        udp_layout.addWidget(self.udpButton)
        
        main_layout.addLayout(udp_layout)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("QFrame { color: rgba(100, 100, 100, 100); margin: 5px 0px; }")
        main_layout.addWidget(separator)
        
        # Server list
        self.ServerTable = QTableWidget()
        self.ServerTable.setColumnCount(3)
        self.ServerTable.setHorizontalHeaderLabels(["Server ID", "Function", "Port"])
        self.ServerTable.setStyleSheet("""
            QTableWidget {
                background-color: rgba(255, 255, 255, 245);
                border: 2px solid rgba(200, 200, 200, 100);
                border-radius: 8px;
                gridline-color: rgba(200, 200, 200, 100);
                selection-background-color: rgba(0, 129, 140, 100);
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: rgba(0, 129, 140, 150);
                color: white;
            }
            QHeaderView::section {
                background-color: rgba(52, 73, 94, 20);
                color: #2c3e50;
                font-weight: bold;
                padding: 8px;
                border: 1px solid rgba(200, 200, 200, 100);
                border-radius: 4px;
            }
        """)
        main_layout.addWidget(self.ServerTable)
        
        # Hint information area
        hint_label = QLabel("Connection Information")
        hint_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #34495e;
                padding: 5px 0px;
            }
        """)
        main_layout.addWidget(hint_label)
        
        self.Hint = QPlainTextEdit()
        self.Hint.setMaximumHeight(80)
        self.Hint.setPlaceholderText("Connection status and hint information will be displayed here...")
        self.Hint.setStyleSheet("""
            QPlainTextEdit {
                background-color: rgba(248, 249, 250, 255);
                border: 2px solid rgba(200, 200, 200, 100);
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """)
        main_layout.addWidget(self.Hint)
        
        # Control button area
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.Connect = SimpleButton_1()
        self.Connect.setParams(
            text="Connect",
            full_color=QColor(34, 139, 34),
            font_anim_start_color=QColor(34, 139, 34),
            font_anim_finish_color=QColor(255, 255, 255),
            border_radius=8
        )
        self.Connect.setFixedHeight(40)
        
        self.Disconnect = SimpleButton_1()
        self.Disconnect.setParams(
            text="Disconnect",
            full_color=QColor(220, 53, 69),
            font_anim_start_color=QColor(220, 53, 69),
            font_anim_finish_color=QColor(255, 255, 255),
            border_radius=8
        )
        self.Disconnect.setFixedHeight(40)
        
        button_layout.addWidget(self.Connect, 1)
        button_layout.addWidget(self.Disconnect, 1)
        main_layout.addLayout(button_layout)
    
    def setModernStyle(self):
        """Set modern style"""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }
            QWidget {
                font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
            }
        """)


class ModernAddDialog(QDialog):
    """Modern Add User Dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi()
        self.setModernStyle()
    
    def setupUi(self):
        """Setup UI Layout"""
        self.setObjectName("AddDialog")
        self.resize(400, 300)
        self.setWindowTitle("Add User")
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Add New User")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 0px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # User/Group selection
        select_layout = QHBoxLayout()
        select_label = QLabel("Type:")
        select_label.setStyleSheet("font-weight: bold; color: #34495e;")
        
        self.UserGroup = QComboBox()
        self.UserGroup.addItems(["User", "Group"])
        self.UserGroup.setFixedWidth(120)

        # User ID / Group name input box
        self.printId = QLineEdit()
        self.printId.setPlaceholderText("Please enter user ID or group name")
        self.printId.setStyleSheet("""
                    QLineEdit {
                        background-color: white;
                        border: 2px solid rgba(200, 200, 200, 100);
                        border-radius: 6px;
                        padding: 8px 12px;
                        font-size: 14px;
                    }
                    QLineEdit:focus {
                        border: 2px solid rgba(0, 129, 140, 200);
                    }
                """)
        main_layout.addWidget(self.printId)

        select_layout.addWidget(select_label)
        select_layout.addWidget(self.UserGroup)
        select_layout.addStretch()
        main_layout.addLayout(select_layout)

        # Hint information area
        self.Hint1 = QPlainTextEdit()
        self.Hint1.setMaximumHeight(80)
        self.Hint1.setPlaceholderText("Operation hint information...")
        self.Hint1.setStyleSheet("""
            QPlainTextEdit {
                background-color: rgba(248, 249, 250, 255);
                border: 2px solid rgba(200, 200, 200, 100);
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }
        """)
        main_layout.addWidget(self.Hint1)
        
        # Button area
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Add user button
        self.AddButton1 = SimpleButton_1()
        self.AddButton1.setParams(
            text="Add User",
            full_color=QColor(0, 129, 140),
            font_anim_start_color=QColor(0, 129, 140),
            font_anim_finish_color=QColor(255, 255, 255),
            border_radius=8
        )
        self.AddButton1.setFixedHeight(40)
        
        # Create group button
        self.createButton1 = SimpleButton_1()
        self.createButton1.setParams(
            text="Create Group",
            full_color=QColor(76, 175, 80),
            font_anim_start_color=QColor(76, 175, 80),
            font_anim_finish_color=QColor(255, 255, 255),
            border_radius=8
        )
        self.createButton1.setFixedHeight(40)
        
        # Cancel button
        cancel_button = SimpleButton_2()
        cancel_button.setParams(
            text="Cancel",
            full_color=QColor(108, 117, 125),
            font_anim_start_color=QColor(108, 117, 125),
            font_anim_finish_color=QColor(255, 255, 255),
            border_radius=8
        )
        cancel_button.setFixedHeight(40)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.AddButton1, 1)
        button_layout.addWidget(self.createButton1, 1)
        button_layout.addWidget(cancel_button, 1)
        main_layout.addLayout(button_layout)
    
    def currentText(self):
        """Compatibility method - return currently selected user/group type"""
        return self.UserGroup.curr_text()
    
    def setModernStyle(self):
        """Set modern style"""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }
            QWidget {
                font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
            }
        """)


class ModernModifyGroupDialog(QDialog):
    """Modern Modify Group Dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi()
        self.setModernStyle()
    
    def setupUi(self):
        """Setup UI Layout"""
        self.setObjectName("ModifyGroupDialog")
        self.resize(450, 400)
        self.setWindowTitle("Group Management")
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Group Management")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 0px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Operation button area
        operation_layout = QHBoxLayout()
        operation_layout.setSpacing(10)
        
        self.LeaveButton = SimpleButton_1()
        self.LeaveButton.setParams(
            text="Leave Group",
            full_color=QColor(220, 53, 69),
            font_anim_start_color=QColor(220, 53, 69),
            font_anim_finish_color=QColor(255, 255, 255),
            border_radius=8
        )
        self.LeaveButton.setFixedHeight(40)
        
        self.InviteButton = SimpleButton_1()
        self.InviteButton.setParams(
            text="Invite Member",
            full_color=QColor(0, 129, 140),
            font_anim_start_color=QColor(0, 129, 140),
            font_anim_finish_color=QColor(255, 255, 255),
            border_radius=8
        )
        self.InviteButton.setFixedHeight(40)
        
        operation_layout.addWidget(self.LeaveButton, 1)
        operation_layout.addWidget(self.InviteButton, 1)
        main_layout.addLayout(operation_layout)
        
        # Group name input
        name_layout = QHBoxLayout()
        name_label = QLabel("Group Name:")
        name_label.setStyleSheet("font-weight: bold; color: #34495e;")
        
        self.GroupName = QLineEdit()
        self.GroupName.setPlaceholderText("Enter group name...")
        self.GroupName.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid rgba(200, 200, 200, 100);
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid rgba(0, 129, 140, 200);
            }
        """)
        
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.GroupName)
        main_layout.addLayout(name_layout)
        
        # Group information area
        info_label = QLabel("Group Operations and Management")
        info_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #7f8c8d;
                padding: 20px;
                background-color: rgba(200, 200, 200, 50);
                border-radius: 8px;
                border: 2px dashed rgba(200, 200, 200, 100);
            }
        """)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(info_label)

        # Invited user ID input box
        invite_layout = QHBoxLayout()
        invite_label = QLabel("Invite User ID:")
        invite_label.setStyleSheet("font-weight: bold; color: #34495e;")
        invite_layout.addWidget(invite_label)

        # QLineEdit for inputting invited user ID
        self.lineEdit = QLineEdit()
        self.lineEdit.setPlaceholderText("Please enter user ID")
        self.lineEdit.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid rgba(200, 200, 200, 100);
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid rgba(0, 129, 140, 200);
            }
        """)
        invite_layout.addWidget(self.lineEdit)
        main_layout.addLayout(invite_layout)

        # Close button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        
        close_button = SimpleButton_2()
        close_button.setParams(
            text="Close",
            full_color=QColor(108, 117, 125),
            font_anim_start_color=QColor(108, 117, 125),
            font_anim_finish_color=QColor(255, 255, 255),
            border_radius=8
        )
        close_button.setFixedHeight(40)
        close_button.setFixedWidth(100)
        close_button.clicked.connect(self.accept)
        
        close_layout.addWidget(close_button)
        main_layout.addLayout(close_layout)
    
    def setModernStyle(self):
        """Set modern style"""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }
            QWidget {
                font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
            }
        """)


class ModernInvitePopUpDialog(QDialog):
    """Modern Invitation Popup Dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi()
        self.setModernStyle()
    
    def setupUi(self):
        """Setup UI Layout"""
        self.setObjectName("InvitePopUpDialog")
        self.resize(350, 250)
        self.setWindowTitle("Group Invitation")
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Group Invitation")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 0px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Invitation information area
        self.InviteText = QLabel("You have received a group invitation")
        self.InviteText.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #34495e;
                padding: 15px;
                background-color: rgba(0, 129, 140, 20);
                border-radius: 8px;
                border-left: 4px solid rgba(0, 129, 140, 200);
            }
        """)
        self.InviteText.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.InviteText)
        
        # Button area
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        self.NoButton = SimpleButton_1()
        self.NoButton.setParams(
            text="Reject",
            full_color=QColor(220, 53, 69),
            font_anim_start_color=QColor(220, 53, 69),
            font_anim_finish_color=QColor(255, 255, 255),
            border_radius=8
        )
        self.NoButton.setFixedHeight(45)
        self.NoButton.clicked.connect(self.reject)

        self.YesButton = SimpleButton_1()
        self.YesButton.setParams(
            text="Accept",
            full_color=QColor(34, 139, 34),
            font_anim_start_color=QColor(34, 139, 34),
            font_anim_finish_color=QColor(255, 255, 255),
            border_radius=8
        )
        self.YesButton.setFixedHeight(45)
        self.YesButton.clicked.connect(self.accept)

        button_layout.addWidget(self.NoButton, 1)
        button_layout.addWidget(self.YesButton, 1)

        main_layout.addLayout(button_layout)
        
        # Add elastic space
        main_layout.addStretch()
    
    def setModernStyle(self):
        """Set modern style"""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }
            QWidget {
                font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
            }
        """) 