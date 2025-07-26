import inspect

def Packing(purpose: str, data: bytes) -> bytes:
    """
    Pack a message with header information for network transmission.
    
    Args:
        purpose (str): The message purpose/type identifier.
        data (bytes): The message payload data.
    
    Returns:
        bytes: The complete message with header and payload.
    """
    purpose = purpose
    length = len(data)
    header = f'{purpose} {length} '.encode('ascii')
    fullmessage = header + data + b'\n'
    
    # Add message sending log record
    log_message_send_safe(purpose, data)
    
    return fullmessage

def Unpacking(data: bytes):
    """
    Unpack received data to extract message purpose, length, and payload.
    
    Args:
        data (bytes): The raw received data.
    
    Returns:
        tuple: A tuple containing (purpose, length, payload).
    """
    buffer = b''
    """
    Input newly received data to the unpacker, returns a list of parsed (purpose, length, payload) tuples.
    """
    buffer += data
    purpose = ''
    length = 0
    payload = b''

    while True:
        try:
            # 1. Find first space
            first_space = buffer.index(b' ')
            # 2. Find second space
            second_space = buffer.index(b' ', first_space + 1)
            # 3. Extract purpose and length
            purpose = buffer[:first_space].decode('ascii')
            length_str = buffer[first_space + 1:second_space].decode('ascii')
            length = int(length_str)

            # 4. Find payload end (payload must end with \n)
            # payload start position: second_space + 1
            payload_end = second_space + 1 + length
            # Must ensure buffer has enough data (including trailing \n)
            if len(buffer) < payload_end + 1:
                break  # Not enough data, wait for next time

            payload = buffer[second_space + 1:payload_end]
            if buffer[payload_end:payload_end + 1] != b'\n':
                # Protocol mismatch
                raise ValueError("Package format error, payload does not end with newline")

            # Move buffer
            buffer = buffer[payload_end + 1:]
            
            # Log immediately after successful unpacking
            log_message_receive_safe(purpose, payload)
            
        except ValueError:
            break  # Cannot find space, etc., indicating incomplete header

    return purpose, length, payload

def log_message_send_safe(purpose, payload):
    """
    Safely log sent message information without causing import errors.
    
    Args:
        purpose (str): The message purpose/type.
        payload (bytes): The message payload data.
    """
    try:
        # 完全过滤ping/pong消息，不在ChatHistory中显示
        if purpose in ['PING', 'PONG']:
            return
            
        # 获取调用栈信息，找到调用Packing的代码行号
        frame = inspect.currentframe()
        if frame and frame.f_back:
            # 尝试不同的调用栈层次
            caller_frame = frame.f_back  # 先尝试一层
            if caller_frame.f_code.co_name == 'Packing' and caller_frame.f_back:
                caller_frame = caller_frame.f_back  # 如果是从Packing调用的，再往上一层
            
            line_number = caller_frame.f_lineno
            filename = caller_frame.f_code.co_filename.split('\\')[-1]  # 获取文件名
            
            # 构造详细的日志消息
            payload_size = len(payload) if payload else 0
            
            # 获取payload的实际内容
            payload_content = get_payload_content(payload, purpose)
            
            # 构造日志消息
            log_text = f"[send] [{filename}:{line_number}] '{purpose} {payload_size} <{payload_content}>'"
            
            # 智能双重输出：检测运行环境
            try:
                try:
                    from server.modern_server_ui import global_ms as modern_global_ms
                    modern_global_ms.message_log_signal.emit(log_text)
                except ImportError:
                    from server.server_ui import global_ms
                    global_ms.message_log_signal.emit(log_text)
            except (ImportError, AttributeError, Exception):
                # 导入失败或其他错误，直接输出到控制台
                print(log_text)
    except Exception as e:
        # 如果出现任何错误，静默忽略，不影响正常的消息处理
        pass

