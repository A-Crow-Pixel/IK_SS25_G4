from pickletools import uint2
# Import PySide6 modules for GUI
from PySide6.QtWidgets import *
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Signal, QObject, Qt
from PySide6.QtGui import QTextCursor, QTextBlockFormat
# Threading, network, translation, language detection and other third-party packages
from threading import Thread
from socket import *
from deep_translator import GoogleTranslator
from langdetect import detect
import datetime
from select import select
from proto import Message_pb2
from modules.PackingandUnpacking import *
import time
# Import reminder popup component
from rrd_widgets import TipsWidget, TipsStatus

uiLoader = QUiLoader()

# Signal class for communication between UI thread and worker thread
class MySignals(QObject):
    # Different UI components and string content signals
    text_print = Signal(QTextBrowser, str)
    subWin_print = Signal(QTextBrowser, str)
    hint1_print = Signal(QTextBrowser, str)
    add_tree_user = Signal(str, str)
    nameofchatLabel = Signal(QTextBrowser, str)
    chatMainWindow = Signal(str, str, bool)
    add_group_to_tree = Signal(str, str, str)  # (group_name, my_userid, my_serverid)
    show_reminder_popup = Signal(str)  # Show reminder popup signal
    show_group_invite = Signal(str, str, int)  # Show group invite popup signal (group_id, server_id, handle)
    add_message_to_chat_signal = Signal(str, str, str, bool)  # New: safely add message to chat window (chat_id, sender, message, is_me)
    close_dialog_signal = Signal(str)  # New: safely close dialog signal

# Global signal object
global_signal = MySignals()

# Current client user information
user = Message_pb2.User()

user.userId = 'User 3'
user.serverId = 'Server_4'
udp_port = 9999

