"""
Chat application client module

This module implements the client functionality of the chat application, including:
- Graphical user interface management
- Network communication (TCP/UDP)
- Message sending and receiving
- Group management
- Reminder functionality
- Translation functionality
- File transfer, etc.

Main classes:
- MySignals: Cross-thread communication signal class
- Stats: Main interface control class
- Socketmanager: Network connection management class
"""

import datetime
import os
# Add project root directory to path to avoid import conflicts
import sys
import threading
from socket import *   # noqa: F403
# Threading, network, translation, language detection and other third-party packages
from threading import Thread

from PySide6.QtCore import Signal, QObject, Qt
from PySide6.QtGui import QTextBlockFormat, QTextDocument
from PySide6.QtUiTools import QUiLoader
# Import PySide6 modules for GUI
from PySide6.QtWidgets import *  # noqa: F403

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from proto import Message_pb2  # noqa: E402
from modules.PackingandUnpacking import *  # noqa: E402, F403
import time  # noqa: E402
# Import reminder popup component
from rrd_widgets import TipsWidget, TipsStatus  # noqa: E402
from PySide6.QtWidgets import QTextBrowser  # noqa: E402
from PySide6.QtGui import QTextCursor  # noqa: E402

uiLoader = QUiLoader()

# Chat history management class
class ChatHistoryManager:
    """
    Chat history manager
    
    Maintains independent chat history records for each chat object (user/group)
    Uses multi-threading to optimize chat switching performance
    """
    def __init__(self):
        # Chat history dictionary: key is chat object identifier, value is QTextDocument
        self.chat_histories = {}
        # Currently selected chat object
        self.current_chat_id = None
        # Lock for thread synchronization
        self.history_lock = threading.Lock()
        # Thread pool for handling chat switching
        self.thread_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="ChatHistory")
        # Switch signal
        self.switch_signal = ChatSwitchSignal()
    
    def get_chat_id(self, chat_type, identifier, server_id=None):
        """Generate unique identifier for chat object"""
        if chat_type == 'User':
            return f"user_{identifier}_{server_id}"
        elif chat_type == 'Group':
            return f"group_{identifier}"
        return None
    
    def get_or_create_chat_history(self, chat_id):
        """Get or create chat history (thread-safe)"""
        with self.history_lock:
            if chat_id not in self.chat_histories:
                self.chat_histories[chat_id] = QTextDocument()
            return self.chat_histories[chat_id]
    
    def add_message_to_chat(self, chat_id, sender, message, is_me=False):
        """Add message to specified chat history (thread-safe)"""
        def _add_message():
            with self.history_lock:
                document = self.get_or_create_chat_history(chat_id)
                cursor = QTextCursor(document)
                cursor.movePosition(QTextCursor.MoveOperation.End)
                cursor.insertBlock()
                
                # Set alignment
                block_fmt = QTextBlockFormat()
                block_fmt.setAlignment(Qt.AlignmentFlag.AlignRight if is_me else Qt.AlignmentFlag.AlignLeft)
                cursor.setBlockFormat(block_fmt)
                
                # Insert message content
                name = "Me" if is_me else sender
                timestamp = datetime.datetime.now().strftime('%H:%M')
                cursor.insertHtml(f"<b>{name}</b> <span style='color: #666; font-size: 10px;'>{timestamp}</span><br>{message}")
                cursor.insertBlock()
                
                # 如果是当前活动聊天，发送更新信号
                if chat_id == self.current_chat_id:
                    self.switch_signal.update_current_chat.emit(document)
        
        # 使用线程池异步添加消息
        self.thread_pool.submit(_add_message)
    
    def switch_to_chat(self, chat_browser, chat_id):
        """Switch to a specific chat and load its history.
        Args:
            chat_browser: The QTextBrowser widget to update.
            chat_id: The ID of the chat to switch to.
        """
        def _switch_chat():
            with self.history_lock:
                if chat_id != self.current_chat_id:
                    self.current_chat_id = chat_id
                    document = self.get_or_create_chat_history(chat_id)
                    # 发送切换信号到UI线程
                    self.switch_signal.switch_chat.emit(chat_browser, document)
        
        # 使用线程池异步切换聊天
        self.thread_pool.submit(_switch_chat)

# 聊天切换信号类
class ChatSwitchSignal(QObject):
    """Chat switch signal class for inter-thread communication"""
    switch_chat = Signal(object, object)  # (chat_browser, document)
    update_current_chat = Signal(object)  # (document)

# Signal class for communication between UI thread and worker thread
class MySignals(QObject):
    """
    Client cross-thread communication signal class
    
    Provides various signals for safely updating UI components between different threads.
    
    Attributes:
        text_print (Signal): Signal for printing text in QTextEdit
        subWin_print (Signal): Signal for printing text in QPlainTextEdit
        hint1_print (Signal): Signal for printing text in hint text box
        add_tree_user (Signal): Signal for adding user to user tree
        nameofchatLabel (Signal): Signal for updating chat label name
        chatMainWindow (Signal): Signal for updating main chat window
        add_group_to_tree (Signal): Signal for adding group to tree widget
        show_reminder_popup (Signal): Signal for showing reminder popup
        show_group_invite (Signal): Signal for showing group invite popup
    """
    # Different UI components and string content signals
    text_print = Signal(object, str)
    subWin_print = Signal(object, str)
    hint1_print = Signal(object, str)
    add_tree_user = Signal(str, str)
    nameofchatLabel = Signal(object, str)
    chatMainWindow = Signal(str, str, bool)
    add_group_to_tree = Signal(str, str, str)  # (group_name, my_userid, my_serverid)
    show_reminder_popup = Signal(str)  # Show reminder popup signal
    show_group_invite = Signal(str, str, int)  # Show group invite popup signal (group_id, server_id, handle)
    add_message_to_chat_signal = Signal(str, str, str, bool)  # New: safely add message to chat window (chat_id, sender, message, is_me)
    close_dialog_signal = Signal(str)  # New: safely close dialog signal

