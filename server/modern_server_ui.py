"""
Modern server UI interface
Using rrd_widgets components to implement modern appearance
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                               QTextEdit, QListWidget, QLabel, QFrame)
from PySide6.QtCore import Signal, QObject, Qt
from PySide6.QtGui import QColor, QFont, QTextCursor

# Import rrd_widgets modern components
from rrd_widgets import (SimpleButton_1, SimpleButton_2, SimpleButton_3,
                         TipsWidget, TipsStatus, CardBoxDeletable)


# Global signals for cross-thread log printing
class MySignals(QObject):
    """
    Global signal class for cross-thread communication
    
    Attributes:
        log_signal (Signal): Log signal for displaying logs in UI thread
        refresh_list_signal (Signal): Refresh list signal for updating client list
        message_log_signal (Signal): Message log signal specifically for message log recording
    """
    log_signal = Signal(str)
    refresh_list_signal = Signal()
    message_log_signal = Signal(str)  # New: specifically for message log recording

global_ms = MySignals()


class ModernServerUI(QMainWindow):
    """Modern server main interface"""
    
    def __init__(self):
        super().__init__()
        self.setupUi()
        self.setModernStyle()
    
    def setupUi(self):
        """Setup UI layout and components"""
        self.setObjectName("Server")
        self.resize(620, 580)
        self.setWindowTitle("Chat Server")
        
        # Central widget
        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)
        
        # Main layout
        main_layout = QVBoxLayout(self.centralwidget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Header area
        self.setupHeaderArea(main_layout)
        
        # Control button area
        self.setupControlButtons(main_layout)
        
        # Content area
        self.setupContentArea(main_layout)
        
        # Create status bar
        self.statusbar = self.statusBar()
        self.statusbar.showMessage("Server ready")
    
    def setupHeaderArea(self, main_layout):
        """Setup header area"""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main title
        title_label = QLabel("Chat Server Console")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 0px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Manage and monitor server status")
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #7f8c8d;
                padding-bottom: 10px;
            }
        """)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle_label)
        
        main_layout.addWidget(header_widget)
    
    def setupControlButtons(self, main_layout):
        """Setup control button area"""
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(10, 5, 10, 5)
        button_layout.setSpacing(15)
        
        # Start server button
        self.StartButton = SimpleButton_1()
        self.StartButton.setParams(
            text="Start Server",
            full_color=QColor(34, 139, 34),
            font_anim_start_color=QColor(34, 139, 34),
            font_anim_finish_color=QColor(255, 255, 255),
            border_radius=8
        )
        self.StartButton.setFixedHeight(45)
        
        # Stop server button
        self.StopButton = SimpleButton_2()
        self.StopButton.setParams(
            text="Stop Server",
            full_color=QColor(220, 53, 69),
            font_anim_start_color=QColor(220, 53, 69),
            font_anim_finish_color=QColor(255, 255, 255),
            border_radius=8
        )
        self.StopButton.setFixedHeight(45)
        
        # Discover server button
        self.DiscoverServerButton = SimpleButton_3()
        self.DiscoverServerButton.setParams(
            text="Discover Servers",
            full_color=QColor(255, 150, 0),
            font_anim_start_color=QColor(255, 150, 0),
            font_anim_finish_color=QColor(255, 255, 255),
            border_radius=8
        )
        self.DiscoverServerButton.setFixedHeight(45)
        
        # Add buttons to layout
        button_layout.addWidget(self.StartButton, 1)
        button_layout.addWidget(self.StopButton, 1)
        button_layout.addWidget(self.DiscoverServerButton, 1)
        
        main_layout.addWidget(button_widget)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("QFrame { color: rgba(100, 100, 100, 100); margin: 5px 0px; }")
        main_layout.addWidget(separator)
    
    def setupContentArea(self, main_layout):
        """Setup content area"""
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(15)
        
        # Left chat history area
        self.setupChatHistory(content_layout)
        
        # Right client list area
        self.setupClientList(content_layout)
        
        main_layout.addWidget(content_widget)
    
    def setupChatHistory(self, content_layout):
        """Setup chat history area"""
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(5, 5, 5, 5)
        chat_layout.setSpacing(8)
        
        # Chat history label
        chat_label = QLabel("Server Logs")
        chat_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #34495e;
                padding: 5px 10px;
                background-color: rgba(52, 73, 94, 10);
                border-radius: 6px;
            }
        """)
        chat_layout.addWidget(chat_label)
        chat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Chat history text area
        self.ChatHistory = QTextEdit()
        self.ChatHistory.setReadOnly(True)
        self.ChatHistory.setStyleSheet("""
            QTextEdit {
                background-color: rgba(248, 249, 250, 255);
                border: 2px solid rgba(200, 200, 200, 100);
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                font-family: 'Consolas', 'Monaco', monospace;
                line-height: 1.4;
            }
            QScrollBar:vertical {
                background-color: rgba(230, 230, 230, 100);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(0, 129, 140, 150);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(0, 129, 140, 200);
            }
        """)
        chat_layout.addWidget(self.ChatHistory)
        
        content_layout.addWidget(chat_container, 2)
    
    def setupClientList(self, content_layout):
        """Setup client list area"""
        client_container = QWidget()
        client_layout = QVBoxLayout(client_container)
        client_layout.setContentsMargins(5, 5, 5, 5)
        client_layout.setSpacing(8)
        
        # Client list label
        client_label = QLabel("Clients & Servers")
        client_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #34495e;
                padding: 5px 10px;
                background-color: rgba(52, 73, 94, 10);
                border-radius: 6px;
            }
        """)
        client_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        client_layout.addWidget(client_label)
        
        # Client list
        self.ClientServerList = QListWidget()
        self.ClientServerList.setStyleSheet("""
            QListWidget {
                background-color: rgba(255, 255, 255, 245);
                border: 2px solid rgba(200, 200, 200, 100);
                border-radius: 8px;
                padding: 5px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 12px;
                margin: 2px 0px;
                border-radius: 4px;
                font-size: 13px;
            }
            QListWidget::item:selected {
                background-color: rgba(0, 129, 140, 150);
                color: white;
            }
            QListWidget::item:hover {
                background-color: rgba(0, 129, 140, 50);
            }
            QScrollBar:vertical {
                background-color: rgba(230, 230, 230, 100);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(0, 129, 140, 150);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(0, 129, 140, 200);
            }
        """)
        client_layout.addWidget(self.ClientServerList)
        
        client_container.setFixedWidth(250)
        content_layout.addWidget(client_container)
    
    def setModernStyle(self):
        """Setup modern overall style"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ecf0f1, stop:1 #bdc3c7);
            }
            QWidget {
                font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
            }
            QStatusBar {
                background-color: rgba(52, 73, 94, 20);
                color: #2c3e50;
                font-weight: bold;
                border-top: 1px solid rgba(52, 73, 94, 50);
                padding: 3px 10px;
            }
        """)


