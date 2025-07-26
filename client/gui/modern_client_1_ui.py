"""
Modern Client UI Interface (based on client_1.py)

Using rrd_widgets components to replace original Qt components, providing a more modern user interface
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QLabel, QTreeWidget, QTreeWidgetItem, QTextBrowser,
                               QStackedWidget, QTableWidget, QTableWidgetItem,
                               QFrame, QSplitter)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont, QColor, QPalette

from rrd_widgets import (SimpleButton_1, SimpleButton_2, SimpleButton_3, 
                         ExpandLineEdit, ComboBoxWidget, TipsWidget, TipsStatus)

class ModernMainWindow(QWidget):
    """Modern Main Window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modern Chat Client")
        self.resize(1000, 700)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI Layout"""
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right chat area
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter ratio
        splitter.setSizes([300, 700])
        
    def create_left_panel(self):
        """Create left panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Box)
        panel.setStyleSheet("QFrame { background-color: #f5f5f5; border-radius: 8px; }")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Chat List")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title_label.setStyleSheet("color: #333; padding: 5px;")
        layout.addWidget(title_label)
        
        # User/Group tree
        self.UserGroupTree = QTreeWidget()
        self.UserGroupTree.setHeaderHidden(True)
        self.UserGroupTree.setStyleSheet("""
            QTreeWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
            QTreeWidget::item {
                padding: 8px;
                border-radius: 3px;
                margin: 2px;
            }
            QTreeWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QTreeWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        layout.addWidget(self.UserGroupTree)
        
        # Button area
        button_layout = QHBoxLayout()
        
        # Connect button
        self.ClientConnectButton = SimpleButton_1()
        self.ClientConnectButton.setParams(
            text="Connect Server",
            border_radius=5,
            full_color=QColor(76, 175, 80),
            font_anim_start_color=QColor(76, 175, 80),
            font_anim_finish_color=QColor(255, 255, 255)
        )
        self.ClientConnectButton.setFont(QFont("Microsoft YaHei", 10))
        self.ClientConnectButton.setFixedHeight(35)
        button_layout.addWidget(self.ClientConnectButton)
        
        # Add user button
        self.ADDButton = SimpleButton_1()
        self.ADDButton.setParams(
            text="Add User",
            border_radius=5,
            full_color=QColor(33, 150, 243),
            font_anim_start_color=QColor(33, 150, 243),
            font_anim_finish_color=QColor(255, 255, 255)
        )
        self.ADDButton.setFont(QFont("Microsoft YaHei", 10))
        self.ADDButton.setFixedHeight(35)
        button_layout.addWidget(self.ADDButton)
        
        layout.addLayout(button_layout)
        
        # Group management button
        self.GroupButton = SimpleButton_1()
        self.GroupButton.setParams(
            text="Group Management",
            border_radius=5,
            full_color=QColor(255, 152, 0),
            font_anim_start_color=QColor(255, 152, 0),
            font_anim_finish_color=QColor(255, 255, 255)
        )
        self.GroupButton.setFont(QFont("Microsoft YaHei", 10))
        self.GroupButton.setFixedHeight(35)
        self.GroupButton.setEnabled(False)  # Default disabled
        layout.addWidget(self.GroupButton)
        
        # Reminder button
        self.ReminderButton = SimpleButton_1()
        self.ReminderButton.setParams(
            text="Set Reminder",
            border_radius=5,
            full_color=QColor(156, 39, 176),
            font_anim_start_color=QColor(156, 39, 176),
            font_anim_finish_color=QColor(255, 255, 255)
        )
        self.ReminderButton.setFont(QFont("Microsoft YaHei", 10))
        self.ReminderButton.setFixedHeight(35)
        layout.addWidget(self.ReminderButton)
        
        # Translation test button
        self.TestTrans = SimpleButton_1()
        self.TestTrans.setParams(
            text="Translation Test",
            border_radius=5,
            full_color=QColor(233, 30, 99),
            font_anim_start_color=QColor(233, 30, 99),
            font_anim_finish_color=QColor(255, 255, 255)
        )
        self.TestTrans.setFont(QFont("Microsoft YaHei", 10))
        self.TestTrans.setFixedHeight(35)
        layout.addWidget(self.TestTrans)
        
        return panel
        
    def create_right_panel(self):
        """Create right chat area"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Box)
        panel.setStyleSheet("QFrame { background-color: white; border-radius: 8px; }")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Chat title
        self.NameOfChat = QLabel("Please select a chat object")
        self.NameOfChat.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        self.NameOfChat.setStyleSheet("color: #333; padding: 10px; background-color: #f8f9fa; border-radius: 5px;")
        layout.addWidget(self.NameOfChat)
        
        # Chat window
        self.ChatMainWindow = QStackedWidget()
        self.ChatMainWindow.setStyleSheet("""
            QStackedWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.ChatMainWindow)
        
        # Translation and input area
        input_area_layout = QVBoxLayout()
        input_area_layout.setSpacing(5)
        
        # Translation and test button area
        translation_layout = QHBoxLayout()
        
        # Translation dropdown (modern ComboBox)
        self.TransComboBox = ComboBoxWidget()
        self.TransComboBox.setParams(
            border_radius=6,
            font_color=QColor(0, 0, 0),
            background_color=QColor(255, 255, 255)
        )
        self.TransComboBox.setItemParams(
            border_radius=4,
            item_spacing=2,
            item_height=25,
            color_font=QColor(0, 0, 0),
            color_hover=QColor(0, 129, 140, 35),
            color_border=QColor(0, 129, 140),
            color_background=QColor(255, 255, 255)
        )
        # Add translation options
        self.TransComboBox.addItems(["Original", "Deutsch", "English", "Chinese"])
        self.TransComboBox.setFixedWidth(100)
        translation_layout.addWidget(self.TransComboBox)
        
        # Test translation button
        self.TestTrans = SimpleButton_1()
        self.TestTrans.setParams(
            text="Test Translation",
            border_radius=5,
            full_color=QColor(108, 117, 125),
            font_anim_start_color=QColor(108, 117, 125),
            font_anim_finish_color=QColor(255, 255, 255)
        )
        self.TestTrans.setFont(QFont("Microsoft YaHei", 10))
        self.TestTrans.setFixedSize(120, 25)
        translation_layout.addWidget(self.TestTrans)
        
        translation_layout.addStretch()
        input_area_layout.addLayout(translation_layout)
        
        # Input area
        input_layout = QHBoxLayout()
        
        # Input box
        self.InputTextEdit = ExpandLineEdit()
        self.InputTextEdit.setParams(editer_height=35)
        self.InputTextEdit.setPlaceholderText("Enter message...")
        self.InputTextEdit.setStyleSheet("""
            ExpInput {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 5px;
                color: #333;
                padding: 5px;
            }
        """)
        self.InputTextEdit.setFont(QFont("Microsoft YaHei", 10))
        input_layout.addWidget(self.InputTextEdit)
        
        # Send button
        self.SendButton = SimpleButton_1()
        self.SendButton.setParams(
            text="Send",
            border_radius=5,
            full_color=QColor(76, 175, 80),
            font_anim_start_color=QColor(76, 175, 80),
            font_anim_finish_color=QColor(255, 255, 255)
        )
        self.SendButton.setFont(QFont("Microsoft YaHei", 10))
        self.SendButton.setFixedSize(80, 35)
        input_layout.addWidget(self.SendButton)
        
        input_area_layout.addLayout(input_layout)
        
        layout.addLayout(input_area_layout)
        
        return panel

class ModernConnectToServerDialog(QWidget):
    """Modern Connect to Server Dialog"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Connect to Server")
        self.resize(500, 400)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI Layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Connect to Server")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title_label.setStyleSheet("color: #333; text-align: center;")
        layout.addWidget(title_label)
        
        # Server table
        self.ServerTable = QTableWidget()
        self.ServerTable.setColumnCount(3)
        self.ServerTable.setHorizontalHeaderLabels(["Server ID", "Function", "Port"])
        self.ServerTable.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                gridline-color: #f0f0f0;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #ddd;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.ServerTable)
        
        # Hint information
        self.Hint = QLabel("Click 'Discover Servers' button to search for available servers")
        self.Hint.setStyleSheet("color: #666; padding: 10px; background-color: #f8f9fa; border-radius: 5px;")
        layout.addWidget(self.Hint)
        
        # Button area
        button_layout = QHBoxLayout()
        
        # UDP broadcast button
        self.udpButton = SimpleButton_1()
        self.udpButton.setParams(
            text="Discover Servers",
            border_radius=5,
            full_color=QColor(33, 150, 243),
            font_anim_start_color=QColor(33, 150, 243),
            font_anim_finish_color=QColor(255, 255, 255)
        )
        self.udpButton.setFont(QFont("Microsoft YaHei", 10))
        self.udpButton.setFixedHeight(35)
        button_layout.addWidget(self.udpButton)
        
        # Connect button
        self.Connect = SimpleButton_1()
        self.Connect.setParams(
            text="Connect",
            border_radius=5,
            full_color=QColor(76, 175, 80),
            font_anim_start_color=QColor(76, 175, 80),
            font_anim_finish_color=QColor(255, 255, 255)
        )
        self.Connect.setFont(QFont("Microsoft YaHei", 10))
        self.Connect.setFixedHeight(35)
        button_layout.addWidget(self.Connect)
        
        # Disconnect button
        self.Disconnect = SimpleButton_1()
        self.Disconnect.setParams(
            text="Disconnect",
            border_radius=5,
            full_color=QColor(244, 67, 54),
            font_anim_start_color=QColor(244, 67, 54),
            font_anim_finish_color=QColor(255, 255, 255)
        )
        self.Disconnect.setFont(QFont("Microsoft YaHei", 10))
        self.Disconnect.setFixedHeight(35)
        button_layout.addWidget(self.Disconnect)
        
        layout.addLayout(button_layout)

class ModernAddDialog(QWidget):
    """Modern Add User/Group Dialog"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add User/Group")
        self.resize(400, 300)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI Layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Add User/Group")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title_label.setStyleSheet("color: #333; text-align: center;")
        layout.addWidget(title_label)
        
        # Type selection
        type_layout = QHBoxLayout()
        type_label = QLabel("Type:")
        type_label.setFont(QFont("Microsoft YaHei", 10))
        type_layout.addWidget(type_label)
        
        self.UserGroup = ComboBoxWidget()
        self.UserGroup.addItems(["User", "Group"])
        self.UserGroup.setParams(
            border_radius=5,
            font_color=QColor(51, 51, 51),
            background_color=QColor(255, 255, 255)
        )
        self.UserGroup.setItemParams(
            color_font=QColor(51, 51, 51),
            border_radius=5,
            color_hover=QColor(0, 0, 0, 35),
            color_background=QColor(255, 255, 255),
            color_border=QColor(33, 150, 243)
        )
        self.UserGroup.setFont(QFont("Microsoft YaHei", 10))
        self.UserGroup.setFixedHeight(35)
        type_layout.addWidget(self.UserGroup)
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        # User ID input
        id_layout = QHBoxLayout()
        id_label = QLabel("User ID:")
        id_label.setFont(QFont("Microsoft YaHei", 10))
        id_layout.addWidget(id_label)
        
        self.printId = ExpandLineEdit()
        self.printId.setParams(editer_height=35)
        self.printId.setPlaceholderText("Enter user ID")
        self.printId.setStyleSheet("""
            ExpInput {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 5px;
                color: #333;
                padding: 5px;
            }
        """)
        self.printId.setFont(QFont("Microsoft YaHei", 10))
        id_layout.addWidget(self.printId)
        layout.addLayout(id_layout)
        
        # Hint information
        self.Hint1 = QLabel("")
        self.Hint1.setStyleSheet("color: #666; padding: 10px; background-color: #f8f9fa; border-radius: 5px; min-height: 60px;")
        self.Hint1.setWordWrap(True)
        layout.addWidget(self.Hint1)
        
        # Button area
        button_layout = QHBoxLayout()
        
        # Add button
        self.AddButton1 = SimpleButton_1()
        self.AddButton1.setParams(
            text="Add User",
            border_radius=5,
            full_color=QColor(76, 175, 80),
            font_anim_start_color=QColor(76, 175, 80),
            font_anim_finish_color=QColor(255, 255, 255)
        )
        self.AddButton1.setFont(QFont("Microsoft YaHei", 10))
        self.AddButton1.setFixedHeight(35)
        button_layout.addWidget(self.AddButton1)
        
        # Create group button
        self.createButton1 = SimpleButton_1()
        self.createButton1.setParams(
            text="Create Group",
            border_radius=5,
            full_color=QColor(255, 152, 0),
            font_anim_start_color=QColor(255, 152, 0),
            font_anim_finish_color=QColor(255, 255, 255)
        )
        self.createButton1.setFont(QFont("Microsoft YaHei", 10))
        self.createButton1.setFixedHeight(35)
        self.createButton1.setEnabled(False)  # Default disabled
        button_layout.addWidget(self.createButton1)
        
        layout.addLayout(button_layout)

class ModernModifyGroupDialog(QWidget):
    """Modern Group Management Dialog"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Group Management")
        self.resize(400, 250)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI Layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Group Management")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title_label.setStyleSheet("color: #333; text-align: center;")
        layout.addWidget(title_label)
        
        # Group name
        group_layout = QHBoxLayout()
        group_label = QLabel("Group Name:")
        group_label.setFont(QFont("Microsoft YaHei", 10))
        group_layout.addWidget(group_label)
        
        self.GroupName = QLabel("")
        self.GroupName.setStyleSheet("color: #333; padding: 8px; background-color: #f8f9fa; border-radius: 5px;")
        self.GroupName.setFont(QFont("Microsoft YaHei", 10))
        group_layout.addWidget(self.GroupName)
        group_layout.addStretch()
        layout.addLayout(group_layout)
        
        # Button area
        button_layout = QHBoxLayout()
        
        # Leave group button
        self.LeaveButton = SimpleButton_1()
        self.LeaveButton.setParams(
            text="Leave Group",
            border_radius=5,
            full_color=QColor(244, 67, 54),
            font_anim_start_color=QColor(244, 67, 54),
            font_anim_finish_color=QColor(255, 255, 255)
        )
        self.LeaveButton.setFont(QFont("Microsoft YaHei", 10))
        self.LeaveButton.setFixedHeight(35)
        button_layout.addWidget(self.LeaveButton)
        
        # Invite user button
        self.InviteButton = SimpleButton_1()
        self.InviteButton.setParams(
            text="Invite User",
            border_radius=5,
            full_color=QColor(33, 150, 243),
            font_anim_start_color=QColor(33, 150, 243),
            font_anim_finish_color=QColor(255, 255, 255)
        )
        self.InviteButton.setFont(QFont("Microsoft YaHei", 10))
        self.InviteButton.setFixedHeight(35)
        button_layout.addWidget(self.InviteButton)
        
        layout.addLayout(button_layout)

