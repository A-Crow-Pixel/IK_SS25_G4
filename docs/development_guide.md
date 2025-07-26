# Development Guide

## 📋 Development Environment Setup

### Environment Requirements
- Python 3.8+
- PySide6
- Protocol Buffers

### Install Dependencies
```bash
pip install -r requirements.txt
```

## 🏗️ Project Architecture

### Core Modules

#### Client Module (`client/`)
- `client.py` - Main client, includes chat history management
- `client_1.py` - Basic client implementation
- `client_2.py` - Client version 2
- `client_3.py` - Client version 3
- `client_1_modern.py` - Modern UI client

#### Server Module (`server/`)
- `server.py` - Server startup entry point
- `server_network.py` - Core network communication logic
- `server_ui.py` - Traditional server UI
- `modern_server_ui.py` - Modern server UI

#### Feature Modules (`modules/`)
- `PackingandUnpacking.py` - Message serialization/deserialization
- `Translator.py` - Translation functionality
- `reminder.py` - Reminder system
- `tips_widget.py` - Tips component

#### Protocol Module (`proto/`)
- `Message.proto` - Protocol buffer definitions
- `Message_pb2.py` - Generated Python code

## 🔧 Development Standards

### Code Style
- Follow PEP 8 standards
- Use type annotations
- Add detailed docstrings
- Keep code concise and readable

### Naming Conventions
- Class names: PascalCase
- Function names: snake_case
- Constants: UPPER_SNAKE_CASE
- Variables: snake_case

### File Organization
```
project/
├── client/          # Client code
├── server/          # Server code
├── modules/         # Shared modules
├── proto/           # Protocol definitions
├── docs/            # Documentation
└── tests/           # Test code
```

## 🌐 Network Communication Protocol

### Message Format
```python
# Message header format
purpose length payload\n

# Example
MESSAGE 45 {"text": "Hello World"}\n
```

### Main Message Types
- `CONNECT_CLIENT` - Client connection
- `MESSAGE` - Chat message
- `CREATE_GROUP` - Create group
- `JOIN_GROUP` - Join group
- `REMINDER` - Reminder message
- `TRANSLATE` - Translation request

### Network Architecture
```
Client A ←→ Server 1 ←→ Server 2 ←→ Client B
```

## 🎨 UI Development

### PySide6 Component Usage
```python
from PySide6.QtWidgets import *
from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QTextCursor

# Signal definition
class MySignals(QObject):
```

### Modern UI Components
```python
from rrd_widgets import (
    TipsWidget, TipsStatus,
    SimpleButton_1, SimpleButton_2,
    CardBoxDeletable
)
```

### Responsive Layout
```python
# Use QSplitter for adjustable layout
splitter = QSplitter(Qt.Horizontal)
splitter.addWidget(user_list)
splitter.addWidget(chat_area)
splitter.setSizes([300, 700])
```

## 🔄 Translation Functionality

### Translation Flow
1. User selects target language
2. Client sends translation request
3. Server calls Google Translate API
4. Returns translation result
5. Client displays translated content

### Language Mapping
```python
language_map = {
    'Deutsch': 'de',
    'English': 'en', 
    'Chinese': 'zh-CN',
    'Türkçe': 'tr'
}
```

## ⏰ Reminder System

### Reminder Manager
- `ReminderManagerSimple` - Simple polling implementation
- `ReminderManagerHeap` - Priority queue implementation (recommended)

### Reminder Data Structure
```python
reminder = {
    'user_id': 'user1',
    'event': 'Meeting reminder',
    'trigger_time': timestamp,
    'countdown_seconds': 3600
}
```

## 🧪 Testing

### Unit Tests
```bash
python -m pytest tests/
```

### Integration Tests
```bash
# Start test server
python server/server.py --serverid TestServer --udpport 9999 --tcpport 65433

# Start test client
python client/client.py
```

## 🚀 Deployment

### Development Environment
```bash
# Start development server
python run_server.py

# Start development client
python run_client.py
```

### Production Environment
```bash
# Use systemd service
sudo systemctl enable internetkommunikation-server
sudo systemctl start internetkommunikation-server
```

## 📝 Debugging Tips

### Logging
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Debug information")
```

### Network Debugging
```python
# Enable network logging
global_ms.log_signal.emit(f"[DEBUG] Sending message: {message}")
```

### UI Debugging
```python
# Use Qt debugging tools
from PySide6.QtCore import QTimer
QTimer.singleShot(1000, lambda: print("UI state:", widget.isVisible()))
```

## �� Related Resources

- [PySide6 Documentation](https://doc.qt.io/qtforpython/)
- [Protocol Buffers Guide](https://developers.google.com/protocol-buffers)
- [Google Translate API](https://cloud.google.com/translate)
- [Python Network Programming](https://docs.python.org/3/library/socket.html) 