# Main UI control class, responsible for starting server and log output
class Stats:
    """
    Server main interface control class
    
    Responsible for managing the server's graphical user interface, including starting the server, displaying logs,
    managing client lists and other functions.
    
    Attributes:
        ui (ModernServerUI): Modern UI interface object
        server_socket (ServerSocket): Server network socket object (injected externally)
    """
    def __init__(self):
        """
        Initialize server UI interface
        
        Create modern UI interface, connect signal slots, set up event handling for interface controls.
        """
        # Use modern UI
        self.ui = ModernServerUI()
        
        # Connect button events
        self.ui.StartButton.clicked.connect(self.handleStart)
        self.ui.DiscoverServerButton.clicked.connect(self.handleDiscoverServer)
        
        # Connect signals
        global_ms.log_signal.connect(self.append_log)
        global_ms.refresh_list_signal.connect(self.refresh_client_server_list)
        global_ms.message_log_signal.connect(self.append_message_log)

    def set_status(self, text, color="#2c3e50"):
        self.ui.statusbar.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.ui.statusbar.showMessage(text)

    def handleStart(self):
        """
        Handle start button click event
        
        Start all server services (UDP and TCP listening).
        Need to ensure server_socket object has been correctly injected.
        """
        # ServerSocket here is injected by main program
        if hasattr(self, 'server_socket'):
            self.server_socket.start_all()
            self.set_status("Server starting...", color="#218838")
            
            # Show green startup success tip
            tip = TipsWidget(self.ui)
            tip.setText("Server Started|Listening for connections")
            tip.status = TipsStatus.Succeed
            tip.move(100, 50)
            tip.resize(350, 30)
            tip.show()

    def handleDiscoverServer(self):
        """
        Handle discover server button click event
        
        Trigger server discovery function to search for other servers on the network.
        """
        if hasattr(self, 'server_socket'):
            self.server_socket.discover_servers()
            self.set_status("Discovering other servers...", color="#FF9800")
            
            # Show yellow discover server tip
            tip = TipsWidget(self.ui)
            tip.setText("Discover Servers|Broadcasting to discover other servers")
            tip.status = TipsStatus.Warning
            tip.move(100, 50)
            tip.resize(350, 30)
            tip.show()

    def append_log(self, text):
        """
        Add log text to chat history area (black font)
        """
        # Unified black font
        formatted_message = f'<span style="color: #222;">{text}</span>'
        self.ui.ChatHistory.append(formatted_message)

    def append_message_log(self, message_log):
        """
        Add message log to chat history area, only highlight content part in yellow
        """
        import html
        escaped_message = html.escape(message_log)
        # Only make the content part yellow, the rest is black
        import re
        pattern = r'(\[send\].*|\[receive\].*)'
        match = re.match(pattern, escaped_message)
        if match:
            # Highlight the whole line
            formatted_message = f'<span style="color: #FFA500;">{escaped_message}</span>'
        else:
            # Other cases, black
            formatted_message = f'<span style="color: #222;">{escaped_message}</span>'
        self.ui.ChatHistory.append("")
        self.ui.ChatHistory.append(formatted_message)
        self.ui.ChatHistory.append("")

    def refresh_client_server_list(self):
        # Clear list
        self.ui.ClientServerList.clear()
        # Add all connected clients
        if hasattr(self, 'server_socket'):
            # Client list
            with self.server_socket.client_info_lock:
                for user_id, info in self.server_socket.client_info.items():
                    self.ui.ClientServerList.addItem(f"[Client] {user_id} @ {info['ip']}:{info['port']}")
            # Server list
            with self.server_socket.server_list_lock:
                for server_id, info in self.server_socket.server_list.items():
                    self.ui.ClientServerList.addItem(f"[Server] {server_id} @ {info['ip']}:{info['port']}")
            
            # Update status bar
            client_count = len(self.server_socket.client_info)
            server_count = len(self.server_socket.server_list)
            self.set_status(f"Running - {client_count} clients, {server_count} servers", color="#2c3e50")