# Main interface and business logic class
class Stats:
    def __init__(self):
        """Initialize the Stats class, set up UI, dialogs, signals, and event bindings."""
        # Load all required UI windows
        self.ui = uiLoader.load('ui/mainWindow.ui')
        self.dialog1 = uiLoader.load('ui/ConnectToServer.ui')
        self.dialog2 = uiLoader.load('ui/Add.ui')
        self.dialog3 = uiLoader.load('ui/ModifyGroup.ui')
        self.dialog4 = uiLoader.load('ui/InvitePopUp.ui')
        
        # Set window title to current username
        self.ui.setWindowTitle(user.userId)

        # Bind button events
        self.ui.SendButton.clicked.connect(self.handleSendButton)
        self.ui.ClientConnectButton.clicked.connect(self.ConnectToServer)
        self.ui.ADDButton.clicked.connect(self.add_users)
        self.ui.GroupButton.clicked.connect(self.handleGroupButton)
        self.ui.ReminderButton.clicked.connect(self.handleReminderButton)
        self.ui.TestTrans.clicked.connect(self.handleTestTransButton)

        # Server list and socket manager
        self.ServerList = {}
        self.tcp_socket = None
        self.Socketm = Socketmanager(self.dialog1, self.ServerList, self.tcp_socket,
                                     self.dialog2, self.ui, self.dialog3, self.dialog4)

        # User/group tree event binding
        self.ui.UserGroupTree.itemSelectionChanged.connect(self.on_chat_target_changed)
        self.ui.UserGroupTree.itemSelectionChanged.connect(self.update_group_button_status)

        # Bind global signals to interface
        self.signal = global_signal
        self.signal.nameofchatLabel.connect(self.printToLabel)
        self.signal.show_reminder_popup.connect(self.show_reminder_popup)
        self.signal.show_group_invite.connect(self.show_group_invite_popup)
        self.signal.close_dialog_signal.connect(self.close_dialog_safely)

        # Load reminder dialog
        self.reminder_dialog = None
        
        # Group invite related variables
        self.current_group_invite = None

    def SendButton(self, fb, text):
        """Display the input text in the chat history and clear the input box.
        Args:
            fb: The QTextEdit or similar widget to append text to.
            text: The message text to display.
        """
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        fb.append(text)
        self.ui.InputTextEdit.clear()

    def handleSendButton(self):
        """Handle the send button click event, send the message and clear the input box."""
        self.Socketm.send_message()
        self.ui.InputTextEdit.clear()

    def ConnectToServer(self):
        """Show the connect to server dialog and bind its events."""
        self.dialog1.udpButton.clicked.connect(self.udpBoardcast)
        self.dialog1.Connect.clicked.connect(self.connect_to_server)
        self.dialog1.Disconnect.clicked.connect(self.Socketm.disconnect)
        self.dialog1.exec()

    def update_group_button_status(self):
        """Enable or disable the group button based on the current selection in the user/group tree."""
        item = self.ui.UserGroupTree.currentItem()
        if item and item.data(0, Qt.UserRole)[0] == 'Group':
            self.ui.GroupButton.setEnabled(True)
        else:
            self.ui.GroupButton.setEnabled(False)

    def handleGroupButton(self):
        """Show the group management dialog for the selected group and bind its events."""
        self.dialog3.LeaveButton.clicked.connect(self.Socketm.leave_group)
        self.dialog3.InviteButton.clicked.connect(self.Socketm.invite_group)
        item = self.ui.UserGroupTree.currentItem()
        if item and item.data(0, Qt.UserRole)[0] == 'Group':
            group_id = item.data(0, Qt.UserRole)[1]
            self.dialog3.GroupName.setText(group_id)  # Set group name
            self.dialog3.show()

    def udpBoardcast(self):
        """Clear the server table and start UDP broadcast to discover servers."""
        self.dialog1.ServerTable.setRowCount(0)
        self.Socketm.UDPBoard()

    def connect_to_server(self):
        """Start a new thread to connect to the selected server via TCP."""
        Thread(target=self.Socketm.TCPConnect, daemon=True).start()

    def handleTestTransButton(self):
        """Send a test TRANSLATE message to the server for translation functionality testing."""
        if self.Socketm.connected and self.Socketm.tcp_socket:
            # Create TRANSLATE message
            translate_msg = Message_pb2.Translate()
            translate_msg.target_language = 1  # EN = 1
            translate_msg.original_text = "This is a message to test the translation function"
            # Do not set translated_text field
            
            # Serialize and send
            data = translate_msg.SerializeToString()
            fullmsg = Packing('TRANSLATE', data)
            self.Socketm.tcp_socket.send(fullmsg)
            
            # print("[Client] Sent TRANSLATE test message")  # Commented out to reduce console output
        else:
            # print("[Client] Not connected to server, cannot send TRANSLATE message")  # Commented out to reduce console output
            pass

    def add_users(self):
        """Show the add user/group dialog and bind its events."""
        self.dialog2.createButton1.setEnabled(False)
        def buttonEnable():
            self.dialog2.Hint1.clear()
            if self.dialog2.UserGroup.currentText() == 'User':
                self.dialog2.createButton1.setEnabled(False)
                self.dialog2.AddButton1.setEnabled(True)
            if self.dialog2.UserGroup.currentText() == 'Group':
                self.dialog2.createButton1.setEnabled(True)
                self.dialog2.AddButton1.setEnabled(False)
        self.dialog2.UserGroup.currentIndexChanged.connect(buttonEnable)
        self.dialog2.AddButton1.clicked.connect(self.Socketm.search_users)
        self.dialog2.createButton1.clicked.connect(self.Socketm.handle_create_group)
        self.dialog2.show()

    def on_chat_target_changed(self):
        """Update the chat label and switch chat window when the chat target changes."""
        item = self.ui.UserGroupTree.currentItem()
        if item:
            # Use data to get user ID or group ID, not text to get display text (may contain unread message markers)
            item_data = item.data(0, Qt.UserRole)
            if item_data and len(item_data) >= 2:
                chat_id = item_data[1]  # [0]type, [1]user_id or group_id
                # Use chat_id directly as display name to avoid including unread message markers
                self.signal.nameofchatLabel.emit(self.ui.NameOfChat, chat_id)
                
                # Switch to corresponding chat window
                self.Socketm.switch_chat_window(chat_id)

    def printToLabel(self, fb, selectUser):
        """Set the chat label to the selected user or group name.
        Args:
            fb: The QLabel to update.
            selectUser: The name to display.
        """
        fb.setText(selectUser)

    def handleReminderButton(self):
        """Show the reminder dialog and bind its set button event."""
        if self.reminder_dialog is None:
            self.reminder_dialog = uiLoader.load('ui/reminder.ui')
            self.reminder_dialog.setButton.clicked.connect(self.handleSetReminder)
        self.reminder_dialog.show()

    def handleSetReminder(self):
        """Handle setting a reminder, send the reminder to the server, and clear the dialog."""
        event_name = self.reminder_dialog.Eventname.text()
        time_seconds = self.reminder_dialog.Time.text()
        
        if not event_name or not time_seconds:
            return
        
        try:
            countdown_seconds = int(time_seconds)
            if countdown_seconds <= 0:
                return
        except ValueError:
            return
        
        # Send SET_REMINDER message to server
        self.Socketm.send_set_reminder(event_name, countdown_seconds)
        
        # Clear input boxes and close dialog
        self.reminder_dialog.Eventname.clear()
        self.reminder_dialog.Time.clear()
        self.reminder_dialog.close()

    def show_reminder_popup(self, message):
        """Display a reminder popup with the given message.
        Args:
            message: The reminder message to display.
        """
        # print("show_reminder_popup function")  # Commented out to reduce console output
        tip = TipsWidget(self.ui)
        tip.setText(f"Reminder|{message}")
        tip.status = TipsStatus.Succeed
        tip.move(200, 100)
        tip.resize(420, 35)
        tip.show()

    def show_group_invite_popup(self, group_id, server_id, handle):
        """Show the group invite popup dialog and bind its accept/reject events.
        Args:
            group_id: The group ID for the invite.
            server_id: The server ID for the invite.
            handle: The handle for the invite event.
        """
        self.current_group_invite = (group_id, server_id, handle)
        self.dialog4.InviteText.setText(f"You are invited to join group: {group_id}, do you accept?")
        
        # Disconnect previous connections first to avoid duplicate binding
        try:
            self.dialog4.YesButton.clicked.disconnect()
            self.dialog4.NoButton.clicked.disconnect()
        except:
            pass  # Ignore if no connection exists
            
        self.dialog4.YesButton.clicked.connect(self.accept_group_invite)
        self.dialog4.NoButton.clicked.connect(self.reject_group_invite)
        self.dialog4.show()  # Use show() instead of exec() to avoid blocking

    def accept_group_invite(self):
        """Accept the current group invite and send a request to the server."""
        if self.current_group_invite:
            group_id, server_id, handle = self.current_group_invite
            req = Message_pb2.ListGroupMembers()
            req.group.groupId = group_id
            req.group.serverId = server_id
            if self.Socketm.tcp_socket:
                self.Socketm.tcp_socket.send(Packing('QUERY_GROUP_MEMBERS', req.SerializeToString()))
            self.dialog4.hide()  # Hide popup
            self.current_group_invite = None  # Clear current invite info

    def reject_group_invite(self):
        """Reject the current group invite and close the dialog."""
        self.dialog4.hide()  # Hide popup
        self.current_group_invite = None  # Clear current invite info

    def close_dialog_safely(self, dialog_name):
        """Safely close a dialog by name.
        Args:
            dialog_name: The name of the dialog to close.
        """
        if dialog_name == "add_dialog":
            self.dialog2.close()