class ModernInvitePopUpDialog(QWidget):
    """Modern Group Invitation Dialog"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Group Invitation")
        self.resize(400, 200)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI Layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Invitation text
        self.InviteText = QLabel("You are invited to join a group, do you accept?")
        self.InviteText.setFont(QFont("Microsoft YaHei", 12))
        self.InviteText.setStyleSheet("color: #333; padding: 20px; background-color: #f8f9fa; border-radius: 5px; text-align: center;")
        self.InviteText.setWordWrap(True)
        layout.addWidget(self.InviteText)
        
        # Button area
        button_layout = QHBoxLayout()
        
        # Accept button
        self.YesButton = SimpleButton_1()
        self.YesButton.setParams(
            text="Accept",
            border_radius=5,
            full_color=QColor(76, 175, 80),
            font_anim_start_color=QColor(76, 175, 80),
            font_anim_finish_color=QColor(255, 255, 255)
        )
        self.YesButton.setFont(QFont("Microsoft YaHei", 10))
        self.YesButton.setFixedHeight(35)
        button_layout.addWidget(self.YesButton)
        
        # Reject button
        self.NoButton = SimpleButton_1()
        self.NoButton.setParams(
            text="Reject",
            border_radius=5,
            full_color=QColor(244, 67, 54),
            font_anim_start_color=QColor(244, 67, 54),
            font_anim_finish_color=QColor(255, 255, 255)
        )
        self.NoButton.setFont(QFont("Microsoft YaHei", 10))
        self.NoButton.setFixedHeight(35)
        button_layout.addWidget(self.NoButton)
        
        layout.addLayout(button_layout)

class ModernReminderDialog(QWidget):
    """Modern Reminder Setting Dialog"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Set Reminder")
        self.resize(400, 250)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI Layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Set Reminder")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title_label.setStyleSheet("color: #333; text-align: center;")
        layout.addWidget(title_label)
        
        # Event name
        event_layout = QHBoxLayout()
        event_label = QLabel("Event Name:")
        event_label.setFont(QFont("Microsoft YaHei", 10))
        event_layout.addWidget(event_label)
        
        self.Eventname = ExpandLineEdit()
        self.Eventname.setParams(editer_height=35)
        self.Eventname.setPlaceholderText("Enter reminder event name")
        self.Eventname.setStyleSheet("""
            ExpInput {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 5px;
                color: #333;
                padding: 5px;
            }
        """)
        self.Eventname.setFont(QFont("Microsoft YaHei", 10))
        event_layout.addWidget(self.Eventname)
        layout.addLayout(event_layout)
        
        # Time setting
        time_layout = QHBoxLayout()
        time_label = QLabel("Countdown (seconds):")
        time_label.setFont(QFont("Microsoft YaHei", 10))
        time_layout.addWidget(time_label)
        
        self.Time = ExpandLineEdit()
        self.Time.setParams(editer_height=35)
        self.Time.setPlaceholderText("Enter countdown seconds")
        self.Time.setStyleSheet("""
            ExpInput {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 5px;
                color: #333;
                padding: 5px;
            }
        """)
        self.Time.setFont(QFont("Microsoft YaHei", 10))
        time_layout.addWidget(self.Time)
        layout.addLayout(time_layout)
        
        # Set button
        self.setButton = SimpleButton_1()
        self.setButton.setParams(
            text="Set Reminder",
            border_radius=5,
            full_color=QColor(156, 39, 176),
            font_anim_start_color=QColor(156, 39, 176),
            font_anim_finish_color=QColor(255, 255, 255)
        )
        self.setButton.setFont(QFont("Microsoft YaHei", 10))
        self.setButton.setFixedHeight(35)
        layout.addWidget(self.setButton) 