def log_message_receive_safe(purpose, payload):
    """
    Safely log received message information without causing import errors.
    
    Args:
        purpose (str): The message purpose/type.
        payload (bytes): The message payload data.
    """
    try:
        # 完全过滤ping/pong消息，不在ChatHistory中显示
        if purpose in ['PING', 'PONG']:
            return
            
        # 获取调用栈信息
        frame = inspect.currentframe()
        if frame and frame.f_back:
            # 尝试不同的调用栈层次
            caller_frame = frame.f_back  # 先尝试一层
            if caller_frame.f_code.co_name == 'Unpacking' and caller_frame.f_back:
                caller_frame = caller_frame.f_back  # 如果是从Unpacking调用的，再往上一层
            
            line_number = caller_frame.f_lineno
            filename = caller_frame.f_code.co_filename.split('\\')[-1]  # 获取文件名
            
            # 构造详细的日志消息
            payload_size = len(payload) if payload else 0
            
            # 获取payload的实际内容
            payload_content = get_payload_content(payload, purpose)
            
            # 构造日志消息
            log_text = f"[receive] [{filename}:{line_number}] '{purpose} {payload_size} <{payload_content}>'"
            
            # 智能双重输出：检测运行环境
            try:
                try:
                    from server.modern_server_ui import global_ms as modern_global_ms
                    modern_global_ms.message_log_signal.emit(log_text)
                except ImportError:
                    from server.server_ui import global_ms
                    global_ms.message_log_signal.emit(log_text)
            except (ImportError, AttributeError, Exception):
                # 导入失败或其他错误，直接输出到控制台
                print(log_text)
    except Exception as e:
        # 如果出现任何错误，静默忽略，不影响正常的消息处理
        pass

def get_payload_content(payload, purpose=None):
    """
    Get a human-readable representation of the payload content.
    
    Args:
        payload (bytes): The message payload data.
        purpose (str, optional): The message purpose for context.
    
    Returns:
        str: A string representation of the payload content.
    """
    try:
        if not payload:
            return "empty"
        
        # 尝试解析protobuf格式（如果提供了purpose参数）
        if purpose:
            protobuf_content = parse_protobuf_content(payload, purpose)
            if protobuf_content:
                return protobuf_content
        
        # 回退到原有的显示方法
        # 方法1：尝试显示为UTF-8字符串（对于简单的文本内容）
        try:
            # 检查是否包含可打印字符
            decoded = payload.decode('utf-8', errors='ignore')
            # 只保留可打印字符，保留换行符让其真正换行
            printable_chars = ''.join(c for c in decoded if c.isprintable() or c in '\n\r\t')
            if printable_chars and len(printable_chars.strip()) > 0:
                # 限制显示长度，避免日志过长
                if len(printable_chars) > 100:
                    return f"{printable_chars[:100]}..."
                # 不转义换行符，让其在UI中真正换行
                return printable_chars.replace('\r', '\\r').replace('\t', '\\t')
        except:
            pass
        
        # 方法2：显示为hex格式（对于二进制数据）
        hex_str = payload.hex()
        if len(hex_str) > 200:  # 限制hex显示长度
            return f"{hex_str[:200]}..."
        return hex_str
        
    except Exception:
        # 如果都失败了，返回基本信息
        return f"{len(payload)} bytes of data"