# Socket and message processing main class
class Socketmanager:
    def __init__(self, dialog_ref, server_list, tcp_ref, dialog_ref1, ui_ref, dialog_ref2, dialog_ref3):
        """Initialize the Socketmanager class with dialog references and UI components.
        Args:
            dialog_ref: Reference to the connect to server dialog.
            server_list: Dictionary to store server information.
            tcp_ref: Reference to the TCP socket.
            dialog_ref1: Reference to the add user/group dialog.
            ui_ref: Reference to the main UI window.
            dialog_ref2: Reference to the modify group dialog.
            dialog_ref3: Reference to the invite popup dialog.
        """
        self.dialog1 = dialog_ref
        self.dialog2 = dialog_ref1
        self.dialog3 = dialog_ref2
        self.dialog4 = dialog_ref3
        self.ui = ui_ref
        self.Serverlist = server_list
        self.udp_socket = None
        self.tcp_socket = None
        self.connected = False
        self.recv_thread = None
        self.heartbeat_thread = None
        self.last_active_time = 0  # Last activity time
        self.heartbeat_interval = 30  # Heartbeat interval
        self.heartbeat_timeout = 90   # Timeout duration
        self.search_users_unit64id = None

        # Various signals and UI control binding
        self.signals = MySignals()
        self.signals.subWin_print.connect(self.update_subWin)
        self.signals.hint1_print.connect(self.update_Hint1)
        self.signals.add_tree_user.connect(self.add_user_to_tree)
        self.signals.chatMainWindow.connect(self.update_ChatMainWindow)
        self.signals.add_group_to_tree.connect(self.add_group_to_tree)
        self.signals.add_message_to_chat_signal.connect(self.add_message_to_chat)
        self.signals.close_dialog_signal.connect(global_signal.close_dialog_signal.emit)

        # Chat window management
        self.chat_browsers = {}  # Store QTextBrowser for each chat object: {chat_id: QTextBrowser}
        self.current_chat_id = None  # Currently selected chat object ID
        
        # Unread message management
        self.unread_counts = {}  # Store unread message count for each chat object: {chat_id: count}

    def update_subWin(self, fb, text):
        """Update the sub-window content with the given text.
        Args:
            fb: The QPlainTextEdit widget to update.
            text: The text to display.
        """
        fb.setPlainText(text)

    def update_Hint1(self, fb, text):
        """Update the hint widget with the given text.
        Args:
            fb: The QTextEdit widget to update.
            text: The text to display.
        """
        fb.setPlainText(text)
    
    def increment_unread_count(self, chat_id):
        """Increment unread message count for a specified chat object.
        Args:
            chat_id: The ID of the chat object.
        """
        """Increment unread message count for specified chat object"""
        if chat_id not in self.unread_counts:
            self.unread_counts[chat_id] = 0
        self.unread_counts[chat_id] += 1
        self.update_tree_display(chat_id)
    
    def clear_unread_count(self, chat_id):
        """Clear unread message count for a specified chat object.
        Args:
            chat_id: The ID of the chat object.
        """
        """Clear unread message count for specified chat object"""
        if chat_id in self.unread_counts:
            self.unread_counts[chat_id] = 0
            self.update_tree_display(chat_id)
    
    def update_tree_display(self, chat_id):
        """Update the display text of a specified chat object in the tree widget.
        Args:
            chat_id: The ID of the chat object to update.
        """
        """Update display text for specified chat object in tree control"""
        root = self.ui.UserGroupTree.invisibleRootItem()
        
        # First search all top-level items (private chat users or groups)
        for i in range(root.childCount()):
            item = root.child(i)
            item_data = item.data(0, Qt.UserRole)
            if item_data and len(item_data) >= 2:
                if item_data[1] == chat_id:  # Found matching chat object
                    self._update_item_text(item, chat_id)
                    return
        
        # If not found in top-level items, search group members
        for i in range(root.childCount()):
            item = root.child(i)
            # Check group members
            for j in range(item.childCount()):
                child = item.child(j)
                child_data = child.data(0, Qt.UserRole)
                if child_data and len(child_data) >= 2 and child_data[1] == chat_id:
                    self._update_item_text(child, chat_id)
                    return
    
    def _update_item_text(self, item, chat_id):
        """Update text display for a single tree widget item.
        Args:
            item: The tree widget item to update.
            chat_id: The ID of the chat object.
        """
        """Update text display for single tree control item"""
        item_data = item.data(0, Qt.UserRole)
        if not item_data or len(item_data) < 2:
            return
        
        base_name = item_data[1]  # User ID or group ID
        unread_count = self.unread_counts.get(chat_id, 0)
        
        if unread_count > 0:
            # Limit maximum display number, show 99+ if over 99
            display_count = "99+" if unread_count > 99 else str(unread_count)
            
            # Use unified red circle + number style
            badge = f"🔴{display_count}"
            
            display_text = f"{base_name}  {badge}"
        else:
            display_text = base_name
        item.setText(0, display_text)

    def get_or_create_chat_browser(self, chat_id):
        """Get or create a QTextBrowser for a specified chat object.
        Args:
            chat_id: The ID of the chat object.
        Returns:
            QTextBrowser: The chat browser widget.
        """
        """Get or create QTextBrowser for specified chat object"""
        if chat_id not in self.chat_browsers:
            # Create new QTextBrowser
            browser = QTextBrowser()
            browser.setReadOnly(True)
            
            # Add to StackedWidget
            self.ui.ChatMainWindow.addWidget(browser)
            self.chat_browsers[chat_id] = browser
            
            print(f"[Client] Created new chat window for chat object {chat_id}")
        return self.chat_browsers[chat_id]
    
    def switch_chat_window(self, chat_id):
        """Switch to the window of a specified chat object.
        Args:
            chat_id: The ID of the chat object to switch to.
        """
        """Switch to specified chat object window"""
        if chat_id == self.current_chat_id:
            return  # Already current window, no need to switch
        
        browser = self.get_or_create_chat_browser(chat_id)
        self.ui.ChatMainWindow.setCurrentWidget(browser)
        self.current_chat_id = chat_id
        
        # Clear unread message count for this chat object
        self.clear_unread_count(chat_id)
        
        print(f"[Client] Switched to chat object {chat_id} window")
    
    def add_message_to_chat(self, chat_id, sender, message, is_me=False):
        """Add message to the window of a specified chat object.
        Args:
            chat_id: The ID of the chat object.
            sender: The sender of the message.
            message: The message content.
            is_me: Whether the message is sent by the current user.
        """
        """Add message to specified chat object window"""
        browser = self.get_or_create_chat_browser(chat_id)
        cursor = browser.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertBlock()
        block_fmt = QTextBlockFormat()
        block_fmt.setAlignment(Qt.AlignRight if is_me else Qt.AlignLeft)
        cursor.setBlockFormat(block_fmt)
        name = "Me" if is_me else sender
        cursor.insertHtml(f"<b>{name}</b><br>{message}")
        cursor.insertBlock()
        
        # Auto-scroll to bottom
        browser.setTextCursor(cursor)
        browser.ensureCursorVisible()
        
        # Unread message handling: if not a self-sent message and not the current chat window, increment unread count
        if not is_me and chat_id != self.current_chat_id:
            self.increment_unread_count(chat_id)

    def add_user_to_tree(self, user_id, server_id):
        """Add a user to the left tree widget.
        Args:
            user_id: The user ID to add.
            server_id: The server ID of the user.
        """
        """Add user to left tree"""
        root = self.ui.UserGroupTree.invisibleRootItem()
        
        # Check if user already exists
        for i in range(root.childCount()):
            item = root.child(i)
            item_data = item.data(0, Qt.UserRole)
            if (item_data and len(item_data) >= 2 and 
                item_data[0] == 'User' and item_data[1] == user_id):
                return  # User already exists
        
        userItem = QTreeWidgetItem()
        userItem.setText(0, user_id)  # Initial display user ID
        userItem.setData(0, Qt.UserRole, ['User', user_id, server_id])
        root.addChild(userItem)

    def update_ChatMainWindow(self, sender, message, is_me=False):
        """Update the chat main window with a new message.
        Args:
            sender: The sender of the message.
            message: The message content.
            is_me: Whether the message is sent by the current user.
        """
        """Update chat window display (supports multiple windows)"""
        # Get current chat object ID
        if self.current_chat_id:
            # Use signal to safely add message to chat window
            self.signals.add_message_to_chat_signal.emit(self.current_chat_id, sender, message, is_me)

    def add_group_to_tree(self, group_name, my_userid, my_serverid):
        """Add a group to the tree widget with the current user as the first member.
        Args:
            group_name: The name of the group to add.
            my_userid: The current user's ID.
            my_serverid: The current user's server ID.
        """
        """Add group to tree (including self as the first member)"""
        root = self.ui.UserGroupTree.invisibleRootItem()
        
        # Check if group already exists
        for i in range(root.childCount()):
            child = root.child(i)
            if (child.data(0, Qt.UserRole) and 
                len(child.data(0, Qt.UserRole)) >= 2 and
                child.data(0, Qt.UserRole)[0] == 'Group' and 
                child.data(0, Qt.UserRole)[1] == group_name):
                print(f"[Client] Group {group_name} already exists, skipping creation")
                return  # Group already exists, return directly
        
        # Create new group
        groupItem = QTreeWidgetItem()
        groupItem.setText(0, group_name)
        groupItem.setData(0, Qt.UserRole, ['Group', group_name])
        root.addChild(groupItem)
        userItem = QTreeWidgetItem(groupItem)
        userItem.setText(0, my_userid)
        userItem.setData(0, Qt.UserRole, ['User', my_userid, my_serverid])
        groupItem.addChild(userItem)
        groupItem.setExpanded(True)
        print(f"[Client] Successfully created group {group_name} and added to UI tree")

    def UDPBoard(self):
        """Perform UDP broadcast to discover servers on the network."""
        self.dialog1.ServerTable.setRowCount(0)
        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.udp_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.udp_socket.settimeout(1)  # Increase timeout
        
        # Try multiple broadcast addresses
        broadcast_addrs = [
            '255.255.255.255',  # Global broadcast
        ]

        DiscoverServer = Message_pb2.DiscoverServer()
        data = DiscoverServer.SerializeToString()
        fullmsg = Packing('DISCOVER_SERVER', data)
        
        # Send to all broadcast addresses
        servers_found = False
        for broadcast_addr in broadcast_addrs:
            try:
                BoardcastAddr = (broadcast_addr, udp_port)
                self.udp_socket.sendto(fullmsg, BoardcastAddr)
                # print(f"[Client] sendto {broadcast_addr}:{udp_port} a DISCOVER_SERVER")  # Commented out, reduce console output
                
                # Try to receive response
                try:
                    resp, server_addr = self.udp_socket.recvfrom(2048)
                    purpose, length, payload = Packing.unpack(resp)
                    if purpose == "SERVER_ANNOUNCE":
                        announce = Message_pb2.ServerAnnounce()
                        announce.ParseFromString(payload)
                        self.dialog1.Hint.setPlainText("The above servers have been found.")
                        for feat in announce.feature:
                            rowCount = self.dialog1.ServerTable.rowCount()
                            self.dialog1.ServerTable.insertRow(rowCount)
                            self.dialog1.ServerTable.setItem(rowCount, 0, QTableWidgetItem(announce.serverId))
                            self.dialog1.ServerTable.setItem(rowCount, 1, QTableWidgetItem(feat.featureName))
                            self.dialog1.ServerTable.setItem(rowCount, 2, QTableWidgetItem(str(feat.port)))
                            self.Serverlist[announce.serverId] = [server_addr[0], feat.port]
                        servers_found = True
                        # print(f"[Client] Received server response from {server_addr}")  # Commented out, reduce console output
                        break  # Stop when server is found
                except TimeoutError:
                    continue  # Continue to next broadcast address
            except Exception as e:
                # print(f"[Client] Broadcasting to {broadcast_addr} failed: {e}")  # Commented out, reduce console output
                continue
        
        if not servers_found:
            self.dialog1.Hint.setPlainText('Server not found-->Timeout!!!')
        
        time.sleep(0.1)
        self.udp_socket.close()

    def close_connection(self):
        """Close the TCP connection and clean up resources."""
        if self.tcp_socket:
            try:
                self.tcp_socket.close()
            except Exception as e:
                # print("[Client] Socket close error:", e)  # Commented out, reduce console output
                pass
            self.tcp_socket = None
        self.connected = False


    def TCPConnect(self):
        """Establish TCP connection to the selected server and start receive/heartbeat threads."""
        if self.connected:
            self.signals.subWin_print.emit(self.dialog1.Hint, "Already connected, please disconnect first!")
            return
        self.close_connection()
        currentrow = self.dialog1.ServerTable.currentRow()
        if currentrow == -1:
            self.signals.subWin_print.emit(self.dialog1.Hint, "Please select a server first!")
            return
        serverid = self.dialog1.ServerTable.item(currentrow, 0).text()
        serverPort = int(self.dialog1.ServerTable.item(currentrow, 2).text())
        serverIP = self.Serverlist.get(serverid)[0]

        try:
            # print("[Client] Opening new TCP socket")  # Commented out, reduce console output
            self.tcp_socket = socket(AF_INET, SOCK_STREAM)
            self.tcp_socket.connect((serverIP, serverPort))

            ConnectClient = Message_pb2.ConnectClient()
            ConnectClient.user.userId = user.userId
            ConnectClient.user.serverId = user.serverId
            data = ConnectClient.SerializeToString()
            fullmsg = Packing('CONNECT_CLIENT', data)
            self.tcp_socket.send(fullmsg)

            self.connected = True
            self.last_active_time = time.time()

            self.recv_thread = Thread(target=self.recv_loop, daemon=True)
            self.recv_thread.start()
            self.heartbeat_thread = Thread(target=self.heartbeat_loop, daemon=True)
            self.heartbeat_thread.start()

        except Exception as e:
            self.signals.subWin_print.emit(self.dialog1.Hint, f"Connect error: {e}")
            self.close_connection()

    def heartbeat_loop(self):
        """Heartbeat thread that periodically checks connection status and activity."""
        while self.connected and self.tcp_socket:
            time.sleep(self.heartbeat_interval)
            now = time.time()
            if not self.connected or not self.tcp_socket:
                break
            if now - self.last_active_time > self.heartbeat_timeout:
                self.signals.subWin_print.emit(self.dialog1.Hint, "Heartbeat timeout, connection closed.")
                self.close_connection()
                break
            try:
                ping_msg = Packing('PING', b'')
                self.tcp_socket.send(ping_msg)
                # print("[Client] Sent PING")  # Commented out, reduce console output
            except Exception as e:
                # print("[Client] Heartbeat send error:", e)  # Commented out, reduce console output
                self.close_connection()
                break

    def recv_loop(self):
        """TCP message main receive thread that processes all received protocol packets."""
        while self.connected and self.tcp_socket:
            data = self.tcp_socket.recv(2048)
            if not data:
                self.signals.subWin_print.emit(self.dialog1.Hint, "Disconnected by server.")
                self.close_connection()
                break
            self.last_active_time = time.time()
            purpose, length, payload = Packing.unpack(data)
            # print("[Client] Purpose:", purpose)  # Commented out, reduce console output
            # Process different protocol packets based on purpose
            if purpose == 'CONNECTED':
                CR = Message_pb2.ConnectResponse()
                CR.ParseFromString(payload)
                if CR.result == Message_pb2.ConnectResponse.CONNECTED:
                    self.signals.subWin_print.emit(self.dialog1.Hint, "Successfully connected to the server.")
                elif CR.result == Message_pb2.ConnectResponse.UNKNOWN_ERROR:
                    self.signals.subWin_print.emit(self.dialog1.Hint, "Server responded with UNKNOWN_ERROR")
                    self.close_connection()
                    break
                elif CR.result == Message_pb2.ConnectResponse.IS_ALREADY_CONNECTED_ERROR:
                    self.signals.subWin_print.emit(self.dialog1.Hint, "This Server is already connected! Please try later.")
                    self.close_connection()
                    break

            elif purpose == 'PING':
                pong_msg = Packing('PONG', b'')
                self.tcp_socket.send(pong_msg)
                # print("[Client] Received PING, sent PONG")  # Commented out, reduce console output
            elif purpose == 'PONG':
                # print("[Client] Received PONG (heartbeat ok)")  # Commented out, reduce console output
                pass

            elif purpose == 'SEARCH_USERS_RESP':
                QueryUserResponse = Message_pb2.QueryUsersResponse()
                QueryUserResponse.ParseFromString(payload)
                if self.search_users_unit64id != QueryUserResponse.handle:
                    # print(self.search_users_unit64id)  # Commented out, reduce console output
                    pass
                else:
                    user_names = '\n'.join(user.userId for user in QueryUserResponse.users)
                    self.signals.hint1_print.emit(self.dialog2.Hint1, user_names)
                    input_userid = self.dialog2.printId.text()
                    if input_userid in [user.userId for user in QueryUserResponse.users]:
                        # print('有')  # Commented out, reduce console output
                        server_id = next(user.serverId for user in QueryUserResponse.users if user.userId == input_userid)
                        self.signals.add_tree_user.emit(input_userid, server_id)

            elif purpose == 'MESSAGE':
                chat_msg = Message_pb2.ChatMessage()
                chat_msg.ParseFromString(payload)
                recipient_type = chat_msg.WhichOneof('recipient')
                is_me = (chat_msg.author.userId == user.userId)
                sender = chat_msg.author.userId
                sender_server = chat_msg.author.serverId
                
                # Get display text based on message content type
                content_type = chat_msg.WhichOneof('content')
                if content_type == 'textContent':
                    # Normal text message
                    msg_text = chat_msg.textContent
                elif content_type == 'translation':
                    # Translation message, display translated content
                    if chat_msg.translation.translated_text:
                        msg_text = chat_msg.translation.translated_text
                    else:
                        # If no translation result, display original text
                        msg_text = chat_msg.translation.original_text
                else:
                    # Other message types, skip for now
                    return

                if chat_msg.author.userId == user.userId:
                    return  # Ignore self-sent echo

                if recipient_type == 'user':
                    # First add sender to user tree (if not already)
                    self.signals.add_tree_user.emit(sender, sender_server)
                    
                    # Use signal to safely add message to sender's chat window
                    self.signals.add_message_to_chat_signal.emit(sender, sender, msg_text, is_me)
                    
                    # If the currently selected chat is the sender, no extra action needed (window is already switched)
                    # Message will automatically appear in the current window
                    
                    # Send ACK to server
                    ack = Message_pb2.ChatMessageResponse()
                    ack.messageSnowflake = chat_msg.messageSnowflake
                    ds = ack.statuses.add()
                    ds.user.userId = user.userId
                    ds.user.serverId = user.serverId
                    ds.status = Message_pb2.ChatMessageResponse.DELIVERED
                    ack_packet = Packing('MESSAGE_ACK', ack.SerializeToString())
                    self.tcp_socket.send(ack_packet)

                elif recipient_type == 'group':
                    group_id = chat_msg.group.groupId
                    # Use signal to safely add message to group chat window
                    self.signals.add_message_to_chat_signal.emit(group_id, sender, msg_text, False)
                    # Also need ACK
                    ack = Message_pb2.ChatMessageResponse()
                    ack.messageSnowflake = chat_msg.messageSnowflake
                    ds = ack.statuses.add()
                    ds.user.userId = user.userId
                    ds.user.serverId = user.serverId
                    ds.status = Message_pb2.ChatMessageResponse.DELIVERED
                    ack_packet = Packing('MESSAGE_ACK', ack.SerializeToString())
                    self.tcp_socket.send(ack_packet)
                elif recipient_type == 'userOfGroup':
                    pass

            elif purpose == 'MESSAGE_ACK':
                ack = Message_pb2.ChatMessageResponse()
                ack.ParseFromString(payload)
                for status in ack.statuses:
                    # print("收信人", status.user.userId, "投递状态：", status.status)  # Commented out, reduce console output
                    pass

            elif purpose == "MODIFY_GROUP_RESP":
                resp = Message_pb2.ModifyGroupResponse()
                resp.ParseFromString(payload)
                if resp.result == Message_pb2.ModifyGroupResponse.SUCCESS:
                    group_name = self.pending_create_group_name
                    # Use signal to safely close dialog
                    self.signals.close_dialog_signal.emit("add_dialog")
                    self.signals.add_group_to_tree.emit(group_name, user.userId, user.serverId)
                    self.signals.hint1_print.emit(self.dialog2.Hint1, f"Group {group_name} created successfully!")
                else:
                    msg = "Server refused to create group" if resp.result == Message_pb2.ModifyGroupResponse.NOT_PERMITTED else "Group creation failed"
                    self.signals.hint1_print.emit(self.dialog2.Hint1, msg)
                    # Re-enable create button to allow retry
                    self.dialog2.createButton1.setEnabled(True)

            elif purpose == 'NOTIFY_GROUP_INVITE':
                notify = Message_pb2.NotifyGroupInvite()
                notify.ParseFromString(payload)
                group_id = notify.group.groupId
                server_id = notify.group.serverId
                handle = notify.handle

                # Display group invite popup in the main thread
                global_signal.show_group_invite.emit(group_id, server_id, handle)

            elif purpose == 'GROUP_MEMBERS':
                group_members = Message_pb2.GroupMembers()
                group_members.ParseFromString(payload)
                group_id = group_members.group.groupId
                root = self.ui.UserGroupTree.invisibleRootItem()
                
                # Find if group already exists
                existing_group_item = None
                for i in range(root.childCount()):
                    child = root.child(i)
                    if (child.data(0, Qt.UserRole) and 
                        len(child.data(0, Qt.UserRole)) >= 2 and
                        child.data(0, Qt.UserRole)[0] == 'Group' and 
                        child.data(0, Qt.UserRole)[1] == group_id):
                        existing_group_item = child
                        break
                
                if existing_group_item:
                    # Group already exists, update member list
                    # Clear existing members (but keep group itself)
                    while existing_group_item.childCount() > 0:
                        existing_group_item.removeChild(existing_group_item.child(0))
                    
                    # Add updated member list
                    for m in group_members.user:
                        userItem = QTreeWidgetItem(existing_group_item)
                        userItem.setText(0, m.userId)
                        userItem.setData(0, Qt.UserRole, ['User', m.userId, m.serverId])
                        existing_group_item.addChild(userItem)
                    existing_group_item.setExpanded(True)
                    
                    # Log update
                    print(f"[Client] Group {group_id} member list updated")
                else:
                    # Group does not exist, create new group (this is for joining a new group)
                    groupItem = QTreeWidgetItem()
                    groupItem.setText(0, group_id)
                    groupItem.setData(0, Qt.UserRole, ['Group', group_id])
                    root.addChild(groupItem)
                    
                    # Check if self is in member list, if not add
                    member_user_ids = [m.userId for m in group_members.user]
                    if user.userId not in member_user_ids:
                        # Add self first
                        userItem = QTreeWidgetItem(groupItem)
                        userItem.setText(0, user.userId)
                        userItem.setData(0, Qt.UserRole, ['User', user.userId, user.serverId])
                        groupItem.addChild(userItem)
                    
                    # Then add other members
                    for m in group_members.user:
                        userItem = QTreeWidgetItem(groupItem)
                        userItem.setText(0, m.userId)
                        userItem.setData(0, Qt.UserRole, ['User', m.userId, m.serverId])
                        groupItem.addChild(userItem)
                    groupItem.setExpanded(True)
                    
                    # Only send JOIN_GROUP message when creating a new group
                    join = Message_pb2.JoinGroup()
                    join.group.groupId = group_id
                    join.group.serverId = group_members.group.serverId  # Get from GROUP_MEMBERS message
                    join.user.userId = user.userId
                    join.user.serverId = user.serverId
                    self.tcp_socket.send(Packing('JOIN_GROUP', join.SerializeToString()))

            elif purpose == 'REMINDER':
                try:
                    reminder = Message_pb2.Reminder()
                    reminder.ParseFromString(payload)
                    
                    event = reminder.reminderContent
                    message = f"Your event '{event}' time is up!"
                    
                    # Send signal to display reminder popup
                    # print('test 111')  # Commented out, reduce console output
                    global_signal.show_reminder_popup.emit(message)
                    
                except Exception as e:
                    # print(f"[Client] REMINDER error: {e}")  # Commented out, reduce console output
                    pass

            else:
                # Process other unknown messages
                # print(f"[Client] Received unhandled message: {purpose}")  # Commented out, reduce console output
                pass

    def disconnect(self):
        """Initiate disconnection from the server."""
        self.signals.subWin_print.emit(self.dialog1.Hint, "Disconnected.")
        self.close_connection()

    def search_users(self):
        """Search for users by sending a query to the server."""
        if self.dialog2.UserGroup.currentText() == 'User':
            text = self.dialog2.printId.text()
            if not text:
                self.signals.hint1_print.emit(self.dialog2.Hint1, 'Please Enter a UserId or ServerId first')
                return
            QueryUsers = Message_pb2.QueryUsers()
            QueryUsers.query = text
            QueryUsers.handle = int(time.time())
            self.search_users_unit64id = QueryUsers.handle
            data = QueryUsers.SerializeToString()
            tosend = Packing('SEARCH_USERS', data)
            self.tcp_socket.send(tosend)
        elif self.dialog2.UserGroup.currentText() == 'Group':
            pass

    def send_message(self):
        """Send a message to the currently selected user or group."""
        item = self.ui.UserGroupTree.currentItem()
        node_type = item.data(0, Qt.UserRole)[0]
        msg = Message_pb2.ChatMessage()
        msg.messageSnowflake = int(time.time())
        msg.author.userId = user.userId
        msg.author.serverId = user.serverId
        
        # Get original text from user input
        original_text = self.ui.InputTextEdit.toPlainText()
        
        # Get selected language
        selected_language = self.ui.TransComboBox.currentText()
        
        if selected_language == "Original":
            # Send normal text message
            msg.textContent = original_text
            display_text = original_text
        else:
            # Send translation message
            msg.translation.original_text = original_text
            
            # Set target language
            language_map = {
                'Deutsch': 0,   # DE
                'English': 1,   # EN
                '中文': 2,  # ZH
                'Türkçe': 3
            }
            msg.translation.target_language = language_map.get(selected_language, 1)
            
            # Local display translated content
            from modules.Translator import translator
            display_text = translator(original_text, selected_language)
        
        # Set recipient
        if node_type == 'User':
            msg.user.userId = item.data(0, Qt.UserRole)[1]
            msg.user.serverId = item.data(0, Qt.UserRole)[2]
        elif node_type == 'Group':
            msg.group.groupId = item.data(0, Qt.UserRole)[1]
        else:
            return
        
        # Send message to server
        data = msg.SerializeToString()
        tosend = Packing('MESSAGE', data)
        self.tcp_socket.send(tosend)
        
        # Display content in the corresponding chat window (user sees translated version or original)
        if node_type == 'User':
            chat_id = item.data(0, Qt.UserRole)[1]  # User ID
        elif node_type == 'Group':
            chat_id = item.data(0, Qt.UserRole)[1]  # Group ID
        
        # Use signal to safely add message to chat window
        self.signals.add_message_to_chat_signal.emit(chat_id, user.userId, display_text, True)

    def handle_create_group(self):
        """Send a group creation request to the server."""
        group_name = self.dialog2.printId.text()
        if not group_name:
            self.signals.hint1_print.emit(self.dialog2.Hint1, "Please enter group name!")
            return
        
        # Disable create button to prevent duplicate clicks
        self.dialog2.createButton1.setEnabled(False)
        
        modify_group_msg = Message_pb2.ModifyGroup()
        modify_group_msg.handle = int(time.time())
        modify_group_msg.groupId = group_name
        modify_group_msg.displayName = group_name
        modify_group_msg.deleteGroup = False
        admin_user = modify_group_msg.admins.add()
        admin_user.userId = user.userId
        admin_user.serverId = user.serverId
        data = modify_group_msg.SerializeToString()
        packet = Packing('MODIFY_GROUP', data)
        self.tcp_socket.send(packet)
        self.signals.hint1_print.emit(self.dialog2.Hint1, f"Group creation request sent to server: {group_name}")
        self.pending_create_group_name = group_name

    def leave_group(self):
        """Leave the current group chat and clean up related resources."""
        leave = Message_pb2.LeaveGroup()
        group_id = self.dialog3.GroupName.text()
        leave.group.groupId = group_id
        leave.group.serverId = user.serverId
        leave.user.userId = user.userId
        leave.user.serverId = user.serverId
        self.tcp_socket.send(Packing('LEAVE_GROUP', leave.SerializeToString()))
        self.dialog3.close()
        
        # Delete chat window corresponding to the group
        if group_id in self.chat_browsers:
            browser = self.chat_browsers[group_id]
            # If the chat window for this group is currently displayed, switch to another window
            if self.current_chat_id == group_id:
                # If there are other chat windows, switch to the first one; otherwise, create a blank window
                if len(self.chat_browsers) > 1:
                    # Find the first chat window that is not the current group
                    for chat_id in self.chat_browsers:
                        if chat_id != group_id:
                            self.switch_chat_window(chat_id)
                            break
                else:
                    # No other chat windows, switch to default blank window
                    self.current_chat_id = None
            
            # Remove and delete the chat window from StackedWidget
            self.ui.ChatMainWindow.removeWidget(browser)
            browser.deleteLater()
            del self.chat_browsers[group_id]
            
            # Clear unread message count for the group
            if group_id in self.unread_counts:
                del self.unread_counts[group_id]
        
        # Delete group from tree control
        root = self.ui.UserGroupTree.invisibleRootItem()
        for i in range(root.childCount()):
            child = root.child(i)
            if child.data(0, Qt.UserRole)[0] == 'Group' and child.data(0, Qt.UserRole)[1] == group_id:
                root.removeChild(child)
                break

    def invite_group(self):
        """Invite other users to join the current group."""
        invite = Message_pb2.InviteToGroup()
        invite.handle = int(time.time())
        invite.user.userId = self.dialog3.lineEdit.text()
        invite.user.serverId = user.serverId
        invite.groupId = self.dialog3.GroupName.text()
        self.tcp_socket.send(Packing('INVITE_GROUP', invite.SerializeToString()))

    def send_set_reminder(self, event_name, countdown_seconds):
        """Send a set reminder message to the server.
        Args:
            event_name: The name of the reminder event.
            countdown_seconds: The countdown time in seconds.
        """
        if not self.tcp_socket:
            return
        
        set_reminder = Message_pb2.SetReminder()
        # User can only set reminder for themselves, so target user is current user
        set_reminder.user.userId = user.userId
        set_reminder.user.serverId = user.serverId
        set_reminder.event = event_name
        set_reminder.countdownSeconds = countdown_seconds
        
        data = set_reminder.SerializeToString()
        tosend = Packing('SET_REMINDER', data)
        self.tcp_socket.send(tosend)

# Program entry
if __name__ == '__main__':
    app = QApplication([])
    main = Stats()
    main.ui.show()
    app.exec()
