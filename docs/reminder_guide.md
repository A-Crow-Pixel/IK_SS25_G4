# Reminder Functionality Guide

## 📋 Overview

The Internetkommunikation_Project_Gruppe4 chat application provides powerful reminder functionality, supporting scheduled reminders, event reminders, and various other scenarios. The system implements two different reminder management solutions to adapt to different scale application requirements.

## 🎯 Feature Characteristics

### Core Functions
- **Scheduled Reminders**: Support precise timing down to seconds
- **Event Reminders**: Custom reminder event content
- **Multi-user Support**: Each user can set multiple independent reminders
- **Real-time Notifications**: Send notifications immediately when reminders are due
- **Persistent Storage**: Reminder information persists after server restart

### Technical Features
- **High Performance**: Support for large numbers of concurrent reminders
- **Low Latency**: Precise time scheduling
- **Reliability**: Automatic error recovery and retry mechanisms
- **Scalability**: Support for cluster deployment

## 🏗️ Architecture Design

### Solution 1: Simple Polling (ReminderManagerSimple)

**Applicable Scenarios**: Small-scale applications with few reminders (<100)

**Working Principle**:
- Use a list to store all pending reminders
- Background thread checks all reminders every second
- Send reminder and remove from list when time is reached

**Advantages**:
- Simple implementation, clear logic
- Code is easy to understand and maintain
- Suitable for scenarios with few reminders

**Disadvantages**:
- CPU consumption increases linearly with reminder count
- Need to traverse all reminders every second, low efficiency

### Solution 2: Priority Queue (ReminderManagerHeap) ⭐Recommended

**Applicable Scenarios**: Large-scale applications with many reminders (>100)

**Working Principle**:
- Use min-heap (priority queue) to store reminders, sorted by trigger time
- Background thread sleeps precisely until the next reminder trigger time
- Support dynamic reminder addition and automatic sleep time adjustment

**Advantages**:
- Excellent performance, extremely low CPU consumption
- Support efficient processing of large numbers of reminders
- Precise scheduling, no unnecessary polling
- High memory usage efficiency

**Disadvantages**:
- Slightly complex implementation, requires understanding of heap data structure
- Uses thread synchronization mechanisms (Event)

## 🚀 Usage Methods

### 1. Server-side Integration

#### Initialize Reminder Manager
```python
# In server_network.py
from modules.reminder import create_reminder_manager

class ServerSocket:
    def __init__(self, ...):
        # ... Other initialization code ...
        
        # Initialize reminder manager (recommended to use priority queue solution)
        self.reminder_manager = create_reminder_manager(self, use_heap=True)
    
    def start_all(self):
        # ... Start other services ...
        
        # Start reminder service
        self.reminder_manager.start()
```

#### Handle Client Reminder Requests
```python
# Add in handle_tcp_client method
elif purpose == 'SET_REMINDER':
    try:
        set_reminder = Message_pb2.SetReminder()
        set_reminder.ParseFromString(payload)
        
        user_id = set_reminder.user.userId
        event = set_reminder.event
        countdown_seconds = set_reminder.countdownSeconds
        
        # Add reminder
        self.reminder_manager.add_reminder(user_id, event, countdown_seconds)
        
        global_ms.log_signal.emit(f"[Server] Set reminder: {user_id} - {event} ({countdown_seconds} seconds)")
        
    except Exception as e:
        global_ms.log_signal.emit(f"[Server] SET_REMINDER error: {e}")
```

### 2. Client Usage

#### Send Reminder Request
```python
def send_set_reminder(self, event_name, countdown_seconds):
    """Send set reminder request"""
    set_reminder = Message_pb2.SetReminder()
    set_reminder.user.userId = self.user_id
    set_reminder.user.serverId = self.server_id
    set_reminder.event = event_name
    set_reminder.countdownSeconds = countdown_seconds
    
    packet = Packing('SET_REMINDER', set_reminder.SerializeToString())
    self.tcp_socket.send(packet)
```

#### Handle Reminder Notification
```python
elif purpose == 'REMINDER':
    try:
        reminder = Message_pb2.Reminder()
        reminder.ParseFromString(payload)
        
        # Display reminder notification
        self.show_reminder_popup(reminder.reminderContent)
        
    except Exception as e:
        print(f"Error processing reminder message: {e}")
```

### 3. Protocol Definition

