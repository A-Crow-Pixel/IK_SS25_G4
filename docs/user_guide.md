# User Guide

## 🚀 Quick Start

### Launch Application
1. **Start Server**
   ```bash
   python run_server.py
   ```

2. **Start Client**
   ```bash
   python run_client.py
   ```

3. **Connect to Server**
   - Click "Connect to Server" button
   - Select available server
   - Enter username and server ID

## 💬 Basic Functions

### Send Messages
1. Enter message content in the input box
2. Click "Send" button or press `Ctrl+Enter`
3. Message will appear in the chat history area

### Select Chat Target
- Select target in the left user/group list
- Click username or group name to start chat
- Support chatting with multiple users/groups simultaneously

### Group Functions
- **Create Group**: Click "+" button, select "Create Group"
- **Join Group**: Click "+" button, select "Join Group"
- **Invite Users**: Click "Invite" button in group
- **Leave Group**: Click "Leave" button in group

## 🔄 Translation Functionality

### Using Translation
1. Select target language in the language dropdown menu:
   - **Original** - No translation
   - **Deutsch** - German
   - **English** - English
   - **Chinese** - Chinese
   - **Türkçe** - Turkish

2. When sending messages, the system will automatically translate and display the translation result

### Translation Display
- Original message and translated message will be displayed simultaneously
- Translated messages are identified with different colors
- Support real-time translation

## ⏰ Reminder Functionality

### Set Reminders
1. Click "Reminder" button
2. Enter reminder event name
3. Set reminder time (seconds)
4. Click "Set Reminder"

### Reminder Notifications
- Reminder notification will pop up when time is reached
- Reminder messages will be displayed in the chat area
- Support setting multiple reminders simultaneously

## 🎨 Interface Functions

### Modern Interface Features
- **Responsive Layout**: Window size can be adjusted
- **Multi-tabs**: Support multiple chat sessions
- **Beautiful Design**: Modern UI components
- **Real-time Status**: Connection status displayed in real-time

### Interface Operations
- **Resize Window**: Drag window edges
- **Switch Tabs**: Click tabs to switch chats
- **Close Tabs**: Click close button on tabs
- **Minimize/Maximize**: Use window control buttons

## 🔧 Advanced Functions

### Server Discovery
- System automatically discovers other servers on the network
- Support cross-server communication
- Server status updated in real-time

### Message History
- Chat records are automatically saved
- Support viewing historical messages
- Messages displayed in chronological order

### Online Status
- User online status displayed in real-time
- Support user search functionality
- Display user's server affiliation

## 🛠️ Troubleshooting

### Connection Issues
**Problem**: Cannot connect to server
**Solution**:
1. Check if server is started
2. Confirm network connection is normal
3. Check firewall settings
4. Try restarting the client

### Translation Issues
**Problem**: Translation functionality not working
**Solution**:
1. Check network connection
2. Confirm correct target language is selected
3. Check if Google Translate API is available

### Interface Issues
**Problem**: Interface display abnormal
**Solution**:
1. Restart the client
2. Check if PySide6 is properly installed
3. Update graphics card drivers