def parse_protobuf_content(payload, purpose):
    """
    Parse protobuf content based on the message purpose.
    
    Args:
        payload (bytes): The protobuf serialized data.
        purpose (str): The message purpose to determine parsing method.
    
    Returns:
        str: A string representation of the parsed protobuf content.
    """
    try:
        # 动态导入避免循环导入
        import Message_pb2
        
        if purpose == 'MESSAGE':
            msg = Message_pb2.ChatMessage()
            msg.ParseFromString(payload)
            fields = []
            if msg.messageSnowflake:
                fields.append(f"snowflake={msg.messageSnowflake}")
            if msg.HasField('author'):
                fields.append(f"author.userId={msg.author.userId}")
                fields.append(f"author.serverId={msg.author.serverId}")
            # 检查recipient类型
            if msg.HasField('user'):
                fields.append(f"to.userId={msg.user.userId}")
            elif msg.HasField('group'):
                fields.append(f"to.groupId={msg.group.groupId}")
            elif msg.HasField('userOfGroup'):
                fields.append(f"to.userOfGroup={msg.userOfGroup.user.userId}@{msg.userOfGroup.group.groupId}")
            # 检查content字段类型 (oneof content)
            if msg.HasField('textContent'):
                content = msg.textContent[:50] + "..." if len(msg.textContent) > 50 else msg.textContent
                fields.append(f"content=textContent:{content}")
            elif msg.HasField('live_location'):
                fields.append(f"content=live_location:lat:{msg.live_location.location.latitude},lng:{msg.live_location.location.longitude}")
                if msg.live_location.HasField('user'):
                    fields.append(f"location.user={msg.live_location.user.userId}")
                if msg.live_location.timestamp:
                    fields.append(f"location.timestamp={msg.live_location.timestamp}")
            elif msg.HasField('translation'):
                lang_names = {0: 'DE', 1: 'EN', 2: 'ZH', 3: 'TR'}
                trans_fields = [f"lang={lang_names.get(msg.translation.target_language, 'UNKNOWN')}"]
                if msg.translation.original_text:
                    orig = msg.translation.original_text[:30] + "..." if len(msg.translation.original_text) > 30 else msg.translation.original_text
                    trans_fields.append(f"original={orig}")
                if hasattr(msg.translation, 'translated_text') and msg.translation.translated_text:
                    trans = msg.translation.translated_text[:30] + "..." if len(msg.translation.translated_text) > 30 else msg.translation.translated_text
                    trans_fields.append(f"translated={trans}")
                fields.append(f"content=translation:{', '.join(trans_fields)}")
            else:
                # 如果没有content字段，标记为空
                fields.append("content=empty")
            return ", ".join(fields)
            
        elif purpose == 'CONNECT_CLIENT':
            msg = Message_pb2.ConnectClient()
            msg.ParseFromString(payload)
            fields = []
            if msg.HasField('user'):
                fields.append(f"user.userId={msg.user.userId}")
                fields.append(f"user.serverId={msg.user.serverId}")
            return ", ".join(fields)
            
        elif purpose == 'CONNECT_SERVER':
            msg = Message_pb2.ConnectServer()
            msg.ParseFromString(payload)
            fields = [f"serverId={msg.serverId}"]
            if msg.features:
                features = list(msg.features)[:3]
                if len(msg.features) > 3:
                    features.append(f"...+{len(msg.features)-3}more")
                fields.append(f"features=[{', '.join(features)}]")
            return ", ".join(fields)
            
        elif purpose == 'CONNECTED':
            msg = Message_pb2.ConnectResponse()
            msg.ParseFromString(payload)
            result_names = {0: 'UNKNOWN_ERROR', 1: 'CONNECTED', 2: 'IS_ALREADY_CONNECTED_ERROR'}
            return f"result={result_names.get(msg.result, f'CODE_{msg.result}')}"
            
        elif purpose == 'HANGUP':
            msg = Message_pb2.HangUp()
            msg.ParseFromString(payload)
            reason_names = {0: 'UNKNOWN_REASON', 1: 'EXIT', 2: 'TIMEOUT', 3: 'PAYLOAD_LIMIT_EXCEEDED', 4: 'MESSAGE_MALFORMED'}
            return f"reason={reason_names.get(msg.reason, f'CODE_{msg.reason}')}"
            
        elif purpose == 'SERVER_ANNOUNCE':
            msg = Message_pb2.ServerAnnounce()
            msg.ParseFromString(payload)
            fields = [f"serverId={msg.serverId}"]
            if msg.feature:
                feature_list = [f"{f.featureName}:{f.port}" for f in msg.feature[:3]]
                if len(msg.feature) > 3:
                    feature_list.append(f"...+{len(msg.feature)-3}more")
                fields.append(f"features=[{', '.join(feature_list)}]")
            return ", ".join(fields)
            
        elif purpose == 'MESSAGE_ACK' or purpose == 'CHATMESSAGERESPONSE':
            msg = Message_pb2.ChatMessageResponse()
            msg.ParseFromString(payload)
            fields = [f"snowflake={msg.messageSnowflake}"]
            if msg.statuses:
                status_names = {0: 'UNKNOWN_STATUS', 2: 'DELIVERED', 3: 'OTHER_ERROR', 4: 'USER_AWAY', 5: 'USER_NOT_FOUND', 6: 'OTHER_SERVER_TIMEOUT', 7: 'OTHER_SERVER_NOT_FOUND', 8: 'USER_BLOCKED'}
                status_list = []
                for status in msg.statuses[:3]:
                    status_name = status_names.get(status.status, f'CODE_{status.status}')
                    status_list.append(f"{status.user.userId}:{status_name}")
                if len(msg.statuses) > 3:
                    status_list.append(f"...+{len(msg.statuses)-3}more")
                fields.append(f"statuses=[{', '.join(status_list)}]")
            return ", ".join(fields)
            
        elif purpose == 'SEARCH_USERS':
            msg = Message_pb2.QueryUsers()
            msg.ParseFromString(payload)
            fields = [f"handle={msg.handle}"]
            if msg.query:
                fields.append(f"query={msg.query}")
            return ", ".join(fields)
            
        elif purpose == 'SEARCH_USERS_RESP':
            msg = Message_pb2.QueryUsersResponse()
            msg.ParseFromString(payload)
            fields = [f"handle={msg.handle}"]
            if len(msg.users) > 0:
                user_list = [f"{user.userId}@{user.serverId}" for user in msg.users[:3]]
                if len(msg.users) > 3:
                    user_list.append(f"...+{len(msg.users)-3}more")
                fields.append(f"users=[{', '.join(user_list)}]")
            return ", ".join(fields)
            
        elif purpose == 'MODIFY_GROUP':
            msg = Message_pb2.ModifyGroup()
            msg.ParseFromString(payload)
            fields = [f"handle={msg.handle}", f"groupId={msg.groupId}"]
            if msg.deleteGroup:
                fields.append("action=DELETE")
            else:
                fields.append("action=MODIFY")
            if msg.displayName:
                fields.append(f"displayName={msg.displayName}")
            if msg.admins:
                admin_list = [admin.userId for admin in msg.admins[:3]]
                if len(msg.admins) > 3:
                    admin_list.append(f"...+{len(msg.admins)-3}more")
                fields.append(f"admins=[{', '.join(admin_list)}]")
            return ", ".join(fields)
            
        elif purpose == 'MODIFY_GROUP_RESP':
            msg = Message_pb2.ModifyGroupResponse()
            msg.ParseFromString(payload)
            result_names = {0: 'UNKNOWN_ERROR', 1: 'SUCCESS', 2: 'NOT_PERMITTED'}
            return f"handle={msg.handle}, result={result_names.get(msg.result, f'CODE_{msg.result}')}"
            
        elif purpose == 'INVITE_GROUP':
            msg = Message_pb2.InviteToGroup()
            msg.ParseFromString(payload)
            fields = [f"handle={msg.handle}", f"groupId={msg.groupId}"]
            if msg.HasField('user'):
                fields.append(f"user={msg.user.userId}")
            return ", ".join(fields)
            
        elif purpose == 'NOTIFY_GROUP_INVITE':
            msg = Message_pb2.NotifyGroupInvite()
            msg.ParseFromString(payload)
            fields = [f"handle={msg.handle}"]
            if msg.HasField('group'):
                fields.append(f"group={msg.group.groupId}@{msg.group.serverId}")
            return ", ".join(fields)
            
        elif purpose == 'JOIN_GROUP':
            msg = Message_pb2.JoinGroup()
            msg.ParseFromString(payload)
            fields = [f"handle={msg.handle}"]
            if msg.HasField('group'):
                fields.append(f"group={msg.group.groupId}")
            if msg.HasField('user'):
                fields.append(f"user={msg.user.userId}")
            return ", ".join(fields)
            
        elif purpose == 'LEAVE_GROUP':
            msg = Message_pb2.LeaveGroup()
            msg.ParseFromString(payload)
            fields = []
            if msg.HasField('group'):
                fields.append(f"group={msg.group.groupId}")
            if msg.HasField('user'):
                fields.append(f"user={msg.user.userId}")
            return ", ".join(fields)
            
        elif purpose == 'QUERY_GROUP_MEMBERS':
            msg = Message_pb2.ListGroupMembers()
            msg.ParseFromString(payload)
            if msg.HasField('group'):
                return f"group={msg.group.groupId}@{msg.group.serverId}"
            return "empty"
            
        elif purpose == 'GROUP_MEMBERS':
            msg = Message_pb2.GroupMembers()
            msg.ParseFromString(payload)
            fields = []
            if msg.HasField('group'):
                fields.append(f"group={msg.group.groupId}")
            result_names = {0: 'UNKNOWN_ERROR', 1: 'SUCCESS', 2: 'NOT_FOUND'}
            fields.append(f"result={result_names.get(msg.result, f'CODE_{msg.result}')}")
            if msg.user:
                user_list = [user.userId for user in msg.user[:5]]
                if len(msg.user) > 5:
                    user_list.append(f"...+{len(msg.user)-5}more")
                fields.append(f"members=[{', '.join(user_list)}]")
            return ", ".join(fields)
            
        elif purpose == 'SET_REMINDER':
            msg = Message_pb2.SetReminder()
            msg.ParseFromString(payload)
            fields = []
            if msg.HasField('user'):
                fields.append(f"user={msg.user.userId}")
            if msg.event:
                event = msg.event[:30] + "..." if len(msg.event) > 30 else msg.event
                fields.append(f"event={event}")
            if msg.countdownSeconds:
                fields.append(f"countdown={msg.countdownSeconds}s")
            return ", ".join(fields)
            
        elif purpose == 'REMINDER':
            msg = Message_pb2.Reminder()
            msg.ParseFromString(payload)
            fields = []
            if msg.HasField('user'):
                fields.append(f"user={msg.user.userId}")
            if msg.reminderContent:
                content = msg.reminderContent[:50] + "..." if len(msg.reminderContent) > 50 else msg.reminderContent
                fields.append(f"content={content}")
            return ", ".join(fields)
            
        elif purpose == 'LIVE_LOCATION':
            msg = Message_pb2.LiveLocation()
            msg.ParseFromString(payload)
            fields = []
            if msg.HasField('user'):
                fields.append(f"user={msg.user.userId}")
            if msg.timestamp:
                fields.append(f"timestamp={msg.timestamp}")
            if msg.HasField('location'):
                fields.append(f"lat={msg.location.latitude}")
                fields.append(f"lng={msg.location.longitude}")
            return ", ".join(fields)
            
        elif purpose == 'LIVE_LOCATIONS':
            msg = Message_pb2.LiveLocations()
            msg.ParseFromString(payload)
            if msg.extended_live_locations:
                count = len(msg.extended_live_locations)
                return f"locations_count={count}"
            return "empty"
            
        elif purpose == 'TRANSLATE':
            msg = Message_pb2.Translate()
            msg.ParseFromString(payload)
            fields = []
            lang_names = {0: 'DE', 1: 'EN', 2: 'ZH'}
            fields.append(f"target_lang={lang_names.get(msg.target_language, 'UNKNOWN')}")
            if msg.original_text:
                orig = msg.original_text[:30] + "..." if len(msg.original_text) > 30 else msg.original_text
                fields.append(f"original_text={orig}")
            if hasattr(msg, 'translated_text') and msg.translated_text:
                trans = msg.translated_text[:30] + "..." if len(msg.translated_text) > 30 else msg.translated_text
                fields.append(f"translated_text={trans}")
            return ", ".join(fields)
            
        elif purpose == 'TRANSLATED':
            msg = Message_pb2.Translated()
            msg.ParseFromString(payload)
            fields = []
            lang_names = {0: 'DE', 1: 'EN', 2: 'ZH'}
            fields.append(f"target_lang={lang_names.get(msg.target_language, 'UNKNOWN')}")
            if msg.original_text:
                orig = msg.original_text[:30] + "..." if len(msg.original_text) > 30 else msg.original_text
                fields.append(f"original_text={orig}")
            if hasattr(msg, 'translated_text') and msg.translated_text:
                trans = msg.translated_text[:30] + "..." if len(msg.translated_text) > 30 else msg.translated_text
                fields.append(f"translated_text={trans}")
            return ", ".join(fields)
            
        elif purpose == 'UNSUPPORTED_MESSAGE_NOTIFICATION':
            msg = Message_pb2.UnsupportedMessageNotification()
            msg.ParseFromString(payload)
            return f"unsupported_message={msg.message_name}"
            
        elif purpose == 'DISCOVER_SERVER':
            # DiscoverServer消息为空
            return "discovery_request"
            
        # PING/PONG已经在上层被过滤掉了，这里不需要处理
        
        # 其他未知类型，返回None让它回退到原有显示方法
        return None
        
    except Exception:
        # 如果protobuf解析失败，返回None让它回退到原有显示方法
        return None

def get_safe_payload_preview(purpose, payload):
    """
    Get a safe preview of the payload content for logging purposes.
    
    Args:
        purpose (str): The message purpose/type.
        payload (bytes): The message payload data.
    
    Returns:
        str: A safe string representation of the payload.
    """
    try:
        if not payload:
            return ""
            
        # 对于一些简单的消息类型，尝试提取基本信息
        if purpose == 'CONNECTED' and len(payload) >= 1:
            # ConnectResponse通常只有一个字段，可以安全地检查第一个字节
            result_code = payload[0] if payload else 0
            result_names = {0: 'UNKNOWN_ERROR', 1: 'CONNECTED', 2: 'ALREADY_CONNECTED'}
            return f"result={result_names.get(result_code, f'CODE_{result_code}')}"
        
        elif purpose == 'SERVER_ANNOUNCE':
            # 可以尝试提取服务器ID（通常在开头）
            return "server announcement"
            
        elif purpose in ['MESSAGE', 'SEARCH_USERS', 'CONNECT_CLIENT', 'CONNECT_SERVER']:
            # 对于复杂消息，只显示大小信息
            return f"payload_size={len(payload)}"
            
        else:
            return ""
            
    except Exception:
        return ""
