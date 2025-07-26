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
# Add project root directory to path to avoid import conflicts
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

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

user.userId = 'User 2'
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

        # 绑定全局信号到界面
        self.signal = global_signal
        self.signal.nameofchatLabel.connect(self.printToLabel)
        self.signal.show_reminder_popup.connect(self.show_reminder_popup)
        self.signal.show_group_invite.connect(self.show_group_invite_popup)
        self.signal.close_dialog_signal.connect(self.close_dialog_safely)

        # 加载提醒对话框
        self.reminder_dialog = None

        # 群邀请相关变量
        self.current_group_invite = None

    # 发送按钮逻辑，输入框内容显示在历史消息区，并清空输入框
    def SendButton(self, fb, text):
        """Display the input text in the chat history and clear the input box.
        Args:
            fb: The QTextEdit or similar widget to append text to.
            text: The message text to display.
        """
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        fb.append(text)
        self.ui.InputTextEdit.clear()

    # 发送消息处理逻辑
    def handleSendButton(self):
        """Handle the send button click event, send the message and clear the input box."""
        self.Socketm.send_message()
        self.ui.InputTextEdit.clear()

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
        self.dialog2.createButton1.clicked.connect(self.Socketm.handle_create_group)
        self.dialog2.show()

    # 切换聊天对象（用户或群组），更新聊天栏和标签
    def on_chat_target_changed(self):
        """Update the chat label and switch chat window when the chat target changes."""
        item = self.ui.UserGroupTree.currentItem()
        if item:
            # 使用data获取用户ID或群组ID，而不是text获取显示文本（可能包含未读消息标记）
            item_data = item.data(0, Qt.UserRole)
            if item_data and len(item_data) >= 2:
                chat_id = item_data[1]  # [0]类型, [1]user_id或group_id
                # 直接使用chat_id作为显示名称，避免包含未读消息标记
                self.signal.nameofchatLabel.emit(self.ui.NameOfChat, chat_id)

                # 切换到对应的聊天窗口
                self.Socketm.switch_chat_window(chat_id)

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
            self.reminder_dialog = uiLoader.load('ui/reminder.ui')
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

    # 安全关闭对话框
    def close_dialog_safely(self, dialog_name):
        """Safely close a dialog by name.
        Args:
            dialog_name: The name of the dialog to close.
        """
        if dialog_name == "add_dialog":
            self.dialog2.close()