# 全局信号对象
global_signal = MySignals()

# 当前客户端用户信息
user = Message_pb2.User()

user.userId =  'User 0'
user.serverId = 'Server_4'
udp_port = 9999

# 主界面与业务逻辑类
class Stats:
    """
    客户端主界面控制类
    
    负责管理客户端的图形用户界面和业务逻辑，包括：
    - UI界面的初始化和事件处理
    - 消息发送和接收
    - 群组管理
    - 用户管理
    - 提醒功能
    - 翻译功能
    
    Attributes:
        ui (QWidget): 主界面UI对象
        dialog1-4 (QWidget): 各种对话框UI对象
        tcp_socket (socket): TCP连接套接字
        socketManager (Socketmanager): 网络连接管理器
        reminder_dialog (QWidget): 提醒对话框
    """

    def __init__(self):
        # 使用现代化主界面
        from client.gui.modern_main_window import ModernMainWindow
        self.ui = ModernMainWindow()

        # 使用现代化对话框
        from client.gui.modern_dialogs import (ModernConnectToServerDialog, ModernAddDialog,
                                               ModernModifyGroupDialog, ModernInvitePopUpDialog)

        self.dialog1 = ModernConnectToServerDialog()
        self.dialog2 = ModernAddDialog()
        self.dialog3 = ModernModifyGroupDialog()
        self.dialog4 = ModernInvitePopUpDialog()
        
        # 初始化聊天历史管理器
        self.chat_history_manager = ChatHistoryManager()
        
        # 连接聊天切换信号
        self.chat_history_manager.switch_signal.switch_chat.connect(self._handle_chat_switch)
        self.chat_history_manager.switch_signal.update_current_chat.connect(self._handle_chat_update)
        
        # 设置窗口标题为当前用户名
        self.ui.setWindowTitle(user.userId)

        # 绑定按钮事件
        self.ui.SendButton.clicked.connect(self.handleSendButton)
        self.ui.ClientConnectButton.clicked.connect(self.ConnectToServer)
        self.ui.ADDButton.clicked.connect(self.add_users)
        self.ui.GroupButton.clicked.connect(self.handleGroupButton)
        self.ui.ReminderButton.clicked.connect(self.handleReminderButton)
        self.ui.TestTrans.clicked.connect(self.handleTestTransButton)

        # 服务器列表与套接字管理器
        self.ServerList = {}
        self.tcp_socket = None
        self.Socketm = Socketmanager(self.dialog1, self.ServerList, self.tcp_socket,
                                     self.dialog2, self.ui, self.dialog3, self.dialog4)
        # 将聊天历史管理器传递给Socketmanager
        self.Socketm.chat_history_manager = self.chat_history_manager

        # 用户/群组树事件绑定
        self.ui.UserGroupTree.itemSelectionChanged.connect(self.on_chat_target_changed)
        self.ui.UserGroupTree.itemSelectionChanged.connect(self.update_group_button_status)

        # 绑定全局信号到界面
        self.signal = global_signal
        self.signal.nameofchatLabel.connect(self.printToLabel)
        self.signal.show_reminder_popup.connect(self.show_reminder_popup)
        self.signal.show_group_invite.connect(self.show_group_invite_popup)

        # 加载提醒对话框
        self.reminder_dialog = None
        
            # 群邀请相关变量
        self.current_group_invite = None

    # 聊天切换信号处理方法
    def _handle_chat_switch(self, chat_browser, document):
        """Handle chat switching by updating the browser with the document.
        Args:
            chat_browser: The QTextBrowser widget to update.
            document: The QTextDocument to load.
        """
        chat_browser.setDocument(document)
        # 滚动到底部
        scrollbar = chat_browser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _handle_chat_update(self, document):
        """Handle chat update by refreshing the current chat display.
        Args:
            document: The QTextDocument to update with.
        """
        if self.ui.ChatMainWindow.document() == document:
            # 滚动到底部显示最新消息
            scrollbar = self.ui.ChatMainWindow.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    # 发送按钮逻辑，输入框内容显示在历史消息区，并清空输入框
    def SendButton(self, fb, text):
        """Display the input text in the chat history and clear the input box.
        Args:
            fb: The QTextEdit or similar widget to append text to.
            text: The message text to display.
        """
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        fb.append(text)
        self.ui.clear()

    # 发送消息处理逻辑
    def handleSendButton(self):
        """Handle the send button click event, send the message and clear the input box."""
        self.Socketm.send_message()
        self.ui.InputTextEdit.editer.clear()

    # 客户端连接服务器弹窗
    def ConnectToServer(self):
        """Show the connect to server dialog and bind its events."""
        self.dialog1.udpButton.clicked.connect(self.udpBoardcast)
        self.dialog1.Connect.clicked.connect(self.connect_to_server)
        self.dialog1.Disconnect.clicked.connect(self.Socketm.disconnect)
        self.dialog1.exec()

    # 刷新群聊按钮可用状态（仅选中群组时可用）
    def update_group_button_status(self):
        """Enable or disable the group button based on the current selection in the user/group tree."""
        item = self.ui.UserGroupTree.currentItem()
        if item and item.data(0, Qt.UserRole)[0] == 'Group':
            self.ui.GroupButton.setEnabled(True)
        else:
            self.ui.GroupButton.setEnabled(False)

    # 群聊按钮处理（弹出管理群窗口）
    def handleGroupButton(self):
        """Show the group management dialog for the selected group and bind its events."""
        self.dialog3.LeaveButton.clicked.connect(self.Socketm.leave_group)
        self.dialog3.InviteButton.clicked.connect(self.Socketm.invite_group)
        item = self.ui.UserGroupTree.currentItem()
        if item and item.data(0, Qt.UserRole)[0] == 'Group':
            group_id = item.data(0, Qt.UserRole)[1]
            self.dialog3.GroupName.setText(group_id)  # 设定群名称
            self.dialog3.show()

    # UDP 广播发现服务器
    def udpBoardcast(self):
        """Clear the server table and start UDP broadcast to discover servers."""
        self.dialog1.ServerTable.setRowCount(0)
        self.Socketm.UDPBoard()

    # 建立 TCP 连接
    def connect_to_server(self):
        """Start a new thread to connect to the selected server via TCP."""
        Thread(target=self.Socketm.TCPConnect, daemon=True).start()

    # 处理TestTrans按钮，发送TRANSLATE测试消息
    def handleTestTransButton(self):
        """Send a test TRANSLATE message to the server for translation functionality testing."""
        if self.Socketm.connected and self.Socketm.tcp_socket:
            # 创建TRANSLATE消息
            translate_msg = Message_pb2.Translate()
            translate_msg.target_language = 1  # EN = 1
            translate_msg.original_text = "这是一个用来测试翻译功能的消息"
            # 不设置translated_text字段
            
            # 序列化并发送
            data = translate_msg.SerializeToString()
            fullmsg = Packing('TRANSLATE', data)
            self.Socketm.tcp_socket.send(fullmsg)
            
            # print("[Client] 发送TRANSLATE测试消息")  # 注释掉，减少控制台输出
        else:
            # print("[Client] 未连接到服务器，无法发送TRANSLATE消息")  # 注释掉，减少控制台输出
            pass

    # 添加用户/群组弹窗
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
        self.dialog2.AddButton1.clicked.disconnect(self.Socketm.search_users)
        self.dialog2.UserGroup.currentIndexChanged.connect(self._onUserGroupChanged)
        self.dialog2.createButton1.clicked.connect(self.Socketm.handle_create_group)
        self.dialog2.show()

    def _onUserGroupChanged(self, index):
        """Handle user/group selection change in the combo box.
        Args:
            index: The selected index in the combo box.
        """
        # 切换“添加”按钮逻辑：User 调用 search_users，Group 调用 list group members
        kind = self.dialog2.UserGroup.currentText()
        self.dialog2.AddButton1.clicked.disconnect()
        if kind == 'User':
            self.dialog2.AddButton1.clicked.connect(self.Socketm.search_users)
            self.dialog2.createButton1.setEnabled(False)
        else:  # Group
            self.dialog2.AddButton1.clicked.connect(self.Socketm.query_group_members)
            self.dialog2.createButton1.setEnabled(True)

    # 切换聊天对象（用户或群组），更新聊天栏和标签
    def on_chat_target_changed(self):
        """Update the chat label and switch chat window when the chat target changes."""
        item = self.ui.UserGroupTree.currentItem()
        if item:
            selectUser = item.text(0)
            self.signal.nameofchatLabel.emit(self.ui.NameOfChat, selectUser)
            user_data = item.data(0, Qt.UserRole)
            if user_data and len(user_data) >= 2:
                chat_type = user_data[0]
                identifier = user_data[1]
                server_id = user_data[2] if len(user_data) > 2 else None
                
                # 生成聊天ID
                if chat_type == 'User':
                    chat_id = f"user_{identifier}_{server_id}"
                elif chat_type == 'Group':
                    chat_id = f"group_{identifier}"
                else:
                    return
                
                # 切换到对应的聊天窗口
                self.Socketm.switch_chat_window(chat_id)
            
            # 获取聊天对象信息
            user_data = item.data(0, Qt.UserRole)
            if user_data and len(user_data) >= 2:
                chat_type = user_data[0]  # 'User' 或 'Group'
                identifier = user_data[1]  # user_id 或 group_id
                server_id = user_data[2] if len(user_data) > 2 else None
                
                # 生成聊天ID并切换到对应的聊天历史
                chat_id = self.chat_history_manager.get_chat_id(chat_type, identifier, server_id)
                if chat_id:
                    self.chat_history_manager.switch_to_chat(self.ui.ChatMainWindow, chat_id)

    # 聊天窗口名称标签显示
    def printToLabel(self, fb, selectUser):
        """Set the chat label to the selected user or group name.
        Args:
            fb: The QLabel to update.
            selectUser: The name to display.
        """
        fb.setText(selectUser)

    # 提醒按钮处理
    def handleReminderButton(self):
        """Show the reminder dialog and bind its set button event."""
        if self.reminder_dialog is None:
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            ui_path = os.path.join(current_dir, 'ui', 'reminder.ui')
            self.reminder_dialog = uiLoader.load(ui_path)
            self.reminder_dialog.setButton.clicked.connect(self.handleSetReminder)
        self.reminder_dialog.show()

    # 设置提醒处理
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
        
        # 发送SET_REMINDER消息到服务器
        self.Socketm.send_set_reminder(event_name, countdown_seconds)
        
        # 清空输入框并关闭对话框
        self.reminder_dialog.Eventname.clear()
        self.reminder_dialog.Time.clear()
        self.reminder_dialog.close()

    # 显示提醒弹窗
    def show_reminder_popup(self, message):
        """Display a reminder popup with the given message.
        Args:
            message: The reminder message to display.
        """
        # print("show_reminder_popup函数")  # 注释掉，减少控制台输出
        tip = TipsWidget(self.ui)
        tip.setText(f"提醒|{message}")
        tip.status = TipsStatus.Succeed
        tip.move(200, 100)
        tip.resize(420, 35)
        tip.show()

    # 显示群邀请弹窗
    def show_group_invite_popup(self, group_id, server_id, handle):
        """Show the group invite popup dialog and bind its accept/reject events.
        Args:
            group_id: The group ID for the invite.
            server_id: The server ID for the invite.
            handle: The handle for the invite event.
        """
        self.current_group_invite = (group_id, server_id, handle)
        self.dialog4.InviteText.setText(f"你被邀请加入群组：{group_id}，是否接受？")
        
        # 先断开之前的连接，避免重复绑定
        try:
            self.dialog4.YesButton.clicked.disconnect()
            self.dialog4.NoButton.clicked.disconnect()
        except:
            pass  # 如果没有连接则忽略
            
        self.dialog4.YesButton.clicked.connect(self.accept_group_invite)
        self.dialog4.NoButton.clicked.connect(self.reject_group_invite)
        self.dialog4.show()  # 使用show()代替exec()避免阻塞

    # 接受群邀请
    def accept_group_invite(self):
        """Accept the current group invite and send a request to the server."""
        if self.current_group_invite:
            group_id, server_id, handle = self.current_group_invite
            req = Message_pb2.ListGroupMembers()
            req.group.groupId = group_id
            req.group.serverId = server_id
            if self.Socketm.tcp_socket:
                self.Socketm.tcp_socket.send(Packing('QUERY_GROUP_MEMBERS', req.SerializeToString()))
            self.dialog4.hide()  # 隐藏弹窗
            self.current_group_invite = None  # 清空当前邀请信息

    # 拒绝群邀请
    def reject_group_invite(self):
        """Reject the current group invite and close the dialog."""
        self.dialog4.hide()  # 隐藏弹窗
        self.current_group_invite = None  # 清空当前邀请信息
    
    def close_dialog_safely(self, dialog_name):
        """Safely close a dialog by name.
        Args:
            dialog_name: The name of the dialog to close.
        """
        if dialog_name == "dialog2":
            self.dialog2.close()
        elif dialog_name == "dialog3":
            self.dialog3.close()
        elif dialog_name == "dialog4":
            self.dialog4.close()





