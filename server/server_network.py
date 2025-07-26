"""
Server network communication module

This module implements the network communication functionality of the chat server, including:
- UDP broadcast and server discovery
- TCP client connection management
- Message routing and forwarding
- Group management
- Reminder functionality
- Translation service
- Cross-server communication

Main classes:
- ServerSocket: Server network socket management class
"""

import time
from threading import Thread, Lock
import threading
from socket import *
from proto import Message_pb2
from modules.PackingandUnpacking import *
import traceback
from modules.Translator import translator
from server.modern_server_ui import global_ms
import random
from modules.reminder import create_reminder_manager

class ServerSocket:
    """
    Server network socket management class

    Responsible for managing all network communications of the server, including UDP broadcast, TCP connections,
    message routing, group management, reminder services and other functions.

    Attributes:
        BROADCAST_IP (str): Broadcast IP address
        UDP_PORTS (list): UDP port list
        server_id (str): Server ID
        udp_port (int): UDP listening port
        tcp_port (int): TCP listening port
        client_info (dict): Client information dictionary
        server_info (dict): Server information dictionary
        group_info (dict): Group information dictionary
        ui (QWidget): UI interface reference
    """
    # BROADCAST_IP = '10.181.104.115'  # Broadcast IP, easy to modify later
    BROADCAST_IP = '255.255.255.255'  # Broadcast IP, easy to modify later
    UDP_PORTS = [65432, 65433, 65434, 65435, 9999]  # Local test UDP port list for all servers, can be expanded based on actual server count

    def __init__(self, ui_ref=None, server_id='Server_4', udp_port=65432, tcp_port=65433, udp_ports=None):
        self.server_id = server_id
        self.udp_port = udp_port  # UDP port this server listens on
        self.tcp_port = tcp_port  # TCP port this server listens on
        if udp_ports is not None:
            self.udp_ports = udp_ports  # Customizable broadcast port list
        else:
            self.udp_ports = self.UDP_PORTS
        self.udp_socket = None
        self.tcp_socket = None
        self.heartbeat_interval = 10   # Heartbeat cycle seconds
        self.heartbeat_timeout = 30    # Client timeout seconds
        self.client_info = {}
        self.client_info_lock = Lock()
        self.pending_acks = {}
        self.pending_acks_lock = threading.Lock()
        self.group_info = {}
        self.group_info_lock = Lock()
        self.server_list = {}  # Other server information
        self.server_list_lock = Lock()
        self.ui = ui_ref  # Compatibility retention

        # Initialize reminder manager
        self.reminder_manager = create_reminder_manager(self, use_heap=True)

    def start_all(self):
        Thread(target=self.start_udp_listener, daemon=True).start()
        Thread(target=self.hanle_udp_boardcast, daemon=True).start()
        Thread(target=self.start_tcp_server, daemon=True).start()
        # Start reminder service
        self.reminder_manager.start()

    def discover_servers(self):
        # Actively broadcast DISCOVER_SERVER to all known UDP ports
        def send_discover():
            try:
                msg = Packing('DISCOVER_SERVER', b'')
                for port in self.udp_ports:
                    udp = socket(AF_INET, SOCK_DGRAM)
                    udp.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
                    udp.settimeout(2)
                    udp.sendto(msg, (self.BROADCAST_IP, port))
                    udp.close()
                global_ms.log_signal.emit(f'[Server] Broadcasted DISCOVER_SERVER to all ports {self.udp_ports}')
            except Exception as e:
                global_ms.log_signal.emit(f'[Server] Failed to send DISCOVER_SERVER broadcast: {e}')
        Thread(target=send_discover, daemon=True).start()

    def start_udp_listener(self):
        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.udp_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.udp_socket.bind(('0.0.0.0', self.udp_port))
        global_ms.log_signal.emit(f"[Server] UDP listening port {self.udp_port}")

    def hanle_udp_boardcast(self):
            while True:
                try:
                    # print("[Debug] UDP listening loop, waiting for data...")
                    data, clientaddr = self.udp_socket.recvfrom(2048)
                    purpose, length, payload = Unpacking(data)
                    if purpose == 'DISCOVER_SERVER':
                        # Received DISCOVER_SERVER, first reply to clientaddr, then broadcast to all UDP ports
                        print(f"[Debug] Received DISCOVER_SERVER: {clientaddr}")
                        tosend = self.Feature()
                        # Reply to initiator (client or server's temporary port)
                        self.udp_socket.sendto(tosend, clientaddr)
                        # Broadcast to all server UDP ports
                        for port in self.udp_ports:
                            self.udp_socket.sendto(tosend, (self.BROADCAST_IP, port))
                        global_ms.log_signal.emit(f"Replied to {clientaddr} and broadcasted SERVER_ANNOUNCE to all ports {self.udp_ports}")
                    elif purpose == 'SERVER_ANNOUNCE':
                        announce = Message_pb2.ServerAnnounce()
                        announce.ParseFromString(payload)
                        server_id = announce.serverId
                        features = [(f.featureName, f.port) for f in announce.feature]
                        # print(f"[Debug] Received SERVER_ANNOUNCE: server_id={server_id}, features={features}, from={clientaddr}")
                        if server_id == self.server_id:
                            # Ignore self
                            continue
                        with self.server_list_lock:
                            self.server_list[server_id] = {
                                'ip': clientaddr[0],
                                'features': features,
                                'port': clientaddr[1],
                                'last_announce': time.time(),
                                'socket': None,
                            }
                        global_ms.log_signal.emit(f"[Server] Discovered new server: {server_id} @ {clientaddr[0]} features={features}")

                        # Actively connect to discovered server
                        print(f"[Debug] Discovered server {server_id}, initiating connection")
                        Thread(target=self.connect_to_server, args=(server_id, clientaddr[0], features), daemon=True).start()
                except Exception as e:
                    global_ms.log_signal.emit(f"[Server] hanle_udp_boardcast error: {e}")
                    continue


    def connect_to_server(self, server_id, ip, features):
        # Check if connection already exists
        with self.server_list_lock:
            if server_id in self.server_list and self.server_list[server_id].get('socket'):
                print(f"[Debug] Server {server_id} already has a connection, skipping duplicate connection.")
                return

        try:
            port = features[0][1] if features else self.tcp_port
            print(f"[Debug] Attempting to connect to {ip}:{port} ...")

            # Add brief delay to avoid simultaneous connection conflicts
            time.sleep(random.uniform(0.5, 2.0))

            s = socket(AF_INET, SOCK_STREAM)
            s.settimeout(10)  # Set connection timeout
            s.connect((ip, port))

            # Construct CONNECT_SERVER message
            connect_server = Message_pb2.ConnectServer()
            connect_server.serverId = self.server_id  # Use instance variable
            connect_server.features.extend([f[0] for f in features])
            payload = connect_server.SerializeToString()
            msg = Packing('CONNECT_SERVER', payload)
            s.send(msg)

            # Wait for CONNECTED reply
            try:
                data = s.recv(1024)
                if data:
                    purpose, length, payload = Unpacking(data)
                    if purpose == 'CONNECTED':
                        connect_response = Message_pb2.ConnectResponse()
                        connect_response.ParseFromString(payload)
                        if connect_response.result == Message_pb2.ConnectResponse.CONNECTED:
                            # Connection successful, save socket
                            with self.server_list_lock:
                                if server_id in self.server_list:
                                    self.server_list[server_id]['socket'] = s
                                    self.server_list[server_id]['last_active'] = time.time()
                                else:
                                    self.server_list[server_id] = {
                                        'ip': ip,
                                        'features': features,
                                        'port': port,
                                        'last_active': time.time(),
                                        'socket': s,
                                    }
                            global_ms.log_signal.emit(f"[Server] Successfully connected to server {server_id}@{ip}:{port}")
                            global_ms.refresh_list_signal.emit()

                            # Start dedicated message handling thread
                            Thread(target=self.handle_server_messages, args=(s, server_id), daemon=True).start()
                        else:
                            global_ms.log_signal.emit(f"[Server] Connection to server {server_id} rejected: {connect_response.result}")
                            s.close()
                    else:
                        global_ms.log_signal.emit(f"[Server] Received unexpected reply: {purpose}")
                        s.close()
                else:
                    global_ms.log_signal.emit(f"[Server] No response from server {server_id}")
                    s.close()
            except Exception as e:
                global_ms.log_signal.emit(f"[Server] Error waiting for CONNECTED reply: {e}")
                s.close()

        except Exception as e:
            print(f"[Debug] Failed to connect to server {server_id}@{ip}:{port}: {e}")
            global_ms.log_signal.emit(f"[Server] Failed to connect to server {server_id}@{ip}:{port}: {e}")

    def Feature(self):
        announce = Message_pb2.ServerAnnounce()
        announce.serverId = self.server_id  # Use instance variable
        feature1 = announce.feature.add()
        feature1.featureName = 'TRANSLATION'
        feature1.port = self.tcp_port
        feature2 = announce.feature.add()
        feature2.featureName = 'REMINDER'
        feature2.port = self.tcp_port
        feature3 = announce.feature.add()
        feature3.featureName = 'MESSAGES'
        feature3.port = self.tcp_port
        return Packing('SERVER_ANNOUNCE', announce.SerializeToString())

    def start_tcp_server(self):
        self.tcp_socket = socket(AF_INET, SOCK_STREAM)
        self.tcp_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.tcp_socket.bind(('0.0.0.0', self.tcp_port))
        self.tcp_socket.listen(5)
        global_ms.log_signal.emit(f"[Server] TCP Server started at port {self.tcp_port}")
        Thread(target=self.heartbeat_monitor, daemon=True).start()
        Thread(target=self.server_heartbeat_monitor, daemon=True).start()
        while True:
            try:
                client_socket, client_addr = self.tcp_socket.accept()
                global_ms.log_signal.emit(f"[Server] New TCP connection from {client_addr[0]}:{client_addr[1]}")
                Thread(target=self.handle_tcp_client, args=(client_socket, client_addr), daemon=True).start()
            except Exception as e:
                global_ms.log_signal.emit(f"[Server] TCP Client connection error: {e}")
                continue

    def handle_tcp_client(self, client_socket, client_addr):
        user_id = None
        try:
            data = client_socket.recv(1024)
            if not data:
                global_ms.log_signal.emit(f"[Server] Client {client_addr} disconnected (no data on connect)")
                client_socket.close()
                return

            purpose, length, payload = Unpacking(data)
            print(Unpacking(data))
            if purpose == 'CONNECT_CLIENT':
                connect_client = Message_pb2.ConnectClient()
                connect_client.ParseFromString(payload)
                user_id = connect_client.user.userId
                server_id = connect_client.user.serverId

                with self.client_info_lock:
                    if user_id in self.client_info:
                        ConnectResponse = Message_pb2.ConnectResponse()
                        ConnectResponse.result = Message_pb2.ConnectResponse.IS_ALREADY_CONNECTED_ERROR
                        payload = ConnectResponse.SerializeToString()
                        tosend = Packing('CONNECTED', payload)
                        client_socket.send(tosend)
                        global_ms.log_signal.emit(
                            f"[Server] Reject duplicate connection for userId {user_id} from {client_addr[0]}:{client_addr[1]}"
                        )
                        client_socket.close()
                        return
                    else:
                        ConnectResponse = Message_pb2.ConnectResponse()
                        ConnectResponse.result = Message_pb2.ConnectResponse.CONNECTED
                        payload = ConnectResponse.SerializeToString()
                        tosend = Packing('CONNECTED', payload)
                        client_socket.send(tosend)
                        global_ms.log_signal.emit(
                            f"[Server] User {user_id} connection established from {client_addr[0]}:{client_addr[1]}"
                        )
                        self.client_info[user_id] = {
                            'socket': client_socket,
                            'last_active': time.time(),
                            'thread': threading.current_thread(),
                            'server_id': server_id,
                            'ip': client_addr[0],
                            'port': client_addr[1],
                        }
                global_ms.refresh_list_signal.emit()
            elif purpose == 'CONNECT_SERVER':
                connect_server = Message_pb2.ConnectServer()
                connect_server.ParseFromString(payload)
                server_id = connect_server.serverId
                features = connect_server.features

                # Check if connection already exists to this server
                with self.server_list_lock:
                    if server_id in self.server_list and self.server_list[server_id].get('socket'):
                        # Connection already exists, reject duplicate connection
                        global_ms.log_signal.emit(f"[Server] Rejecting duplicate connection for server {server_id}")
                        client_socket.close()
                        return

                # Reply CONNECTED message
                ConnectResponse = Message_pb2.ConnectResponse()
                ConnectResponse.result = Message_pb2.ConnectResponse.CONNECTED
                payload = ConnectResponse.SerializeToString()
                tosend = Packing('CONNECTED', payload)
                client_socket.send(tosend)

                global_ms.log_signal.emit(
                    f"[Server] Server {server_id} connection established from {client_addr[0]}:{client_addr[1]}"
                )

                # Update socket information in server_list
                with self.server_list_lock:
                    if server_id in self.server_list:
                        self.server_list[server_id]['socket'] = client_socket
                        self.server_list[server_id]['last_active'] = time.time()
                    else:
                        # If not in server_list, add new entry
                        self.server_list[server_id] = {
                            'ip': client_addr[0],
                            'features': [(f, self.tcp_port) for f in features],
                            'port': client_addr[1],
                            'last_active': time.time(),
                            'socket': client_socket,
                        }

                global_ms.refresh_list_signal.emit()

                # Server connection enters dedicated message handling loop
                self.handle_server_messages(client_socket, server_id)
                return

            elif purpose == 'SEARCH_USERS':
                # Handle client user search request
                QueryUsers = Message_pb2.QueryUsers()
                QueryUsers.ParseFromString(payload)
                query = QueryUsers.query
                handle = QueryUsers.handle

                                    # First collect local users
                QueryUsersResponse = Message_pb2.QueryUsersResponse()
                QueryUsersResponse.handle = handle

                                    # Add local users
                with self.client_info_lock:
                    for uid, info in self.client_info.items():
                        user = Message_pb2.User()
                        user.userId = str(uid)
                        user.serverId = str(info['server_id'])
                        QueryUsersResponse.users.append(user)

                                    # Forward search request to other servers
                with self.server_list_lock:
                    for server_id, server_info in self.server_list.items():
                        server_socket = server_info.get('socket')
                        if server_socket:
                            try:
                                # Forward SEARCH_USERS to other servers
                                forward_query = Message_pb2.QueryUsers()
                                forward_query.query = query
                                forward_query.handle = handle  # Keep same handle for response matching
                                forward_msg = Packing('SEARCH_USERS', forward_query.SerializeToString())
                                server_socket.send(forward_msg)
                                global_ms.log_signal.emit(f"[Server] Forwarding SEARCH_USERS to server {server_id}")
                            except Exception as e:
                                global_ms.log_signal.emit(f"[Server] Failed to forward SEARCH_USERS to server {server_id}: {e}")

                # Reply local results first
                tosend = Packing('SEARCH_USERS_RESP', QueryUsersResponse.SerializeToString())
                client_socket.send(tosend)

                # Save request information for later aggregation of remote server responses
                with self.client_info_lock:
                    if user_id in self.client_info:
                        self.client_info[user_id]['pending_search'] = {
                            'handle': handle,
                            'query': query,
                            'socket': client_socket
                        }

            else:
                global_ms.log_signal.emit(f"[Server] First packet is neither CONNECT_CLIENT nor CONNECT_SERVER, closing.")
                client_socket.close()
                return

            while True:
                data = client_socket.recv(1024)
                if not data:
                    global_ms.log_signal.emit(f"[Server] Client {user_id} disconnected")
                    break
                with self.client_info_lock:
                    if user_id in self.client_info:
                        self.client_info[user_id]['last_active'] = time.time()
                purpose, length, payload = Unpacking(data)
                # print(purpose)  # Commented out to avoid console printing of ping/pong messages

                if purpose == 'PING':
                    pong_msg = Packing('PONG', b'')
                    client_socket.send(pong_msg)
                    print(f"[Server] Received PING from {user_id}, sent PONG")
                elif purpose == 'PONG':
                    print(f"[Server] Received PONG from {user_id}")
                    pass

                elif purpose == 'MESSAGE':
                    msg = Message_pb2.ChatMessage()
                    msg.ParseFromString(payload)
                    which = msg.WhichOneof('recipient')
                    msg_snowflake = msg.messageSnowflake
                    source_user_id = user_id
                    source_server_id = self.client_info[source_user_id]['server_id']

                    # Check if translation is needed
                    content_type = msg.WhichOneof('content')
                    if content_type == 'translation':
                        # Handle translation request
                        translation_msg = msg.translation
                        if translation_msg.original_text and not translation_msg.translated_text:
                            # Only original text without translation, perform translation
                            try:
                                from modules.Translator import translator

                                # Convert protobuf Language enum to string
                                language_map = {
                                    0: 'Deutsch',   # DE
                                    1: 'English',   # EN
                                    2: 'Chinese' ,      # ZH
                                    3: 'Türkçe',
                                    'DE': 'Deutsch',  # DE
                                    'EN': 'English',  # EN
                                    'ZH': 'Chinese',
                                    'TR': 'Türkçe'
                                }
                                target_language = language_map.get(translation_msg.target_language, 'English')

                                # Perform translation
                                translated_text = translator(translation_msg.original_text, target_language)

                                # Fill in translation result
                                msg.translation.translated_text = translated_text

                                # Re-serialize message
                                payload = msg.SerializeToString()

                                global_ms.log_signal.emit(f"[Server] Translating message: '{translation_msg.original_text}' -> '{translated_text}' ({target_language})")

                            except Exception as e:
                                global_ms.log_signal.emit(f"[Server] Translation failed: {e}")
                                # When translation fails, forward as is

                    with self.pending_acks_lock:
                        self.pending_acks[msg_snowflake] = {
                            'source_user': source_user_id,
                            'source_server': source_server_id,
                        }

                    if which == 'user':
                        target_user = msg.user.userId
                        target_server = msg.user.serverId

                        # First check if target user is local
                        with self.client_info_lock:
                            if target_user in self.client_info:
                                # Local user, forward directly
                                tosend = Packing('MESSAGE', payload)
                                self.client_info[target_user]['socket'].send(tosend)
                                global_ms.log_signal.emit(f"[Server] Forwarding message to local user {target_user}")
                            else:
                                # User not local, need to forward to other servers
                                message_forwarded = False
                                with self.server_list_lock:
                                    for server_id, server_info in self.server_list.items():
                                        server_socket = server_info.get('socket')
                                        if server_socket and (target_server == server_id or target_server in str(server_info)):
                                            try:
                                                forward_msg = Packing('MESSAGE', payload)
                                                server_socket.send(forward_msg)
                                                global_ms.log_signal.emit(f"[Server] Forwarding message to server {server_id} user {target_user}")
                                                message_forwarded = True
                                                break
                                            except Exception as e:
                                                global_ms.log_signal.emit(f"[Server] Failed to forward message to server {server_id}: {e}")

                                if not message_forwarded:
                                    # If target server not found, try broadcasting to all connected servers
                                    with self.server_list_lock:
                                        for server_id, server_info in self.server_list.items():
                                            server_socket = server_info.get('socket')
                                            if server_socket:
                                                try:
                                                    forward_msg = Packing('MESSAGE', payload)
                                                    server_socket.send(forward_msg)
                                                    global_ms.log_signal.emit(f"[Server] Broadcasting message to server {server_id}")
                                                except Exception as e:
                                                    global_ms.log_signal.emit(f"[Server] Failed to broadcast message to server {server_id}: {e}")

                    elif which == 'group':
                        groupId = msg.group.groupId
                        with self.group_info_lock:
                            if groupId not in self.group_info:
                                global_ms.log_signal.emit(f"[Server] Group {groupId} not found for group message.")
                                return
                            members = self.group_info[groupId]['members']
                            with self.client_info_lock:
                                for member_id in members:
                                    if member_id != user_id and member_id in self.client_info:
                                        tosend = Packing('MESSAGE', payload)
                                        self.client_info[member_id]['socket'].send(tosend)

                elif purpose == 'MESSAGE_ACK':
                    ack = Message_pb2.ChatMessageResponse()
                    ack.ParseFromString(payload)
                    msg_snowflake = ack.messageSnowflake

                    with self.pending_acks_lock:
                        if msg_snowflake in self.pending_acks:
                            source_info = self.pending_acks[msg_snowflake]
                            source_user_id = source_info['source_user']

                            with self.client_info_lock:
                                if source_user_id in self.client_info:
                                    self.client_info[source_user_id]['socket'].send(
                                        Packing('MESSAGE_ACK', payload)
                                    )
                            del self.pending_acks[msg_snowflake]

                elif purpose == 'MODIFY_GROUP':
                    try:
                        modify_group = Message_pb2.ModifyGroup()
                        modify_group.ParseFromString(payload)

                        groupId = modify_group.groupId
                        displayName = modify_group.displayName
                        deleteGroup = modify_group.deleteGroup
                        admin_ids = {admin.userId for admin in modify_group.admins}

                        resp = Message_pb2.ModifyGroupResponse()
                        resp.handle = modify_group.handle

                        with self.group_info_lock:
                            if deleteGroup:
                                if groupId in self.group_info:
                                    del self.group_info[groupId]
                                    resp.result = Message_pb2.ModifyGroupResponse.SUCCESS
                                else:
                                    resp.result = Message_pb2.ModifyGroupResponse.NOT_FOUND
                            else:
                                if groupId in self.group_info:
                                    self.group_info[groupId]['displayName'] = displayName
                                    self.group_info[groupId]['admins'] = admin_ids
                                    resp.result = Message_pb2.ModifyGroupResponse.SUCCESS
                                else:
                                    self.group_info[groupId] = {
                                        'displayName': displayName,
                                        'admins': set(admin_ids),
                                        'members': set(admin_ids),
                                    }
                                    resp.result = Message_pb2.ModifyGroupResponse.SUCCESS

                        tosend = Packing('MODIFY_GROUP_RESP', resp.SerializeToString())
                        client_socket.send(tosend)
                        global_ms.log_signal.emit(f"[Server] MODIFY_GROUP {groupId} by {user_id}, result={resp.result}")

                    except Exception as e:
                        resp = Message_pb2.ModifyGroupResponse()
                        resp.handle = modify_group.handle if 'modify_group' in locals() else 0
                        resp.result = Message_pb2.ModifyGroupResponse.UNKNOWN_ERROR
                        tosend = Packing('MODIFY_GROUP_RESP', resp.SerializeToString())
                        client_socket.send(tosend)
                        global_ms.log_signal.emit(f"[Server] MODIFY_GROUP error: {e}")

                elif purpose == 'LEAVE_GROUP':
                    try:
                        leave_msg = Message_pb2.LeaveGroup()
                        leave_msg.ParseFromString(payload)
                        group_id = leave_msg.group.groupId
                        user_leaving = leave_msg.user.userId
                        with self.group_info_lock:
                            if group_id in self.group_info:
                                # Remove leaving user
                                self.group_info[group_id]['members'].discard(user_leaving)
                                self.group_info[group_id]['admins'].discard(user_leaving)

                                # Get remaining group members
                                remaining_members = self.group_info[group_id]['members'].copy()
                                global_ms.log_signal.emit(f"[Server] {user_leaving} has left group {group_id}")

                                # Send updated GROUP_MEMBERS message to remaining group members
                                if remaining_members:
                                    group_members_msg = Message_pb2.GroupMembers()
                                    group_members_msg.group.groupId = group_id
                                    group_members_msg.group.serverId = self.server_id
                                    group_members_msg.result = Message_pb2.GroupMembers.SUCCESS

                                    # Add remaining group members to message
                                    for member_id in remaining_members:
                                        member_user = group_members_msg.user.add()
                                        member_user.userId = member_id
                                        with self.client_info_lock:
                                            member_user.serverId = self.client_info[member_id][
                                                'server_id'] if member_id in self.client_info else ""

                                    # Serialize message
                                    group_members_data = group_members_msg.SerializeToString()
                                    group_members_packet = Packing('GROUP_MEMBERS', group_members_data)

                                    # Send update message to all remaining members
                                    with self.client_info_lock:
                                        for remaining_member_id in remaining_members:
                                            if remaining_member_id in self.client_info:
                                                try:
                                                    self.client_info[remaining_member_id]['socket'].send(
                                                        group_members_packet)
                                                    global_ms.log_signal.emit(
                                                        f"[Server] Sending GROUP_MEMBERS update to remaining members {remaining_member_id}")
                                                except Exception as e:
                                                    global_ms.log_signal.emit(
                                                        f"[Server] Failed to send GROUP_MEMBERS update to member {remaining_member_id}: {e}")
                                else:
                                    # If group has no remaining members, consider deleting the group
                                    del self.group_info[group_id]
                                    global_ms.log_signal.emit(f"[Server] Group {group_id} deleted (no remaining members)")
                            else:
                                global_ms.log_signal.emit(f"[Server] Group {group_id} not found for LEAVE_GROUP")
                    except Exception as e:
                        global_ms.log_signal.emit(f"[Server] LEAVE_GROUP error: {e}")

                elif purpose == 'INVITE_GROUP':
                    try:
                        invite = Message_pb2.InviteToGroup()
                        invite.ParseFromString(payload)
                        group_id = invite.groupId
                        invited_user_id = invite.user.userId
                        invited_user_server = invite.user.serverId

                        with self.group_info_lock:
                            if group_id not in self.group_info:
                                global_ms.log_signal.emit(
                                    f"[Server] INVITE_GROUP failed: Group {group_id} does not exist")
                                return

                            admins = self.group_info[group_id]['admins']
                            if user_id not in admins:
                                global_ms.log_signal.emit(
                                    f"[Server] INVITE_GROUP denied: {user_id} is not admin of {group_id}")
                                return

                        with self.client_info_lock:
                            if invited_user_id in self.client_info:
                                notify = Message_pb2.NotifyGroupInvite()
                                notify.handle = invite.handle
                                notify.group.groupId = group_id
                                notify.group.serverId = self.client_info[user_id]['server_id']
                                packet = Packing('NOTIFY_GROUP_INVITE', notify.SerializeToString())
                                self.client_info[invited_user_id]['socket'].send(packet)
                                global_ms.log_signal.emit(
                                    f"[Server] INVITE_GROUP: {user_id} invited {invited_user_id} to group {group_id}")
                            else:
                                global_ms.log_signal.emit(
                                    f"[Server] INVITE_GROUP: Invited user {invited_user_id} offline (invite dropped)")
                    except Exception as e:
                        global_ms.log_signal.emit(f"[Server] INVITE_GROUP error: {e}")

                elif purpose == 'QUERY_GROUP_MEMBERS':
                    try:
                        query = Message_pb2.ListGroupMembers()
                        query.ParseFromString(payload)
                        group_id = query.group.groupId
                        group_server_id = query.group.serverId
                        resp = Message_pb2.GroupMembers()
                        resp.group.groupId = group_id
                        resp.group.serverId = self.client_info[user_id]['server_id']
                        with self.group_info_lock:
                            if group_id not in self.group_info:
                                resp.result = Message_pb2.GroupMembers.NOT_FOUND
                            else:
                                resp.result = Message_pb2.GroupMembers.SUCCESS
                                for uid in self.group_info[group_id]['members']:
                                    u = resp.user.add()
                                    u.userId = uid
                                    u.serverId = self.client_info[uid]['server_id'] if uid in self.client_info else ""
                        client_socket.send(Packing('GROUP_MEMBERS', resp.SerializeToString()))
                        global_ms.log_signal.emit(f"[Server] Sent member list of {group_id} to {user_id}")
                    except Exception as e:
                        global_ms.log_signal.emit(f"[Server] QUERY_GROUP_MEMBERS error: {e}")

                elif purpose == 'JOIN_GROUP':
                    try:
                        join = Message_pb2.JoinGroup()
                        join.ParseFromString(payload)
                        group_id = join.group.groupId
                        new_user_id = join.user.userId
                        with self.group_info_lock:
                            if group_id not in self.group_info:
                                global_ms.log_signal.emit(f"[Server] JOIN_GROUP failed: Group {group_id} not found")
                                return
                            self.group_info[group_id]['members'].add(new_user_id)
                            global_ms.log_signal.emit(f"[Server] {new_user_id} joined group {group_id}")
                    except Exception as e:
                        global_ms.log_signal.emit(f"[Server] JOIN_GROUP error: {e}")

                elif purpose == 'SEARCH_USERS':
                    # Handle client user search request
                    QueryUsers = Message_pb2.QueryUsers()
                    QueryUsers.ParseFromString(payload)
                    query = QueryUsers.query
                    handle = QueryUsers.handle

                    # First collect local users
                    QueryUsersResponse = Message_pb2.QueryUsersResponse()
                    QueryUsersResponse.handle = handle

                    # Add local users
                    with self.client_info_lock:
                        for uid, info in self.client_info.items():
                            user = Message_pb2.User()
                            user.userId = str(uid)
                            user.serverId = str(info['server_id'])
                            QueryUsersResponse.users.append(user)

                    # Forward search request to other servers
                    with self.server_list_lock:
                        for server_id, server_info in self.server_list.items():
                            server_socket = server_info.get('socket')
                            if server_socket:
                                try:
                                    # Forward SEARCH_USERS to other servers
                                    forward_query = Message_pb2.QueryUsers()
                                    forward_query.query = query
                                    forward_query.handle = handle  # Keep same handle for response matching
                                    forward_msg = Packing('SEARCH_USERS', forward_query.SerializeToString())
                                    server_socket.send(forward_msg)
                                    global_ms.log_signal.emit(f"[Server] Forwarding SEARCH_USERS to server {server_id}")
                                except Exception as e:
                                    global_ms.log_signal.emit(f"[Server] Failed to forward SEARCH_USERS to server {server_id}: {e}")

                    # Reply local results first
                    tosend = Packing('SEARCH_USERS_RESP', QueryUsersResponse.SerializeToString())
                    client_socket.send(tosend)

                    # Save request information for later aggregation of remote server responses
                    with self.client_info_lock:
                        if user_id in self.client_info:
                            self.client_info[user_id]['pending_search'] = {
                                'handle': handle,
                                'query': query,
                                'socket': client_socket
                            }

                elif purpose == 'SEARCH_USERS_RESP':
                    # Handle search result response from other servers
                    QueryUsersResponse = Message_pb2.QueryUsersResponse()
                    QueryUsersResponse.ParseFromString(payload)
                    handle = QueryUsersResponse.handle

                    # Find client waiting for this response
                    target_client = None
                    with self.client_info_lock:
                        for user_id, info in self.client_info.items():
                            pending_search = info.get('pending_search')
                            if pending_search and pending_search['handle'] == handle:
                                target_client = info['socket']
                                break

                    if target_client:
                        # Forward search results to client
                        response_msg = Packing('SEARCH_USERS_RESP', payload)
                        target_client.send(response_msg)
                        global_ms.log_signal.emit(f"[Server] Forwarding search results from server {server_id} to client")

                elif purpose == 'MESSAGE':
                    # Handle message forwarding from other servers
                    msg = Message_pb2.ChatMessage()
                    msg.ParseFromString(payload)
                    which = msg.WhichOneof('recipient')

                    if which == 'user':
                        target_user = msg.user.userId
                        with self.client_info_lock:
                            if target_user in self.client_info:
                                # Forward message to local user
                                forward_msg = Packing('MESSAGE', payload)
                                self.client_info[target_user]['socket'].send(forward_msg)
                                global_ms.log_signal.emit(f"[Server] Forwarding message from server {server_id} to user {target_user}")
                            else:
                                global_ms.log_signal.emit(f"[Server] Target user {target_user} not on this server")

                elif purpose == 'MESSAGE_ACK':
                    # Handle message acknowledgment from other servers
                    ack = Message_pb2.ChatMessageResponse()
                    ack.ParseFromString(payload)
                    msg_snowflake = ack.messageSnowflake

                    # Find local user waiting for this ACK
                    with self.pending_acks_lock:
                        if msg_snowflake in self.pending_acks:
                            source_info = self.pending_acks[msg_snowflake]
                            source_user_id = source_info['source_user']

                            with self.client_info_lock:
                                if source_user_id in self.client_info:
                                    # Forward ACK to original sender
                                    ack_msg = Packing('MESSAGE_ACK', payload)
                                    self.client_info[source_user_id]['socket'].send(ack_msg)
                                    global_ms.log_signal.emit(f"[Server] Forwarding message ACK to user {source_user_id}")

                            del self.pending_acks[msg_snowflake]

                elif purpose == 'MODIFY_GROUP':
                    try:
                        modify_group = Message_pb2.ModifyGroup()
                        modify_group.ParseFromString(payload)

                        groupId = modify_group.groupId
                        displayName = modify_group.displayName
                        deleteGroup = modify_group.deleteGroup
                        admin_ids = {admin.userId for admin in modify_group.admins}

                        resp = Message_pb2.ModifyGroupResponse()
                        resp.handle = modify_group.handle

                        with self.group_info_lock:
                            if deleteGroup:
                                if groupId in self.group_info:
                                    del self.group_info[groupId]
                                    resp.result = Message_pb2.ModifyGroupResponse.SUCCESS
                                else:
                                    resp.result = Message_pb2.ModifyGroupResponse.NOT_FOUND
                            else:
                                if groupId in self.group_info:
                                    self.group_info[groupId]['displayName'] = displayName
                                    self.group_info[groupId]['admins'] = admin_ids
                                    resp.result = Message_pb2.ModifyGroupResponse.SUCCESS
                                else:
                                    self.group_info[groupId] = {
                                        'displayName': displayName,
                                        'admins': set(admin_ids),
                                        'members': set(admin_ids),
                                    }
                                    resp.result = Message_pb2.ModifyGroupResponse.SUCCESS

                        tosend = Packing('MODIFY_GROUP_RESP', resp.SerializeToString())
                        client_socket.send(tosend)
                        global_ms.log_signal.emit(f"[Server] MODIFY_GROUP {groupId} by {user_id}, result={resp.result}")

                    except Exception as e:
                        resp = Message_pb2.ModifyGroupResponse()
                        resp.handle = modify_group.handle if 'modify_group' in locals() else 0
                        resp.result = Message_pb2.ModifyGroupResponse.UNKNOWN_ERROR
                        tosend = Packing('MODIFY_GROUP_RESP', resp.SerializeToString())
                        client_socket.send(tosend)
                        global_ms.log_signal.emit(f"[Server] MODIFY_GROUP error: {e}")


                elif purpose == 'LEAVE_GROUP':
                    try:
                        leave_msg = Message_pb2.LeaveGroup()
                        leave_msg.ParseFromString(payload)
                        group_id = leave_msg.group.groupId
                        user_leaving = leave_msg.user.userId
                        with self.group_info_lock:
                            if group_id in self.group_info:
                                # Remove leaving user
                                self.group_info[group_id]['members'].discard(user_leaving)
                                self.group_info[group_id]['admins'].discard(user_leaving)

                                # Get remaining group members
                                remaining_members = self.group_info[group_id]['members'].copy()
                                global_ms.log_signal.emit(f"[Server] {user_leaving} has left group {group_id}")

                                # Send updated GROUP_MEMBERS message to remaining group members
                                if remaining_members:
                                    group_members_msg = Message_pb2.GroupMembers()
                                    group_members_msg.group.groupId = group_id
                                    group_members_msg.group.serverId = self.server_id
                                    group_members_msg.result = Message_pb2.GroupMembers.SUCCESS

                                    # Add remaining group members to message
                                    for member_id in remaining_members:
                                        member_user = group_members_msg.user.add()
                                        member_user.userId = member_id
                                        with self.client_info_lock:
                                            member_user.serverId = self.client_info[member_id][
                                                'server_id'] if member_id in self.client_info else ""

                                    # Serialize message
                                    group_members_data = group_members_msg.SerializeToString()
                                    group_members_packet = Packing('GROUP_MEMBERS', group_members_data)
                                    # Send update message to all remaining members

                                    with self.client_info_lock:
                                        for remaining_member_id in remaining_members:
                                            if remaining_member_id in self.client_info:
                                                try:
                                                    self.client_info[remaining_member_id]['socket'].send(
                                                        group_members_packet)
                                                    global_ms.log_signal.emit(
                                                        f"[Server] Sending GROUP_MEMBERS update to remaining members {remaining_member_id}")
                                                except Exception as e:
                                                    global_ms.log_signal.emit(
                                                        f"[Server] Failed to send GROUP_MEMBERS update to member {remaining_member_id}: {e}")

                                else:
                                    # If group has no remaining members, consider deleting the group
                                    del self.group_info[group_id]
                                    global_ms.log_signal.emit(f"[Server] Group {group_id} deleted (no remaining members)")
                            else:
                                global_ms.log_signal.emit(f"[Server] Group {group_id} not found for LEAVE_GROUP")
                    except Exception as e:
                        global_ms.log_signal.emit(f"[Server] LEAVE_GROUP error: {e}")

                elif purpose == 'INVITE_GROUP':
                    try:
                        invite = Message_pb2.InviteToGroup()
                        invite.ParseFromString(payload)
                        group_id = invite.groupId
                        invited_user_id = invite.user.userId
                        invited_user_server = invite.user.serverId

                        with self.group_info_lock:
                            if group_id not in self.group_info:
                                global_ms.log_signal.emit(
                                    f"[Server] INVITE_GROUP failed: Group {group_id} does not exist")
                                return

                            admins = self.group_info[group_id]['admins']
                            if user_id not in admins:
                                global_ms.log_signal.emit(
                                    f"[Server] INVITE_GROUP denied: {user_id} is not admin of {group_id}")
                                return

                        with self.client_info_lock:
                            if invited_user_id in self.client_info:
                                notify = Message_pb2.NotifyGroupInvite()
                                notify.handle = invite.handle
                                notify.group.groupId = group_id
                                notify.group.serverId = self.client_info[user_id]['server_id']
                                packet = Packing('NOTIFY_GROUP_INVITE', notify.SerializeToString())
                                self.client_info[invited_user_id]['socket'].send(packet)
                                global_ms.log_signal.emit(
                                    f"[Server] INVITE_GROUP: {user_id} invited {invited_user_id} to group {group_id}")
                            else:
                                global_ms.log_signal.emit(
                                    f"[Server] INVITE_GROUP: Invited user {invited_user_id} offline (invite dropped)")
                    except Exception as e:
                        global_ms.log_signal.emit(f"[Server] INVITE_GROUP error: {e}")

                elif purpose == 'QUERY_GROUP_MEMBERS':
                    try:
                        query = Message_pb2.ListGroupMembers()
                        query.ParseFromString(payload)
                        group_id = query.group.groupId
                        group_server_id = query.group.serverId
                        resp = Message_pb2.GroupMembers()
                        resp.group.groupId = group_id
                        resp.group.serverId = self.client_info[user_id]['server_id']
                        with self.group_info_lock:
                            if group_id not in self.group_info:
                                resp.result = Message_pb2.GroupMembers.NOT_FOUND
                            else:
                                resp.result = Message_pb2.GroupMembers.SUCCESS
                                for uid in self.group_info[group_id]['members']:
                                    u = resp.user.add()
                                    u.userId = uid
                                    u.serverId = self.client_info[uid]['server_id'] if uid in self.client_info else ""
                        client_socket.send(Packing('GROUP_MEMBERS', resp.SerializeToString()))
                        global_ms.log_signal.emit(f"[Server] Sent member list of {group_id} to {user_id}")
                    except Exception as e:
                        global_ms.log_signal.emit(f"[Server] QUERY_GROUP_MEMBERS error: {e}")

                elif purpose == 'JOIN_GROUP':
                    try:
                        join = Message_pb2.JoinGroup()
                        join.ParseFromString(payload)
                        group_id = join.group.groupId
                        new_user_id = join.user.userId
                        with self.group_info_lock:
                            if group_id not in self.group_info:
                                global_ms.log_signal.emit(f"[Server] JOIN_GROUP failed: Group {group_id} not found")
                                return
                            self.group_info[group_id]['members'].add(new_user_id)
                            global_ms.log_signal.emit(f"[Server] {new_user_id} joined group {group_id}")
                    except Exception as e:
                        global_ms.log_signal.emit(f"[Server] JOIN_GROUP error: {e}")

                elif purpose == 'SET_REMINDER':
                    try:
                        set_reminder = Message_pb2.SetReminder()
                        set_reminder.ParseFromString(payload)

                        reminder_user_id = set_reminder.user.userId
                        reminder_server_id = set_reminder.user.serverId
                        event = set_reminder.event
                        countdown_seconds = set_reminder.countdownSeconds

                        # Verify user can only set reminders for themselves
                        if reminder_user_id != user_id:
                            global_ms.log_signal.emit(f"[Server] User {user_id} attempted to set reminder for another user {reminder_user_id}, rejected.")
                            continue

                        # Construct complete user identifier including server information for cross-server reminders
                        if reminder_server_id and reminder_server_id != self.server_id:
                            # Cross-server reminder: user on other server, use format userId@serverId
                            full_user_id = f"{reminder_user_id}@{reminder_server_id}"
                            global_ms.log_signal.emit(f"[Server] Received cross-server reminder request: User {user_id} on server {reminder_server_id} setting reminder: {event} (countdown {countdown_seconds} seconds)")
                        else:
                            # Local server user, use userId directly
                            full_user_id = reminder_user_id
                            global_ms.log_signal.emit(f"[Server] User {user_id} setting reminder for self: {event} (countdown {countdown_seconds} seconds)")

                        # Add reminder to manager
                        self.reminder_manager.add_reminder(full_user_id, event, countdown_seconds)

                    except Exception as e:
                        global_ms.log_signal.emit(f"[Server] SET_REMINDER error: {e}")

                elif purpose == 'TRANSLATE':
                    # Handle new TRANSLATE message protocol
                    try:
                        translate_msg = Message_pb2.Translate()
                        translate_msg.ParseFromString(payload)

                        # Perform translation processing
                        if translate_msg.original_text:
                            try:
                                from modules.Translator import translator

                                # Convert protobuf Language enum to string
                                language_map = {
                                    0: 'Deutsch',   # DE
                                    1: 'English',   # EN
                                    2: 'Chinese',       # ZH
                                    3: 'Türkçe',
                                }
                                target_language = language_map.get(translate_msg.target_language, 'English')

                                # Perform translation
                                translated_text = translator(translate_msg.original_text, target_language)

                                # Create TRANSLATED message response
                                translated_msg = Message_pb2.Translated()
                                translated_msg.target_language = translate_msg.target_language
                                translated_msg.original_text = translate_msg.original_text
                                translated_msg.translated_text = translated_text

                                # Send TRANSLATED message to requesting client
                                response_data = translated_msg.SerializeToString()
                                response_packet = Packing('TRANSLATED', response_data)
                                client_socket.send(response_packet)

                                global_ms.log_signal.emit(f"[Server] Processing TRANSLATE request: '{translate_msg.original_text}' -> '{translated_text}' ({target_language})")

                            except Exception as e:
                                global_ms.log_signal.emit(f"[Server] Translation processing failed: {e}")
                                # Send original text when translation fails
                                translated_msg = Message_pb2.Translated()
                                translated_msg.target_language = translate_msg.target_language
                                translated_msg.original_text = translate_msg.original_text
                                translated_msg.translated_text = translate_msg.original_text  # Use original text

                                response_data = translated_msg.SerializeToString()
                                response_packet = Packing('TRANSLATED', response_data)
                                client_socket.send(response_packet)

                    except Exception as e:
                        global_ms.log_signal.emit(f"[Server] Failed to process TRANSLATE message: {e}")

                else:
                    # Handle other server-server protocol messages
                    global_ms.log_signal.emit(f"[Server] Received unhandled message from server {server_id}: {purpose}")

        except BaseException as e:
            global_ms.log_signal.emit(f"[Server] handle_tcp_client error: {e}\n{traceback.format_exc()}")
        finally:
            if user_id:
                with self.client_info_lock:
                    if user_id in self.client_info and self.client_info[user_id]['socket'] is client_socket:
                        del self.client_info[user_id]
                global_ms.refresh_list_signal.emit()
            try:
                client_socket.close()
            except:
                pass

    def heartbeat_monitor(self):
        while True:
            time.sleep(self.heartbeat_interval)
            now = time.time()
            to_remove = []
            with self.client_info_lock:
                for user_id, info in list(self.client_info.items()):
                    s = info['socket']
                    last_active = info['last_active']
                    if now - last_active > self.heartbeat_timeout:
                        global_ms.log_signal.emit(f"[Server] User {user_id} heartbeat timeout, disconnecting.")
                        try:
                            s.close()
                        except:
                            pass
                        to_remove.append(user_id)
                        continue
                    try:
                        ping_msg = Packing('PING', b'')
                        s.send(ping_msg)
                        print(f"[Server] Sent PING to {user_id}")
                    except Exception as e:
                        print(f"[Server] Heartbeat send error for {user_id}: {e}")
                        try:
                            s.close()
                        except:
                            pass
                        to_remove.append(user_id)
            with self.client_info_lock:
                for user_id in to_remove:
                    if user_id in self.client_info:
                        del self.client_info[user_id]

    def server_heartbeat_monitor(self):
        """Heartbeat monitoring thread between servers"""
        while True:
            time.sleep(self.heartbeat_interval)
            now = time.time()
            to_remove = []
            with self.server_list_lock:
                for server_id, info in list(self.server_list.items()):
                    s = info.get('socket')
                    last_active = info.get('last_active', 0)
                    if not s:
                        continue
                    if now - last_active > self.heartbeat_timeout:
                        global_ms.log_signal.emit(f"[Server] Server {server_id} heartbeat timeout, disconnecting.")
                        try:
                            s.close()
                        except:
                            pass
                        to_remove.append(server_id)
                        continue
                    try:
                        ping_msg = Packing('PING', b'')
                        s.send(ping_msg)
                        print(f"[Server] Sending PING to server {server_id}")
                    except Exception as e:
                        global_ms.log_signal.emit(f"[Server] Failed to send heartbeat to server {server_id}: {e}")
                        try:
                            s.close()
                        except:
                            pass
                        to_remove.append(server_id)
            with self.server_list_lock:
                for server_id in to_remove:
                    if server_id in self.server_list:
                        del self.server_list[server_id]
            global_ms.refresh_list_signal.emit()

    def handle_server_messages(self, server_socket, server_id):
        """Handle message interaction between servers"""
        try:
            while True:
                data = server_socket.recv(1024)
                if not data:
                    global_ms.log_signal.emit(f"[Server] Server {server_id} disconnected")
                    break

                # Update server's last active time
                with self.server_list_lock:
                    if server_id in self.server_list:
                        self.server_list[server_id]['last_active'] = time.time()

                purpose, length, payload = Unpacking(data)
                # print(f"[Server] Received message from server {server_id}: {purpose}")  # Commented out, to avoid console printing of ping/pong messages

                if purpose == 'PING':
                    pong_msg = Packing('PONG', b'')
                    server_socket.send(pong_msg)
                    print(f"[Server] Received PING from server {server_id}, replied PONG")
                elif purpose == 'PONG':
                    print(f"[Server] Received PONG from server {server_id} (heartbeat normal)")

                elif purpose == 'SEARCH_USERS':
                    # Handle user search request from other servers
                    QueryUsers = Message_pb2.QueryUsers()
                    QueryUsers.ParseFromString(payload)
                    query = QueryUsers.query
                    handle = QueryUsers.handle

                    # Collect local user information
                    QueryUsersResponse = Message_pb2.QueryUsersResponse()
                    QueryUsersResponse.handle = handle

                    with self.client_info_lock:
                        for user_id, info in self.client_info.items():
                            user = Message_pb2.User()
                            user.userId = str(user_id)
                            user.serverId = str(info['server_id'])
                            QueryUsersResponse.users.append(user)

                    # Reply search results to requesting server
                    response_msg = Packing('SEARCH_USERS_RESP', QueryUsersResponse.SerializeToString())
                    server_socket.send(response_msg)
                    global_ms.log_signal.emit(f"[Server] Replying SEARCH_USERS_RESP to server {server_id}, user count: {len(QueryUsersResponse.users)}")

                elif purpose == 'SEARCH_USERS_RESP':
                    # Handle search result response from other servers
                    QueryUsersResponse = Message_pb2.QueryUsersResponse()
                    QueryUsersResponse.ParseFromString(payload)
                    handle = QueryUsersResponse.handle

                    # Find client waiting for this response
                    target_client = None
                    with self.client_info_lock:
                        for user_id, info in self.client_info.items():
                            pending_search = info.get('pending_search')
                            if pending_search and pending_search['handle'] == handle:
                                target_client = info['socket']
                                break

                    if target_client:
                        # Forward search results to client
                        response_msg = Packing('SEARCH_USERS_RESP', payload)
                        target_client.send(response_msg)
                        global_ms.log_signal.emit(f"[Server] Forwarding search results from server {server_id} to client")

                elif purpose == 'MESSAGE':
                    # Handle message forwarding from other servers
                    msg = Message_pb2.ChatMessage()
                    msg.ParseFromString(payload)
                    which = msg.WhichOneof('recipient')

                    if which == 'user':
                        target_user = msg.user.userId
                        with self.client_info_lock:
                            if target_user in self.client_info:
                                # Forward message to local user
                                forward_msg = Packing('MESSAGE', payload)
                                self.client_info[target_user]['socket'].send(forward_msg)
                                global_ms.log_signal.emit(f"[Server] Forwarding message from server {server_id} to user {target_user}")
                            else:
                                global_ms.log_signal.emit(f"[Server] Target user {target_user} not on this server")

                elif purpose == 'MESSAGE_ACK':
                    # Handle message acknowledgment from other servers
                    ack = Message_pb2.ChatMessageResponse()
                    ack.ParseFromString(payload)
                    msg_snowflake = ack.messageSnowflake

                    # Find local user waiting for this ACK
                    with self.pending_acks_lock:
                        if msg_snowflake in self.pending_acks:
                            source_info = self.pending_acks[msg_snowflake]
                            source_user_id = source_info['source_user']

                            with self.client_info_lock:
                                if source_user_id in self.client_info:
                                    # Forward ACK to original sender
                                    ack_msg = Packing('MESSAGE_ACK', payload)
                                    self.client_info[source_user_id]['socket'].send(ack_msg)
                                    global_ms.log_signal.emit(f"[Server] Forwarding message ACK to user {source_user_id}")

                            del self.pending_acks[msg_snowflake]

                elif purpose == 'REMINDER':
                    # Handle REMINDER message from reminder server
                    try:
                        reminder = Message_pb2.Reminder()
                        reminder.ParseFromString(payload)

                        target_user_id = reminder.user.userId
                        event = reminder.reminderContent

                        # Check if target user is on this server (as homeserver)
                        with self.client_info_lock:
                            if target_user_id in self.client_info:
                                # User on this server, forward reminder to user
                                client_socket = self.client_info[target_user_id]['socket']
                                forward_msg = Packing('REMINDER', payload)
                                client_socket.send(forward_msg)
                                global_ms.log_signal.emit(f"[Server] Forwarding reminder from reminder server {server_id} to user {target_user_id}: {event}")
                            else:
                                global_ms.log_signal.emit(f"[Server] Target user {target_user_id} not on this server, cannot forward reminder")

                    except Exception as e:
                        global_ms.log_signal.emit(f"[Server] Failed to process REMINDER message from server {server_id}: {e}")

                else:
                    # Handle other server-server protocol messages
                    global_ms.log_signal.emit(f"[Server] Received unhandled message from server {server_id}: {purpose}")

        except Exception as e:
            global_ms.log_signal.emit(f"[Server] Error handling messages from server {server_id}: {e}")
        finally:
            # Clean up server connection information
            with self.server_list_lock:
                if server_id in self.server_list:
                    del self.server_list[server_id]
            global_ms.refresh_list_signal.emit()
            try:
                server_socket.close()
            except:
                pass 