# 套接字及消息处理主类
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
        self.last_active_time = 0  # 上次活动时间
        self.heartbeat_interval = 30  # 心跳间隔
        self.heartbeat_timeout = 90   # 超时时长
        self.search_users_unit64id = None

        # 各类信号与 UI 控件绑定
        self.signals = MySignals()
        self.signals.subWin_print.connect(self.update_subWin)
        self.signals.hint1_print.connect(self.update_Hint1)
        self.signals.add_tree_user.connect(self.add_user_to_tree)
        self.signals.chatMainWindow.connect(self.update_ChatMainWindow)
        self.signals.add_group_to_tree.connect(self.add_group_to_tree)
        self.signals.add_message_to_chat_signal.connect(self.add_message_to_chat)
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
        """增加指定聊天对象的未读消息计数"""
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
        """清除指定聊天对象的未读消息计数"""
        if chat_id in self.unread_counts:
            self.unread_counts[chat_id] = 0
            self.update_tree_display(chat_id)

    # 更新树形控件显示
    def update_tree_display(self, chat_id):
        """Update the display text of a specified chat object in the tree widget.
        Args:
            chat_id: The ID of the chat object to update.
        """
        """更新树形控件中指定聊天对象的显示文本"""
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
        """更新单个树形控件项目的文本显示"""
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
        item.setText(0, display_text)

    # 获取或创建聊天窗口
    def get_or_create_chat_browser(self, chat_id):
        """Get or create a QTextBrowser for a specified chat object.
        Args:
            chat_id: The ID of the chat object.
        Returns:
            QTextBrowser: The chat browser widget.
        """
        """获取或创建指定聊天对象的QTextBrowser"""
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
        """切换到指定聊天对象的窗口"""
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
        """向指定聊天对象的窗口添加消息"""
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

        # 检查是否已存在该用户
        for i in range(root.childCount()):
            item = root.child(i)
            item_data = item.data(0, Qt.UserRole)
            if (item_data and len(item_data) >= 2 and
                item_data[0] == 'User' and item_data[1] == user_id):
                return  # 用户已存在

        userItem = QTreeWidgetItem()
        userItem.setText(0, user_id)  # 初始显示用户ID
        userItem.setData(0, Qt.UserRole, ['User', user_id, server_id])
        root.addChild(userItem)

    # 聊天窗口更新显示（支持多窗口）
    def update_ChatMainWindow(self, sender, message, is_me=False):
        """Update the chat main window with a new message.
        Args:
            sender: The sender of the message.
            message: The message content.
            is_me: Whether the message is sent by the current user.
        """
        # 获取当前聊天对象ID
        if self.current_chat_id:
            # 使用信号安全地添加消息到聊天窗口
            self.signals.add_message_to_chat_signal.emit(self.current_chat_id, sender, message, is_me)

    # 添加群组到树（含自己为首个成员）
    def add_group_to_tree(self, group_name, my_userid, my_serverid):
        """Add a group to the tree widget with the current user as the first member.
        Args:
            group_name: The name of the group to add.
            my_userid: The current user's ID.
            my_serverid: The current user's server ID.
        """
        root = self.ui.UserGroupTree.invisibleRootItem()

        # 检查群组是否已存在
        for i in range(root.childCount()):
            child = root.child(i)
            if (child.data(0, Qt.UserRole) and
                len(child.data(0, Qt.UserRole)) >= 2 and
                child.data(0, Qt.UserRole)[0] == 'Group' and
                child.data(0, Qt.UserRole)[1] == group_name):
                print(f"[Client] 群组 {group_name} 已存在，跳过创建")
                return  # 群组已存在，直接返回

        # 创建新群组
        groupItem = QTreeWidgetItem()
        groupItem.setText(0, group_name)
        groupItem.setData(0, Qt.UserRole, ['Group', group_name])
        root.addChild(groupItem)
        userItem = QTreeWidgetItem(groupItem)
        userItem.setText(0, my_userid)
        userItem.setData(0, Qt.UserRole, ['User', my_userid, my_serverid])
        groupItem.addChild(userItem)
        groupItem.setExpanded(True)
        print(f"[Client] 成功创建群组 {group_name} 并添加到UI树")

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

                    # 使用信号安全地添加消息到发送者的聊天窗口
                    self.signals.add_message_to_chat_signal.emit(sender, sender, msg_text, is_me)

                    # 如果当前选择的正好是发送者，不需要额外操作（因为窗口已经切换到正确位置）
                    # 消息会自动显示在当前窗口中

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
                    # 使用信号安全地添加消息到群组的聊天窗口
                    self.signals.add_message_to_chat_signal.emit(group_id, sender, msg_text, False)
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
                    # 使用信号安全地关闭对话框
                    self.signals.close_dialog_signal.emit("add_dialog")
                    self.signals.add_group_to_tree.emit(group_name, user.userId, user.serverId)
                    self.signals.hint1_print.emit(self.dialog2.Hint1, f"群组 {group_name} 创建成功！")
                else:
                    msg = "服务器拒绝建群" if resp.result == Message_pb2.ModifyGroupResponse.NOT_PERMITTED else "建群失败"
                    self.signals.hint1_print.emit(self.dialog2.Hint1, msg)
                    # 重新启用创建按钮，允许重试
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

                # 查找是否已存在该群组
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
                    # 群组已存在，更新成员列表
                    # 清除现有成员（但保留群组本身）
                    while existing_group_item.childCount() > 0:
                        existing_group_item.removeChild(existing_group_item.child(0))

                    # 添加更新后的成员列表
                    for m in group_members.user:
                        userItem = QTreeWidgetItem(existing_group_item)
                        userItem.setText(0, m.userId)
                        userItem.setData(0, Qt.UserRole, ['User', m.userId, m.serverId])
                        existing_group_item.addChild(userItem)
                    existing_group_item.setExpanded(True)

                    # 记录更新日志
                    print(f"[Client] 群组 {group_id} 成员列表已更新")
                else:
                    # 群组不存在，创建新群组（这是加入新群组的情况）
                    groupItem = QTreeWidgetItem()
                    groupItem.setText(0, group_id)
                    groupItem.setData(0, Qt.UserRole, ['Group', group_id])
                    root.addChild(groupItem)

                    # 检查自己是否在成员列表中，如果不在则添加
                    member_user_ids = [m.userId for m in group_members.user]
                    if user.userId not in member_user_ids:
                        # 先添加自己
                        userItem = QTreeWidgetItem(groupItem)
                        userItem.setText(0, user.userId)
                        userItem.setData(0, Qt.UserRole, ['User', user.userId, user.serverId])
                        groupItem.addChild(userItem)

                    # 然后添加其他成员
                    for m in group_members.user:
                        userItem = QTreeWidgetItem(groupItem)
                        userItem.setText(0, m.userId)
                        userItem.setData(0, Qt.UserRole, ['User', m.userId, m.serverId])
                        groupItem.addChild(userItem)
                    groupItem.setExpanded(True)

                    # 只有在创建新群组时才发送JOIN_GROUP消息
                    join = Message_pb2.JoinGroup()
                    join.group.groupId = group_id
                    join.group.serverId = group_members.group.serverId  # 从GROUP_MEMBERS消息中获取
                    join.user.userId = user.userId
                    join.user.serverId = user.serverId
                    self.tcp_socket.send(Packing('JOIN_GROUP', join.SerializeToString()))

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
        original_text = self.ui.InputTextEdit.toPlainText()

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

        # 在对应的聊天窗口显示内容（用户看到的是翻译版本或原文）
        if node_type == 'User':
            chat_id = item.data(0, Qt.UserRole)[1]  # 用户ID
        elif node_type == 'Group':
            chat_id = item.data(0, Qt.UserRole)[1]  # 群组ID

        # 使用信号安全地添加消息到聊天窗口
        self.signals.add_message_to_chat_signal.emit(chat_id, user.userId, display_text, True)

    # 向服务器发起建群请求
    def handle_create_group(self):
        """Send a group creation request to the server."""
        group_name = self.dialog2.printId.text()
        if not group_name:
            self.signals.hint1_print.emit(self.dialog2.Hint1, "请输入群名！")
            return

        # 禁用创建按钮，防止重复点击
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
        self.signals.hint1_print.emit(self.dialog2.Hint1, f"已向服务器发送建群请求：{group_name}")
        self.pending_create_group_name = group_name

    # 离开当前群聊
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

        # 删除群组对应的聊天窗口
        if group_id in self.chat_browsers:
            browser = self.chat_browsers[group_id]
            # 如果当前正在显示这个群组的聊天窗口，切换到其他窗口
            if self.current_chat_id == group_id:
                # 如果有其他聊天窗口，切换到第一个；否则创建一个空白窗口
                if len(self.chat_browsers) > 1:
                    # 找到第一个不是当前群组的聊天窗口
                    for chat_id in self.chat_browsers:
                        if chat_id != group_id:
                            self.switch_chat_window(chat_id)
                            break
                else:
                    # 没有其他聊天窗口，切换到默认的空白窗口
                    self.current_chat_id = None

            # 从StackedWidget中移除并删除该聊天窗口
            self.ui.ChatMainWindow.removeWidget(browser)
            browser.deleteLater()
            del self.chat_browsers[group_id]

            # 清除该群组的未读消息计数
            if group_id in self.unread_counts:
                del self.unread_counts[group_id]

        # 从树形控件中删除群组

        root = self.ui.UserGroupTree.invisibleRootItem()
        for i in range(root.childCount()):
            child = root.child(i)
            if child.data(0, Qt.UserRole)[0] == 'Group' and child.data(0, Qt.UserRole)[1] == group_id:
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