# 套接字及消息处理主类
class Socketmanager:
    """
    Network connection management class
    
    Manages network communication (TCP/UDP) and handles message sending/receiving.
    
    Attributes:
        dialog1 (QWidget): Reference to the connect to server dialog.
        dialog2 (QWidget): Reference to the add user/group dialog.
        dialog3 (QWidget): Reference to the modify group dialog.
        dialog4 (QWidget): Reference to the invite popup dialog.
        ui (QWidget): Reference to the main UI window.
        Serverlist (dict): Dictionary to store server information.
        udp_socket (socket): UDP socket for discovery.
        tcp_socket (socket): TCP socket for communication.
        connected (bool): Connection status.
        recv_thread (Thread): Thread for receiving messages.
        heartbeat_thread (Thread): Thread for sending heartbeats.
        last_active_time (float): Timestamp of the last activity.
        heartbeat_interval (int): Heartbeat interval in seconds.
        heartbeat_timeout (int): Heartbeat timeout in seconds.
        search_users_unit64id (int): Handle for searching users.
        chat_history_manager (ChatHistoryManager): Reference to the chat history manager.
    """
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
        self.last_active_time = 0  # 上次活动时间
        self.heartbeat_interval = 10  # 心跳间隔
        self.heartbeat_timeout = 30   # 超时时长
        self.search_users_unit64id = None
        self.chat_history_manager = None  # 聊天历史管理器，稍后由外部设置

        # 各类信号与 UI 控件绑定
        self.signals = MySignals()
        self.signals.subWin_print.connect(self.update_subWin)
        self.signals.hint1_print.connect(self.update_Hint1)
        self.signals.add_tree_user.connect(self.add_user_to_tree)
        self.signals.chatMainWindow.connect(self.update_ChatMainWindow)
        self.signals.add_group_to_tree.connect(self.add_group_to_tree)
        self.signals.close_dialog_signal.connect(global_signal.close_dialog_signal.emit)

        # 聊天窗口管理
        self.chat_browsers = {}  # 存储每个聊天对象的QTextBrowser: {chat_id: QTextBrowser}
        self.current_chat_id = None  # 当前选中的聊天对象ID
        
        # 未读消息管理
        self.unread_counts = {}  # 存储每个聊天对象的未读消息数量: {chat_id: count}

    # 更新子窗口内容
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
    
    # 增加未读消息计数
    def increment_unread_count(self, chat_id):
        """Increment unread message count for a specified chat object.
        Args:
            chat_id: The ID of the chat object.
        """
        if chat_id not in self.unread_counts:
            self.unread_counts[chat_id] = 0
        self.unread_counts[chat_id] += 1
        self.update_tree_display(chat_id)
    
    # 清除未读消息计数
    def clear_unread_count(self, chat_id):
        """Clear unread message count for a specified chat object.
        Args:
            chat_id: The ID of the chat object.
        """
        if chat_id in self.unread_counts:
            self.unread_counts[chat_id] = 0
            self.update_tree_display(chat_id)
    
    # 更新树形控件显示
    def update_tree_display(self, chat_id):
        """Update the display text of a specified chat object in the tree widget.
        Args:
            chat_id: The ID of the chat object to update.
        """
        root = self.ui.UserGroupTree.invisibleRootItem()
        
        # 首先查找所有顶级项目（私聊用户或群组）
        for i in range(root.childCount()):
            item = root.child(i)
            item_data = item.data(0, Qt.UserRole)
            if item_data and len(item_data) >= 2:
                if item_data[1] == chat_id:  # 找到匹配的聊天对象
                    self._update_item_text(item, chat_id)
                    return
        
        # 如果在顶级项目中没找到，再查找群组中的成员
        for i in range(root.childCount()):
            item = root.child(i)
            # 检查群组中的成员
            for j in range(item.childCount()):
                child = item.child(j)
                child_data = child.data(0, Qt.UserRole)
                if child_data and len(child_data) >= 2 and child_data[1] == chat_id:
                    self._update_item_text(child, chat_id)
                    return
    
    # 更新单个项目的文本显示
    def _update_item_text(self, item, chat_id):
        """Update text display for a single tree widget item.
        Args:
            item: The tree widget item to update.
            chat_id: The ID of the chat object.
        """
        item_data = item.data(0, Qt.UserRole)
        if not item_data or len(item_data) < 2:
            return
        
        base_name = item_data[1]  # 用户ID或群组ID
        unread_count = self.unread_counts.get(chat_id, 0)
        
        if unread_count > 0:
            # 限制显示的最大数字，超过99显示99+
            display_count = "99+" if unread_count > 99 else str(unread_count)
            
            # 统一使用红色圆圈+数字的样式
            badge = f"🔴{display_count}"
            
            display_text = f"{base_name}  {badge}"
        else:
            display_text = base_name
        
        # 始终保持白色字体（适配深色主题）
        from PySide6.QtGui import QBrush, QColor
        item.setForeground(0, QBrush(QColor(255, 255, 255)))  # 白色字体
        
        item.setText(0, display_text)

    # 获取或创建聊天窗口
    def get_or_create_chat_browser(self, chat_id):
        """Get or create a QTextBrowser for a specified chat object.
        Args:
            chat_id: The ID of the chat object.
        Returns:
            QTextBrowser: The chat browser widget.
        """
        if chat_id not in self.chat_browsers:
            # 创建新的QTextBrowser
            browser = QTextBrowser()
            browser.setReadOnly(True)
            
            # 添加到StackedWidget中
            self.ui.ChatMainWindow.addWidget(browser)
            self.chat_browsers[chat_id] = browser
            
            print(f"[Client] 为聊天对象 {chat_id} 创建新的聊天窗口")
        
        return self.chat_browsers[chat_id]
    
    # 切换聊天窗口
    def switch_chat_window(self, chat_id):
        """Switch to the window of a specified chat object.
        Args:
            chat_id: The ID of the chat object to switch to.
        """
        if chat_id == self.current_chat_id:
            return  # 已经是当前窗口，无需切换
        
        browser = self.get_or_create_chat_browser(chat_id)
        self.ui.ChatMainWindow.setCurrentWidget(browser)
        self.current_chat_id = chat_id
        
        # 清除该聊天对象的未读消息计数
        self.clear_unread_count(chat_id)
        
        print(f"[Client] 切换到聊天对象 {chat_id} 的窗口")
    
    # 向指定聊天窗口添加消息
    def add_message_to_chat(self, chat_id, sender, message, is_me=False):
        """Add message to the window of a specified chat object.
        Args:
            chat_id: The ID of the chat object.
            sender: The sender of the message.
            message: The message content.
            is_me: Whether the message is sent by the current user.
        """
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

        # 自动滚动到底部
        browser.setTextCursor(cursor)
        browser.ensureCursorVisible()

        # 未读消息处理：如果不是自己发的消息且不是当前聊天窗口，增加未读计数
        if not is_me and chat_id != self.current_chat_id:
            self.increment_unread_count(chat_id)

    # 添加用户到左侧树
    def add_user_to_tree(self, user_id, server_id):
        """Add a user to the left tree widget.
        Args:
            user_id: The user ID to add.
            server_id: The server ID of the user.
        """
        root = self.ui.UserGroupTree.invisibleRootItem()
        for i in range(root.childCount()):
            if root.child(i).text(0) == user_id:
                return
        userItem = QTreeWidgetItem()
        userItem.setText(0, user_id)
        userItem.setData(0, Qt.UserRole, ['User', user_id, server_id])
        root.addChild(userItem)

    # 聊天窗口更新显示
    def update_ChatMainWindow(self, sender, message, is_me=False):
        """Update the chat main window with a new message.
        Args:
            sender: The sender of the message.
            message: The message content.
            is_me: Whether the message is sent by the current user.
        """
        # 检查聊天历史管理器是否存在
        if not self.chat_history_manager:
            return
            
        # 获取当前聊天对象
        current_item = self.ui.UserGroupTree.currentItem()
        if current_item:
            user_data = current_item.data(0, Qt.UserRole)
            if user_data and len(user_data) >= 2:
                chat_type = user_data[0]
                identifier = user_data[1]
                server_id = user_data[2] if len(user_data) > 2 else None
                
                # 生成聊天ID
                chat_id = self.chat_history_manager.get_chat_id(chat_type, identifier, server_id)
                if chat_id:
                    # 添加消息到对应的聊天历史
                    self.chat_history_manager.add_message_to_chat(chat_id, sender, message, is_me)
                    
                    # 如果是当前活动的聊天，刷新显示
                    if chat_id == self.chat_history_manager.current_chat_id:
                        # 滚动到底部显示最新消息
                        scrollbar = self.ui.ChatMainWindow.verticalScrollBar()
                        scrollbar.setValue(scrollbar.maximum())

    # 添加群组到树（含自己为首个成员）
    def add_group_to_tree(self, group_name, my_userid, my_serverid):
        """Add a group to the tree widget with the current user as the first member.
        Args:
            group_name: The name of the group to add.
            my_userid: The current user's ID.
            my_serverid: The current user's server ID.
        """
        root = self.ui.UserGroupTree.invisibleRootItem()
        groupItem = QTreeWidgetItem()
        groupItem.setText(0, group_name)
        groupItem.setData(0, Qt.UserRole, ['Group', group_name])
        root.addChild(groupItem)
        userItem = QTreeWidgetItem(groupItem)
        userItem.setText(0, my_userid)
        userItem.setData(0, Qt.UserRole, ['User', my_userid, my_serverid])
        groupItem.addChild(userItem)
        groupItem.setExpanded(True)

    def query_group_members(self):
        """Query group members from the server based on input box content."""
        # 根据输入框内容，向服务器请求群成员列表
        group_id = self.dialog2.printId.text()
        if not group_id:
            self.signals.hint1_print.emit(self.dialog2.Hint1, "请输入群组ID")
            return
        req = Message_pb2.QueryGroupMembers()
        req.group.groupId = group_id
        req.group.serverId = user.serverId
        self.tcp_socket.send(Packing('QUERY_GROUP_MEMBERS', req.SerializeToString()))


    # UDP 广播方式发现服务器
    def UDPBoard(self):
        """Perform UDP broadcast to discover servers on the network."""
        self.dialog1.ServerTable.setRowCount(0)
        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.udp_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.udp_socket.settimeout(1)  # 增加超时时间
        
        # 尝试多个广播地址
        broadcast_addrs = [
            '255.255.255.255',  # 全局广播
        ]

        DiscoverServer = Message_pb2.DiscoverServer()
        data = DiscoverServer.SerializeToString()
        fullmsg = Packing('DISCOVER_SERVER', data)
        
        # 向所有广播地址发送
        servers_found = False
        for broadcast_addr in broadcast_addrs:
            try:
                BoardcastAddr = (broadcast_addr, udp_port)
                self.udp_socket.sendto(fullmsg, BoardcastAddr)
                # print(f"[Client] sendto {broadcast_addr}:{udp_port} a DISCOVER_SERVER")  # 注释掉，减少控制台输出
                
                # 尝试接收响应
                try:
                    resp, server_addr = self.udp_socket.recvfrom(2048)
                    purpose, length, payload = Unpacking(resp)
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
                        # print(f"[Client] 从 {server_addr} 收到服务器响应")  # 注释掉，减少控制台输出
                        break  # 找到服务器就停止
                except TimeoutError:
                    continue  # 继续尝试下一个广播地址
            except Exception as e:
                # print(f"[Client] 向 {broadcast_addr} 广播失败: {e}")  # 注释掉，减少控制台输出
                continue
        
        if not servers_found:
            self.dialog1.Hint.setPlainText('Server not found-->Timeout!!!')
        
        time.sleep(0.1)
        self.udp_socket.close()

    # 断开 TCP 连接
    def close_connection(self):
        """Close the TCP connection and clean up resources."""
        if self.tcp_socket:
            try:
                self.tcp_socket.close()
            except Exception as e:
                # print("[Client] Socket close error:", e)  # 注释掉，减少控制台输出
                pass
            self.tcp_socket = None
        self.connected = False


    # 建立 TCP 连接，负责发送连接请求，启动接收/心跳线程
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
            # print("[Client] Opening new TCP socket")  # 注释掉，减少控制台输出
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

    # 心跳线程，定时检测连接状态与活跃性
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
                # print("[Client] Sent PING")  # 注释掉，减少控制台输出
            except Exception as e:
                # print("[Client] Heartbeat send error:", e)  # 注释掉，减少控制台输出
                self.close_connection()
                break

    # TCP消息主接收线程，处理所有收到的协议包
    def recv_loop(self):
        """TCP message main receive thread that processes all received protocol packets."""
        while self.connected and self.tcp_socket:
            data = self.tcp_socket.recv(2048)
            if not data:
                self.signals.subWin_print.emit(self.dialog1.Hint, "Disconnected by server.")
                self.close_connection()
                break
            self.last_active_time = time.time()
            purpose, length, payload = Unpacking(data)
            # print("[Client] Purpose:", purpose)  # 注释掉，减少控制台输出
            # 根据不同 purpose 处理不同协议包
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
                # print("[Client] Received PING, sent PONG")  # 注释掉，减少控制台输出
            elif purpose == 'PONG':
                # print("[Client] Received PONG (heartbeat ok)")  # 注释掉，减少控制台输出
                pass

            elif purpose == 'SEARCH_USERS_RESP':
                QueryUserResponse = Message_pb2.QueryUsersResponse()
                QueryUserResponse.ParseFromString(payload)
                if self.search_users_unit64id != QueryUserResponse.handle:
                    # print(self.search_users_unit64id)  # 注释掉，减少控制台输出
                    pass
                else:
                    user_names = '\n'.join(user.userId for user in QueryUserResponse.users)
                    self.signals.hint1_print.emit(self.dialog2.Hint1, user_names)
                    input_userid = self.dialog2.printId.text()
                    if input_userid in [user.userId for user in QueryUserResponse.users]:
                        # print('有')  # 注释掉，减少控制台输出
                        server_id = next(user.serverId for user in QueryUserResponse.users if user.userId == input_userid)
                        self.signals.add_tree_user.emit(input_userid, server_id)

            elif purpose == 'MESSAGE':
                chat_msg = Message_pb2.ChatMessage()
                chat_msg.ParseFromString(payload)
                recipient_type = chat_msg.WhichOneof('recipient')
                is_me = (chat_msg.author.userId == user.userId)
                sender = chat_msg.author.userId
                sender_server = chat_msg.author.serverId
                
                # 根据消息内容类型获取显示文本
                content_type = chat_msg.WhichOneof('content')
                if content_type == 'textContent':
                    # 普通文本消息
                    msg_text = chat_msg.textContent
                elif content_type == 'translation':
                    # 翻译消息，显示翻译后的内容
                    if chat_msg.translation.translated_text:
                        msg_text = chat_msg.translation.translated_text
                    else:
                        # 如果没有翻译结果，显示原文
                        msg_text = chat_msg.translation.original_text
                else:
                    # 其他类型消息，暂时跳过
                    return

                if chat_msg.author.userId == user.userId:
                    return  # 忽略自己发的回显

                if recipient_type == 'user':
                    # 首先将发送者添加到用户树（如果不存在的话）
                    self.signals.add_tree_user.emit(sender, sender_server)
                    
                    # 将消息添加到对应的聊天窗口中
                    chat_id = f"user_{sender}_{sender_server}"
                    self.add_message_to_chat(chat_id, sender, msg_text, is_me)
                    
                    # 回送达 ACK 给服务器
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
                    
                    # 将消息添加到群组聊天窗口中
                    chat_id = f"group_{group_id}"
                    self.add_message_to_chat(chat_id, sender, msg_text, is_me)
                    # 也需要ACK
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
                    # print("收信人", status.user.userId, "投递状态：", status.status)  # 注释掉，减少控制台输出
                    pass


            elif purpose == "MODIFY_GROUP_RESP":
                resp = Message_pb2.ModifyGroupResponse()
                resp.ParseFromString(payload)
                if resp.result == Message_pb2.ModifyGroupResponse.SUCCESS:
                    group_name = self.pending_create_group_name
                    # 自动更新左侧树
                    self.signals.add_group_to_tree.emit(group_name, user.userId, user.serverId)
                    # 关闭对话框
                    global_signal.close_dialog_signal.emit("dialog2")
                else:
                    msg = ("服务器拒绝建群" if resp.result == Message_pb2.ModifyGroupResponse.NOT_PERMITTED
                           else "建群失败")
                    self.signals.hint1_print.emit(self.dialog2.Hint1, msg)
                    # 恢复按钮可用
                    self.dialog2.createButton1.setEnabled(True)

            elif purpose == 'NOTIFY_GROUP_INVITE':
                notify = Message_pb2.NotifyGroupInvite()
                notify.ParseFromString(payload)
                group_id = notify.group.groupId
                server_id = notify.group.serverId
                handle = notify.handle

                # 使用信号在主线程中显示群邀请弹窗
                global_signal.show_group_invite.emit(group_id, server_id, handle)


            elif purpose == 'GROUP_MEMBERS':
                group_members = Message_pb2.GroupMembers()
                group_members.ParseFromString(payload)
                group_id = group_members.group.groupId
                root = self.ui.UserGroupTree.invisibleRootItem()

                # 先尝试找到现有群组节点
                groupItem = None

                for i in range(root.childCount()):
                    child = root.child(i)
                    data = child.data(0, Qt.UserRole)
                    if data and data[0] == 'Group' and data[1] == group_id:
                        groupItem = child
                        groupItem.takeChildren()  # 清空旧成员
                        break

                if not groupItem:
                    groupItem = QTreeWidgetItem()
                    groupItem.setText(0, group_id)
                    groupItem.setData(0, Qt.UserRole, ['Group', group_id])
                    root.addChild(groupItem)

                # 添加新成员
                for m in group_members.user:
                    userItem = QTreeWidgetItem(groupItem)
                    userItem.setText(0, m.userId)
                    userItem.setData(0, Qt.UserRole, ['User', m.userId, m.serverId])

                groupItem.setExpanded(True)

                # 自动加入群并关闭对话框
                join = Message_pb2.JoinGroup()
                join.group.groupId = group_id
                join.group.serverId = user.serverId
                join.user.userId = user.userId
                join.user.serverId = user.serverId
                self.tcp_socket.send(Packing('JOIN_GROUP', join.SerializeToString()))
                # 成功后关闭“添加用户/群”对话框
                global_signal.close_dialog_signal.emit("dialog2")

            elif purpose == 'REMINDER':
                try:
                    reminder = Message_pb2.Reminder()
                    reminder.ParseFromString(payload)

                    event = reminder.reminderContent
                    message = f"您设置的事件 '{event}' 时间到了！"
                    
                    # 发送信号显示提醒弹窗
                    # print('test 111')  # 注释掉，减少控制台输出
                    global_signal.show_reminder_popup.emit(message)
                    
                except Exception as e:
                    # print(f"[Client] REMINDER error: {e}")  # 注释掉，减少控制台输出
                    pass

            else:
                # 处理其他未知消息
                # print(f"[Client] 收到未处理消息: {purpose}")  # 注释掉，减少控制台输出
                pass

    # 主动断开连接
    def disconnect(self):
        """Initiate disconnection from the server."""
        self.signals.subWin_print.emit(self.dialog1.Hint, "Disconnected.")
        self.close_connection()

    # 搜索用户，向服务器请求用户列表
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

    # 发送消息到当前选中的用户/群
    def send_message(self):
        """Send a message to the currently selected user or group."""
        item = self.ui.UserGroupTree.currentItem()
        node_type = item.data(0, Qt.UserRole)[0]
        msg = Message_pb2.ChatMessage()
        msg.messageSnowflake = int(time.time())
        msg.author.userId = user.userId
        msg.author.serverId = user.serverId
        
        # 获取用户输入的原文
        original_text = self.ui.toPlainText()
        
        # 获取选择的语言
        selected_language = self.ui.TransComboBox.currentText()
        
        if selected_language == "Original":
            # 发送普通文本消息
            msg.textContent = original_text
            display_text = original_text
        else:
            # 发送翻译消息
            msg.translation.original_text = original_text
            
            # 设置目标语言
            language_map = {
                'Deutsch': 0,   # DE
                'English': 1,   # EN
                '中文': 2,  # ZH
                'Türkçe': 3
            }
            msg.translation.target_language = language_map.get(selected_language, 1)
            
            # 本地显示翻译后的内容
            from modules.Translator import translator
            display_text = translator(original_text, selected_language)
        
        # 设置接收者
        if node_type == 'User':
            msg.user.userId = item.data(0, Qt.UserRole)[1]
            msg.user.serverId = item.data(0, Qt.UserRole)[2]
        elif node_type == 'Group':
            msg.group.groupId = item.data(0, Qt.UserRole)[1]
        else:
            return
        
        # 发送消息到服务器
        data = msg.SerializeToString()
        tosend = Packing('MESSAGE', data)
        self.tcp_socket.send(tosend)
        
        # 将消息添加到对应的聊天历史中
        if node_type == 'User':
            chat_id = self.chat_history_manager.get_chat_id('User', item.data(0, Qt.UserRole)[1], item.data(0, Qt.UserRole)[2])
        elif node_type == 'Group':
            chat_id = self.chat_history_manager.get_chat_id('Group', item.data(0, Qt.UserRole)[1])
        else:
            return
            
        if chat_id:
            self.chat_history_manager.add_message_to_chat(chat_id, user.userId, display_text, True)
            # 找到当前页
            browser = self.ui.ChatMainWindow.currentWidget()
            # 只有当它是 QTextBrowser 时才调用
            if isinstance(browser, QTextBrowser):
                browser.moveCursor(QTextCursor.End)

    # 向服务器发起建群请求
    def handle_create_group(self):
        """Send a group creation request to the server."""
        group_name = self.dialog2.printId.text()
        if not group_name:
            self.signals.hint1_print.emit(self.dialog2.Hint1, "请输入群名！")
            return
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
        self.signals.hint1_print.emit(self.dialog2.Hint1, f"已向服务器发送建群请求：{group_name}")
        self.pending_create_group_name = group_name

    # 离开当前群聊
    def leave_group(self):
        """Leave the current group chat and clean up related resources."""
        leave = Message_pb2.LeaveGroup()
        leave.group.groupId = self.dialog3.GroupName.text()
        leave.group.serverId = user.serverId
        leave.user.userId = user.userId
        leave.user.serverId = user.serverId
        self.tcp_socket.send(Packing('LEAVE_GROUP', leave.SerializeToString()))
        self.dialog3.close()
        root = self.ui.UserGroupTree.invisibleRootItem()
        for i in range(root.childCount()):
            child = root.child(i)
            if child.data(0, Qt.UserRole)[0] == 'Group' and child.data(0, Qt.UserRole)[1] == leave.group.groupId:
                root.removeChild(child)
                break

    # 邀请其他用户进群
    def invite_group(self):
        """Invite other users to join the current group."""
        invite = Message_pb2.InviteToGroup()
        invite.handle = int(time.time())
        invite.user.userId = self.dialog3.lineEdit.text()
        invite.user.serverId = user.serverId
        invite.groupId = self.dialog3.GroupName.text()
        self.tcp_socket.send(Packing('INVITE_GROUP', invite.SerializeToString()))

    # 发送设置提醒消息
    def send_set_reminder(self, event_name, countdown_seconds):
        """Send a set reminder message to the server.
        Args:
            event_name: The name of the reminder event.
            countdown_seconds: The countdown time in seconds.
        """
        if not self.tcp_socket:
            return
        
        set_reminder = Message_pb2.SetReminder()
        # 用户只能给自己设置提醒，所以目标用户就是当前用户
        set_reminder.user.userId = user.userId
        set_reminder.user.serverId = user.serverId
        set_reminder.event = event_name
        set_reminder.countdownSeconds = countdown_seconds
        
        data = set_reminder.SerializeToString()
        tosend = Packing('SET_REMINDER', data)
        self.tcp_socket.send(tosend)

# 程序入口
if __name__ == '__main__':
    app = QApplication([])
    main = Stats()
    main.ui.show()
    app.exec()
