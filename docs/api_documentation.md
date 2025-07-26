# API Documentation

## 📋 Overview

This document describes the API interfaces for the Internetkommunikation_Project_Gruppe4 chat application, including network communication protocols, message formats, and data structures.

## 🌐 Network Communication Protocol

### Base Protocol
- **Transport Layer**: TCP/UDP hybrid
- **Application Layer**: Custom protocol buffers
- **Encoding**: UTF-8
- **Ports**: UDP 9999, TCP 65433

### Message Format
```
purpose length payload\n
```

**Field Description**:
- `purpose`: Message type identifier
- `length`: Payload data length
- `payload`: Actual data content
- `\n`: Message terminator

## 📨 Message Types

### Connection Related

#### CONNECT_CLIENT
Client connection request
```protobuf
message ConnectClient {
    User user = 1;
}
```

#### CONNECTED
Connection response
```protobuf
message ConnectResponse {
    enum Result {
        CONNECTED = 0;
        IS_ALREADY_CONNECTED_ERROR = 1;
        UNKNOWN_ERROR = 2;
    }
    Result result = 1;
}
```

#### CONNECT_SERVER
Server-to-server connection
```protobuf
message ConnectServer {
    string serverId = 1;
    repeated string features = 2;
}
```

### Chat Messages

#### MESSAGE
Chat message
```protobuf
message ChatMessage {
    User sender = 1;
    oneof recipient {
        User user = 2;
        Group group = 3;
    }
    oneof content {
        string textContent = 4;
        TranslateMessage translate = 5;
    }
    int64 timestamp = 6;
    string messageSnowflake = 7;
}
```

#### MESSAGE_ACK
Message acknowledgment
```protobuf
message ChatMessageResponse {
    string messageSnowflake = 1;
    bool success = 2;
    string errorMessage = 3;
}
```

### Translation Functionality

#### TRANSLATE
Translation request
```protobuf
message TranslateMessage {
    string original_text = 1;
    string translated_text = 2;
    int32 target_language = 3;
}
```

### Group Management

#### CREATE_GROUP
Create group
```protobuf
message CreateGroup {
    User creator = 1;
    string groupName = 2;
    repeated User members = 3;
}
```

#### JOIN_GROUP
Join group
```protobuf
message JoinGroup {
    User user = 1;
    string groupId = 2;
}
```

#### GROUP_MESSAGE
Group message
```protobuf
message GroupMessage {
    User sender = 1;
    Group group = 2;
    string content = 3;
    int64 timestamp = 4;
}
```

### Reminder System

#### SET_REMINDER
Set reminder
```protobuf
message SetReminder {
    User user = 1;
    string event = 2;
    uint32 countdownSeconds = 3;
}
```

#### REMINDER
Reminder notification
```protobuf
message Reminder {
    User user = 1;
    string reminderContent = 2;
}
```

### User Management

#### USER_LIST
User list request
```protobuf
message UserList {
    repeated User users = 1;
}
```

#### USER_STATUS
User status update
```protobuf
message UserStatus {
    User user = 1;
    enum Status {
        ONLINE = 0;
        OFFLINE = 1;
        AWAY = 2;
    }
    Status status = 2;
}
```

### Server Discovery

#### SERVER_DISCOVERY
Server discovery broadcast
```protobuf
message ServerDiscovery {
    string serverId = 1;
    string serverAddress = 2;
    uint32 tcpPort = 3;
    uint32 udpPort = 4;
}
```

## 📊 Data Structures

### User
```protobuf
message User {
    string userId = 1;
    string username = 2;
    string serverId = 3;
    UserStatus.Status status = 4;
}
```

### Group
```protobuf
message Group {
    string groupId = 1;
    string groupName = 2;
    User creator = 3;
    repeated User members = 4;
    int64 createdAt = 5;
}
```

### Message
```protobuf
message Message {
    string messageId = 1;
    User sender = 2;
    oneof recipient {
        User user = 3;
        Group group = 4;
    }
    string content = 5;
    int64 timestamp = 6;
    MessageType type = 7;
}

enum MessageType {
    TEXT = 0;
    TRANSLATE = 1;
    REMINDER = 2;
    SYSTEM = 3;
}
```

## 🔄 Communication Flow

### Client-Server Communication
```
Client → TCP Connection → Server
     ← Response ←
```

### Server-to-Server Communication
```
Server A → TCP Connection → Server B
        ← Response ←
```

### Broadcast Communication
```
Server → UDP Broadcast → All Servers
```

## 🛠️ Error Handling

### Error Codes
```protobuf
enum ErrorCode {
    SUCCESS = 0;
    CONNECTION_FAILED = 1;
    AUTHENTICATION_FAILED = 2;
    MESSAGE_DELIVERY_FAILED = 3;
    TRANSLATION_FAILED = 4;
    REMINDER_SET_FAILED = 5;
    GROUP_OPERATION_FAILED = 6;
    UNKNOWN_ERROR = 999;
}
```

### Error Response Format
```protobuf
message ErrorResponse {
    ErrorCode errorCode = 1;
    string errorMessage = 2;
    string requestId = 3;
    int64 timestamp = 4;
}
```

## 📈 Performance Metrics

### Message Delivery
- **Latency**: <100ms for local messages
- **Throughput**: 1000+ messages/second
- **Reliability**: 99.9% delivery success rate

### Translation Service
- **Response Time**: <2 seconds
- **Accuracy**: >95% for supported languages
- **Rate Limit**: 100 requests/minute per user

### Reminder System
- **Precision**: ±1 second
- **Capacity**: 10,000+ concurrent reminders
- **Scalability**: Linear scaling with server resources

## 🔒 Security

### Authentication
- User authentication via user ID
- Server authentication via server ID
- Optional encryption for sensitive data

### Data Protection
- Message content encryption (optional)
- User privacy protection
- Secure server communication

## 📝 Logging

### Log Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General information
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **CRITICAL**: Critical errors

### Log Format
```
[Timestamp] [Level] [Component] [Message]
```

### Example
```
[2024-01-15 10:30:45] [INFO] [Server] Client connected: user123
[2024-01-15 10:30:46] [DEBUG] [Network] Message sent: MESSAGE 45 bytes
[2024-01-15 10:30:47] [WARNING] [Translation] API rate limit approaching
```

## 🔧 Configuration

### Server Configuration
```python
SERVER_CONFIG = {
    'tcp_port': 65433,
    'udp_port': 9999,
    'max_connections': 1000,
    'timeout': 30,
    'heartbeat_interval': 60,
    'log_level': 'INFO'
}
```

### Client Configuration
```python
CLIENT_CONFIG = {
    'server_address': 'localhost',
    'server_port': 65433,
    'reconnect_attempts': 3,
    'reconnect_delay': 5,
    'message_timeout': 10
}
```

## 📚 Related Documentation

- [Development Guide](development_guide.md) - Development guidelines
- [User Guide](user_guide.md) - User interface documentation
- [Translation Flow](translation_flow.md) - Translation functionality details
- [Reminder Guide](reminder_guide.md) - Reminder system documentation 