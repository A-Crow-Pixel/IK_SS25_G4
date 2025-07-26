"""
Modern Client Main Interface UI
Using rrd_widgets components to implement modern appearance
Reference client.py layout design
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                               QTreeWidget, QTextBrowser, QPlainTextEdit, QLabel,
                               QFrame, QSizePolicy, QTreeWidgetItem, QComboBox, QStackedWidget)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont

# Import rrd_widgets modern components
from rrd_widgets import (SimpleButton_1, SimpleButton_2, SimpleButton_3, SimpleButton_4, SimpleButton_5, SimpleButton_6, SimpleLineEdit_1,
                         ComboBoxWidget, TipsWidget, TipsStatus, ExpandLineEdit)


class ModernMainWindow(QMainWindow):
    """Modern Client Main Interface"""
    
    def __init__(self):
        super().__init__()
        self.setupUi()
        self.setModernStyle()
    
    def setupUi(self):
        """Setup UI layout and components"""
        self.setObjectName("Chat")
        self.resize(810, 595)
        self.setWindowTitle("Chat")
        
        # Central widget
        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)
        
        # Main layout
        main_layout = QHBoxLayout(self.centralwidget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Left panel
        self.setupLeftPanel(main_layout)
        
        # Right chat area
        self.setupChatArea(main_layout)
        
        # Create status bar
        self.statusbar = self.statusBar()
    
    def setupLeftPanel(self, main_layout):
        """Setup left panel - reference client.py layout"""
        # Left panel container
        left_panel = QWidget()
        left_panel.setFixedWidth(200)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(8)
        
        # Top button area - reference client.py layout
        top_buttons_layout = QVBoxLayout()
        top_buttons_layout.setSpacing(5)
        
        # First row: connect server and reminder buttons
        row1_layout = QHBoxLayout()
        
        # Connect server button 🔗
        self.ClientConnectButton = SimpleButton_2()
        self.ClientConnectButton.setParams(
            text="🔗 Server",
            full_color=QColor(0, 150, 243),
            font_anim_start_color=QColor(0, 150, 243),
            font_anim_finish_color=QColor(255, 255, 255),
            border_radius=15
        )
        self.ClientConnectButton.setFixedHeight(30)
        
        # Reminder button ⏰
        self.ReminderButton = SimpleButton_2()
        self.ReminderButton.setParams(
            text="⏰ Reminder",
            full_color=QColor(148, 59, 142),
            font_anim_start_color=QColor(148, 59, 142),
            font_anim_finish_color=QColor(255, 255, 255),
            border_radius=15
        )
        self.ReminderButton.setFixedHeight(30)
        
        row1_layout.addWidget(self.ClientConnectButton)
        row1_layout.addWidget(self.ReminderButton)
        top_buttons_layout.addLayout(row1_layout)
        
        # Second row: add friend and group buttons
        row2_layout = QHBoxLayout()
        
        # Add user button 👤
        self.ADDButton = SimpleButton_2()
        self.ADDButton.setParams(
            text="👤 Add Friend",
            full_color=QColor(76, 175, 80),
            font_anim_start_color=QColor(76, 175, 80),
            font_anim_finish_color=QColor(255, 255, 255),
            border_radius=15
        )
        self.ADDButton.setFixedHeight(30)
        
        # Group button 👥
        self.GroupButton = SimpleButton_2()
        self.GroupButton.setParams(
            text="👥 Group",
            full_color=QColor(255, 204, 0),
            font_anim_start_color=QColor(255, 204, 0),
            font_anim_finish_color=QColor(255, 255, 255),
            border_radius=15
        )
        self.GroupButton.setFixedHeight(30)
        self.GroupButton.setEnabled(False)  # Default disabled
        
        row2_layout.addWidget(self.ADDButton)
        row2_layout.addWidget(self.GroupButton)
        top_buttons_layout.addLayout(row2_layout)
        
        left_layout.addLayout(top_buttons_layout)

        title_label = QLabel("Chat List")
        title_label.setFont(QFont("Microsoft YaHei", 15, QFont.Bold))
        title_label.setStyleSheet("color: #333; padding: 5px;")
        title_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(title_label)
        
        # Separator line
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setStyleSheet("QFrame { color: rgba(100, 100, 100, 50); }")
        left_layout.addWidget(separator1)
        
        # User and group tree
        self.UserGroupTree = QTreeWidget()
        self.UserGroupTree.setHeaderHidden(True)
        self.UserGroupTree.setStyleSheet("""
            QTreeWidget {
                background-color: rgba(255, 255, 255, 245);
                border: 1px solid rgba(200, 200, 200, 100);
                border-radius: 8px;
                padding: 5px;
                outline: none;
            }
            QTreeWidget::item {
                padding: 5px;
                margin: 2px 0px;
                border-radius: 4px;
            }
            QTreeWidget::item:selected {
                background-color: rgba(0, 129, 140, 150);
                color: white;
            }
            QTreeWidget::item:hover {
                background-color: rgba(0, 129, 140, 50);
            }
        """)
        left_layout.addWidget(self.UserGroupTree)
        
        main_layout.addWidget(left_panel)
    
    def setupChatArea(self, main_layout):
        """Setup right chat area"""
        # Right chat area container
        chat_area = QWidget()
        chat_layout = QVBoxLayout(chat_area)
        chat_layout.setContentsMargins(5, 5, 5, 5)
        chat_layout.setSpacing(8)
        
        # Chat header area
        header_layout = QHBoxLayout()
        
        # Chat title
        self.NameOfChat = QLabel("Select Chat")
        self.NameOfChat.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding: 5px 10px;
            }
        """)
        header_layout.addWidget(self.NameOfChat)
        header_layout.addStretch()

        chat_layout.addLayout(header_layout)
        
        # Separator line
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet("QFrame { color: rgba(100, 100, 100, 50); }")
        chat_layout.addWidget(separator2)
        
        # Chat history area
        self.ChatMainWindow = QStackedWidget()
        placeholder = QTextBrowser()
        placeholder.setPlainText("Please select a chat")
        placeholder.setReadOnly(True)
        self.ChatMainWindow.addWidget(placeholder)
        self.ChatMainWindow.setStyleSheet("""
            QTextBrowser {
                background-color: rgba(248, 249, 250, 255);
                border: 1px solid rgba(200, 200, 200, 100);
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                line-height: 1.4;
            }
        """)
        chat_layout.addWidget(self.ChatMainWindow)
        
        # Translation and input area
        input_area_layout = QVBoxLayout()
        input_area_layout.setSpacing(5)
        
        # Translation selection area
        translation_layout = QHBoxLayout()
        
        # Translation label
        trans_label = QLabel("🌐 Translation:")
        trans_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 12px;
                padding: 5px;
            }
        """)
        translation_layout.addWidget(trans_label)
        
        # Translation dropdown (modern ComboBox)
        self.TransComboBox = QComboBox()
        self.TransComboBox.addItems(["Original", "Deutsch", "English", "Chinese", "Türkçe"])
        self.TransComboBox.setFixedWidth(120)

        translation_layout.addWidget(self.TransComboBox)

        # Test translation button
        self.TestTrans = SimpleButton_2()
        self.TestTrans.setParams(
            text="🧪 Test Translation",
            full_color=QColor(108, 117, 125),
            font_anim_start_color=QColor(108, 117, 125),
            font_anim_finish_color=QColor(255, 255, 255),
            border_radius=6
        )
        self.TestTrans.setFixedSize(120, 25)
        translation_layout.addWidget(self.TestTrans)
        translation_layout.addStretch()
        input_area_layout.addLayout(translation_layout)
        
        # Input area
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        # Input box container
        input_container = QWidget()
        input_container_layout = QVBoxLayout(input_container)
        input_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Use modern ExpandLineEdit input box
        self.InputTextEdit = ExpandLineEdit()
        self.InputTextEdit.setPlaceholderText("")
        self.InputTextEdit.setMinimumHeight(42)
        self.InputTextEdit.setParams(editer_height=35)
        self.InputTextEdit.setStyleSheet("""
            ExpInput {
                background-color: white;
                border: 2px solid rgba(200, 200, 200, 100);
                border-radius: 10px;
                color: rgb(0, 0, 0);
                padding: 8px 12px;
                font-size: 14px;
            }
        """)
        font = QFont()
        font.setPointSize(12)
        self.InputTextEdit.setFontToEditer(font)
        self.InputTextEdit.setFontToPlaceholder(font)
        input_container_layout.addWidget(self.InputTextEdit)
        input_layout.addWidget(input_container)
        
        # Send button
        self.SendButton = SimpleButton_1()
        self.SendButton.setParams(
            text="📤 Send",
            full_color=QColor(0, 129, 140),
            font_anim_start_color=QColor(0, 129, 140),
            font_anim_finish_color=QColor(255, 255, 255),
            border_radius=15
        )
        self.SendButton.setFixedSize(80, 40)
        input_layout.addWidget(self.SendButton)
        
        input_area_layout.addLayout(input_layout)
        chat_layout.addLayout(input_area_layout)
        
        main_layout.addWidget(chat_area)
    
    def setModernStyle(self):
        """Set modern overall style"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }
            QWidget {
                font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
            }
        """)
    
    def currentText(self):
        """ComboBox compatibility method"""
        return self.TransComboBox.curr_text()
    
    def setCurrentText(self, text):
        """ComboBox compatibility method"""
        self.TransComboBox.setCurrentText(text)
    
    # ExpandLineEdit compatibility methods
    def toPlainText(self):
        """Get input box text content"""
        return self.InputTextEdit.text()
    
    def clear(self):
        """Clear input box"""
        self.InputTextEdit.editer.clear() 