"""
Server UI control module

This module provides server-side graphical user interface control, including:
- Server startup control
- Log display and management
- Client list management
- Cross-thread signal communication
"""

from PySide6.QtWidgets import *
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Signal, QObject

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

# Main UI control class, responsible for starting server and log output
class Stats:
    """
    Server main interface control class
    
    Responsible for managing the server's graphical user interface, including starting the server, displaying logs,
    managing client lists and other functions.
    
    Attributes:
        uiLoader (QUiLoader): UI file loader
        ui (QWidget): Main interface UI object
        server_socket (ServerSocket): Server network socket object (injected externally)
    """
    def __init__(self):
        """
        Initialize server UI interface
        
        Load UI file, connect signal slots, set up event handling for interface controls.
        """
        self.uiLoader = QUiLoader()
        # Get correct UI file path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        ui_path = os.path.join(project_root, 'client', 'ui', 'Server.ui')
        self.ui = self.uiLoader.load(ui_path)
        self.ui.StartButton.clicked.connect(self.handleStart)
        self.ui.DiscoverServerButton.clicked.connect(self.handleDiscoverServer)
        global_ms.log_signal.connect(self.append_log)
        global_ms.refresh_list_signal.connect(self.refresh_client_server_list)
        global_ms.message_log_signal.connect(self.append_message_log)  # New: connect message log signal

    def handleStart(self):
        """
        Handle start button click event
        
        Start all server services (UDP and TCP listening).
        Need to ensure server_socket object has been correctly injected.
        """
        # ServerSocket here is injected by main program
        if hasattr(self, 'server_socket'):
            self.server_socket.start_all()

    def handleDiscoverServer(self):
        """
        Handle discover server button click event
        
        Trigger server discovery function to search for other servers on the network.
        """
        if hasattr(self, 'server_socket'):
            self.server_socket.discover_servers()

    def append_log(self, text):
        """
        Add log text to chat history area
        
        Args:
            text (str): Log text to add
        """
        self.ui.ChatHistory.append(text)

    def append_message_log(self, message_log):
        """
        Add message log to chat history area, displayed in yellow text
        
        This method is specifically used to display server forwarded message logs, will set text
        to yellow and add line breaks for distinction.
        
        Args:
            message_log (str): Message log text to add
        """
        # Escape HTML special characters to prevent <> from being interpreted as tags
        import html
        escaped_message = html.escape(message_log)
        # Use HTML format to set yellow text
        formatted_message = f'<span style="color: #FFA500;">{escaped_message}</span>'
        self.ui.ChatHistory.append(formatted_message)
        # Add empty line for distinction
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