#### Protocol Buffers Definition
```protobuf
// Set reminder request
message SetReminder {
    User user = 1;
    string event = 2;           // Reminder content, e.g., "Time to go to bed"
    uint32 countdownSeconds = 3; // Countdown seconds, e.g., 60 means remind in 1 minute
}

// Reminder message
message Reminder {
    User user = 1;
    string reminderContent = 2; // Reminder content
}
```

## 📊 Performance Comparison

| Feature | Simple Polling | Priority Queue |
|---------|----------------|----------------|
| **CPU Usage** | High (O(n)) | Low (O(log n)) |
| **Memory Usage** | Medium | Low |
| **Response Latency** | 1 second | <1 second |
| **Scalability** | Poor | Excellent |
| **Implementation Complexity** | Simple | Medium |
| **Recommended Scenarios** | <100 reminders | >100 reminders |

## 🔧 Configuration Options

### Reminder Manager Configuration
```python
# Configuration options when creating reminder manager
reminder_manager = create_reminder_manager(
    server_socket_ref=self,
    use_heap=True,              # Use priority queue solution
    check_interval=1,           # Check interval (seconds)
    max_reminders=10000,        # Maximum number of reminders
    enable_logging=True         # Enable logging
)
```

### Performance Tuning
```python
# Recommended configurations for different scenarios

# Small-scale application (<50 users)
reminder_manager = create_reminder_manager(
    server_socket_ref=self,
    use_heap=False,             # Use simple polling
    check_interval=1
)

# Medium-scale application (50-500 users)
reminder_manager = create_reminder_manager(
    server_socket_ref=self,
    use_heap=True,              # Use priority queue
    check_interval=1,
    max_reminders=5000
)

# Large-scale application (>500 users)
reminder_manager = create_reminder_manager(
    server_socket_ref=self,
    use_heap=True,              # Use priority queue
    check_interval=0.5,         # More frequent checks
    max_reminders=50000,
    enable_logging=False        # Disable logging for better performance
)
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Reminders Not Firing
**Possible Causes**:
- Reminder manager not started
- Time calculation error
- Network connection issues

**Solutions**:
```python
# Check reminder manager status
if self.reminder_manager.is_running():
    print("Reminder manager is running")
else:
    print("Reminder manager not started")
    self.reminder_manager.start()
```

#### 2. Performance Issues
**Possible Causes**:
- Too many reminders
- Using an unsuitable solution

**Solutions**:
```python
# Switch to priority queue solution
self.reminder_manager = create_reminder_manager(
    server_socket_ref=self,
    use_heap=True  # Use priority queue
)
```

#### 3. Memory Leaks
**Possible Causes**:
- Reminders not cleaned up correctly
- Threads not exited correctly

**Solutions**:
```python
# Correctly stop reminder manager
def cleanup(self):
    if self.reminder_manager:
        self.reminder_manager.stop()
        self.reminder_manager = None
```

### Debugging Tips

#### Enable Detailed Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debugging in reminder manager
reminder_manager = create_reminder_manager(
    server_socket_ref=self,
    use_heap=True,
    enable_logging=True
)
```

#### Monitor Reminder Status
```python
# Get current reminder count
current_count = len(self.reminder_manager.get_all_reminders())
print(f"Current active reminder count: {current_count}")

# Get next reminder time
next_reminder = self.reminder_manager.get_next_reminder()
if next_reminder:
    print(f"Next reminder: {next_reminder['event']} at {next_reminder['trigger_time']}")
```

## 📈 Best Practices

### 1. Choose the Appropriate Solution
- **Small-scale applications**: Use simple polling solution
- **Large-scale applications**: Use priority queue solution
- **Mixed scenarios**: Dynamically select based on actual reminder count

### 2. Set Reasonable Reminder Times
- Avoid setting too short reminder intervals (<1 second)
- Consider network latency and system load
- Set redundancy mechanisms for important reminders

### 3. Error Handling
- Implement reminder failure retry mechanisms
- Log reminder send failures
- Provide user-friendly error messages

### 4. Performance Optimization
- Periodically clean up expired reminders
- Limit the number of reminders per user
- Optimize network communication using connection pools

## 🔗 Related Resources

- [Development Guide](development_guide.md) - Development related documents
- [API Documentation](api_documentation.md) - Interface documentation
- [User Guide](user_guide.md) - User usage guide 