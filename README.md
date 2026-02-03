# Internetkommunikation_Project_Gruppe4

## 📖 Project Overview

Internetkommunikation_Project_Gruppe4 is a modern chat application developed with Python and PySide6, supporting multi-user real-time communication, group management, message translation, reminder functionality, and other features.

## 👥 Team Members

| | | |
| :--- | :--- | :--- |
| **Yanan Wang** | **Sizhe Cen** | **Rui Ying** |
| **Jingsong Lin** | **Wenhao Cheng** | **Zewen Yang** |

---

## 🚀 Quick Start

### Start Server
```bash
python run_server.py
```

Optional parameters:
```bash
python run_server.py --serverid Server_4 --udpport 9999 --tcpport 65433
```

**Note**: You can also use server.py directly for more detailed configuration:
```bash
python server/server.py --serverid Server_5 --udpport 65432 --tcpport 65433
```

### Start Client
```bash
python run_client.py
```

### Direct Launch (Advanced Users)
```bash
# Server
cd server
python server.py --serverid Server_4 --udpport 9999 --tcpport 65433

# Client
cd client
python client.py
```

**Custom Configuration Example**:
```bash
# Use different server ID and ports
python server/server.py --serverid Server_5 --udpport 65432 --tcpport 65433
```

## 📁 Project Structure

```
internetkommunikation_project_gruppe4/
├── run_client.py          # Client startup script
├── run_server.py          # Server startup script
├── client/                # Client code
│   ├── client.py          # Main client (recommended)
│   ├── client_1.py        # Basic client
│   ├── client_2.py        # Client version 2
│   ├── client_3.py        # Client version 3
│   ├── client_1_modern.py # Modern client
│   ├── gui/               # GUI components
│   └── ui/                # UI files
├── server/                # Server code
│   ├── server.py          # Server startup
│   ├── server_network.py  # Network communication
│   ├── server_ui.py       # Server UI
│   └── modern_server_ui.py # Modern server UI
├── modules/               # Feature modules
│   ├── PackingandUnpacking.py # Message packing/unpacking
│   ├── Translator.py      # Translation functionality
│   ├── reminder.py        # Reminder system
│   └── tips_widget.py     # Tips component
├── proto/                 # Protocol definitions
├── docs/                  # Documentation
└── requirements.txt       # Dependency configuration
```

## 🔧 Dependency Installation

```bash
pip install -r requirements.txt
```

## ✨ Main Features

### 💬 Real-time Chat
- Multi-user real-time message communication
- Group chat functionality
- Message history records
- Online status display

### 🌐 Network Communication
- TCP/UDP hybrid communication
- Server auto-discovery
- Cross-server message forwarding
- Heartbeat detection mechanism

### 🔄 Translation Functionality
- Multi-language translation support (Chinese, English, German, Turkish)
- Real-time message translation
- Automatic language detection
- Translation switch control

### ⏰ Reminder System
- Scheduled reminder functionality
- Event reminder management
- Reminder notification display
- Priority queue management

### 🎨 Modern Interface
- Responsive layout design
- Multi-tab chat system
- Beautiful message bubbles
- Modern UI components

## 📚 Detailed Documentation

- [Documentation Index](docs/INDEX.md) - Complete documentation overview
- [Development Guide](docs/development_guide.md) - Development related documentation
- [User Guide](docs/user_guide.md) - User usage guide
- [API Documentation](docs/api_documentation.md) - Interface documentation
- [Deployment Guide](docs/deployment_guide.md) - Deployment related documentation
- [Translation Flow](docs/translation_flow.md) - Detailed translation functionality flowchart

## 🔄 Translation Flow

### Translation Functionality Workflow

```
User selects language
    ↓
Language selection decision
    ├─ Original → Send normal message → Server forwards → Target user receives → Display message
    └─ Other languages → Send translation request → Translation processing → Google Translate API → Return translation result → Target user receives → Display translated message
```

### Detailed Step Description

1. **User selects language**
   - Select target language in client interface (Original/Deutsch/English/Chinese/Türkçe)

2. **Message processing branch**
   - **Original**: Send normal message directly, no translation
   - **Other languages**: Send translation request, including original text and target language

3. **Server processing**
   - Receive translation request
   - Call Google Translate API
   - Generate translation result

4. **Message forwarding**
   - Forward translated message to target user
   - Maintain association between original and translated messages

5. **Client display**
   - Target user receives message
   - Display corresponding content based on language settings

### Supported Languages

| Language Option | Target Language | Language Code |
|-----------------|-----------------|---------------|
| Original | No translation | - |
| Deutsch | German | de |
| English | English | en |
| Chinese | Chinese | zh-CN |
| Türkçe | Turkish | tr |

## 📄 License

This project uses the MIT License.

## 📚 Project Repository

Project hosted on [LRZ GitLab](https://gitlab.lrz.de/00000000014AEF26/internetkommunikation_project_gruppe4.git) 
