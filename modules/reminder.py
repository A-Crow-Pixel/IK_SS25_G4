import time
import heapq
import threading
from threading import Thread, Lock
from proto import Message_pb2
from modules.PackingandUnpacking import *

class ReminderManagerSimple:
    """
    Option 1: Simple polling reminder manager using list
    Suitable for small-scale applications, simple and intuitive implementation
    """
    
    def __init__(self, server_socket_ref):
        self.server_socket = server_socket_ref
        self.reminders = []  # List to store all reminders
        self.reminders_lock = Lock()  # Thread safety lock
        self.running = False
        self.worker_thread = None
        self.check_interval = 1  # Check every second
        
    def start(self):
        """Start reminder service"""
        if self.running:
            return
        self.running = True
        self.worker_thread = Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        print("[ReminderSimple] Reminder service started (polling mode)")
    
    def stop(self):
        """Stop reminder service"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join()
        print("[ReminderSimple] Reminder service stopped")
    
    def add_reminder(self, user_id, event, countdown_seconds):
        """Add a new reminder"""
        trigger_time = time.time() + countdown_seconds
        reminder = {
            'user_id': user_id,
            'event': event,
            'trigger_time': trigger_time,
            'countdown_seconds': countdown_seconds
        }
        
        with self.reminders_lock:
            self.reminders.append(reminder)
        
        print(f"[ReminderSimple] Added reminder: {user_id} - {event} (will remind in {countdown_seconds} seconds)")
    
    def _worker_loop(self):
        """Worker thread main loop - polling check all reminders"""
        while self.running:
            current_time = time.time()
            reminders_to_remove = []
            
            with self.reminders_lock:
                for i, reminder in enumerate(self.reminders):
                    if current_time >= reminder['trigger_time']:
                        # Time is up, send reminder
                        self._send_reminder(reminder)
                        reminders_to_remove.append(i)
                
                # Delete from back to front to avoid index confusion
                for i in reversed(reminders_to_remove):
                    del self.reminders[i]
            
            # Sleep for a while before checking again
            time.sleep(self.check_interval)
    
    def _send_reminder(self, reminder):
        """Send reminder message to user"""
        user_id = reminder['user_id']
        event = reminder['event']
        
        # Check if user is online
        with self.server_socket.client_info_lock:
            if user_id not in self.server_socket.client_info:
                print(f"[ReminderSimple] User {user_id} is offline, skipping reminder: {event}")
                return
            
            client_socket = self.server_socket.client_info[user_id]['socket']
        
        try:
            # Construct REMINDER message
            reminder_msg = Message_pb2.Reminder()
            reminder_msg.user.userId = user_id
            reminder_msg.user.serverId = self.server_socket.server_id
            reminder_msg.reminderContent = event
            
            payload = reminder_msg.SerializeToString()
            tosend = Packing('REMINDER', payload)
            client_socket.send(tosend)
            
            print(f"[ReminderSimple] Sent reminder to {user_id}: {event}")
            
        except Exception as e:
            print(f"[ReminderSimple] Failed to send reminder to {user_id}: {e}")
    
    def get_reminder_count(self):
        """Get current pending reminder count"""
        with self.reminders_lock:
            return len(self.reminders)


class ReminderManagerHeap:
    """
    Option 2: Priority queue (min heap) reminder manager for precise scheduling
    Suitable for large-scale applications with excellent performance
    """
    
    def __init__(self, server_socket_ref):
        self.server_socket = server_socket_ref
        self.reminders = []  # Min heap, stores (trigger_time, user_id, event)
        self.reminders_lock = Lock()  # Thread safety lock
        self.running = False
        self.worker_thread = None
        self.wake_event = threading.Event()  # For waking up worker thread
        
    def start(self):
        """Start reminder service"""
        if self.running:
            return
        self.running = True
        self.worker_thread = Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        print("[ReminderHeap] Reminder service started (priority queue mode)")
    
    def stop(self):
        """Stop reminder service"""
        self.running = False
        self.wake_event.set()  # Wake up worker thread to exit
        if self.worker_thread:
            self.worker_thread.join()
        print("[ReminderHeap] Reminder service stopped")
    
    def add_reminder(self, user_id, event, countdown_seconds):
        """Add a new reminder"""
        trigger_time = time.time() + countdown_seconds
        
        with self.reminders_lock:
            # Use heapq.heappush to add reminder to priority queue
            # Heap elements are (trigger_time, user_id, event)
            heapq.heappush(self.reminders, (trigger_time, user_id, event))
        
        # Wake up worker thread to recalculate sleep time
        self.wake_event.set()
        
        print(f"[ReminderHeap] Added reminder: {user_id} - {event} (will remind in {countdown_seconds} seconds)")
    
    def _worker_loop(self):
        """Worker thread main loop - precise scheduling"""
        while self.running:
            sleep_duration = None
            next_reminder = None
            
            with self.reminders_lock:
                if self.reminders:
                    # Get the earliest reminder (but don't remove it)
                    next_reminder = self.reminders[0]
                    trigger_time = next_reminder[0]
                    current_time = time.time()
                    
                    if current_time >= trigger_time:
                        # Time is up, process immediately
                        sleep_duration = 0
                    else:
                        # Calculate sleep time needed
                        sleep_duration = trigger_time - current_time
            
            if next_reminder is None:
                # No pending reminders, sleep for a longer time
                print("[ReminderHeap] No pending reminders, waiting for new tasks...")
                self.wake_event.wait(timeout=60)  # Wait up to 60 seconds
                self.wake_event.clear()
                continue
            
            if sleep_duration is not None and sleep_duration > 0:
                # Sleep precisely until reminder time
                print(f"[ReminderHeap] Waiting {sleep_duration:.1f} seconds before processing next reminder")
                if self.wake_event.wait(timeout=sleep_duration):
                    # Woken up early (possibly new reminder added), clear event and loop again
                    self.wake_event.clear()
                    continue
            
            # Time is up, process reminder
            with self.reminders_lock:
                if self.reminders and time.time() >= self.reminders[0][0]:
                    # Pop the earliest reminder from heap
                    trigger_time, user_id, event = heapq.heappop(self.reminders)
                    self._send_reminder(user_id, event)
    
    def _send_reminder(self, user_id, event):
        """Send reminder message to user (supports cross-server via homeserver forwarding)"""
        # Parse user_id, check if it's cross-server format: userId@serverId
        target_user_id = user_id
        target_server_id = None
        
        if '@' in user_id:
            target_user_id, target_server_id = user_id.split('@', 1)
        
        # First check if target user is on this server
        with self.server_socket.client_info_lock:
            if target_user_id in self.server_socket.client_info:
                # Local server user, send directly
                client_socket = self.server_socket.client_info[target_user_id]['socket']
                try:
                    reminder_msg = Message_pb2.Reminder()
                    reminder_msg.user.userId = target_user_id
                    reminder_msg.user.serverId = self.server_socket.server_id
                    reminder_msg.reminderContent = event
                    
                    payload = reminder_msg.SerializeToString()
                    tosend = Packing('REMINDER', payload)
                    client_socket.send(tosend)
                    
                    print(f"[ReminderHeap] Sent reminder to local user {target_user_id}: {event}")
                    return
                    
                except Exception as e:
                    print(f"[ReminderHeap] Failed to send reminder to local user {target_user_id}: {e}")
                    return
        
        # User not on this server, need to forward to target server
        if target_server_id:
            print(f"[ReminderHeap] User {target_user_id} is on server {target_server_id}, forwarding reminder")
            
            # Construct REMINDER message
            reminder_msg = Message_pb2.Reminder()
            reminder_msg.user.userId = target_user_id
            reminder_msg.user.serverId = target_server_id
            reminder_msg.reminderContent = event
            
            payload = reminder_msg.SerializeToString()
            tosend = Packing('REMINDER', payload)
            
            # Find target server and forward
            forwarded = False
            with self.server_socket.server_list_lock:
                for server_id, server_info in self.server_socket.server_list.items():
                    if server_id == target_server_id:
                        server_socket = server_info.get('socket')
                        if server_socket:
                            try:
                                server_socket.send(tosend)
                                print(f"[ReminderHeap] Forwarded reminder to server {target_server_id} for user {target_user_id}: {event}")
                                forwarded = True
                                break
                            except Exception as e:
                                print(f"[ReminderHeap] Failed to forward reminder to server {target_server_id}: {e}")
            
            if not forwarded:
                print(f"[ReminderHeap] Target server {target_server_id} not found or not connected, cannot forward reminder for user {target_user_id}: {event}")
        else:
            # User offline and no server specified
            print(f"[ReminderHeap] User {target_user_id} is offline, skipping reminder: {event}")
    
    def get_reminder_count(self):
        """Get current pending reminder count"""
        with self.reminders_lock:
            return len(self.reminders)


# For convenience, provide a factory function
def create_reminder_manager(server_socket_ref, use_heap=True):
    """
    Create reminder manager
    
    Args:
        server_socket_ref: Server socket reference
        use_heap: True to use priority queue (recommended), False to use simple polling
    
    Returns:
        ReminderManager instance
    """
    if use_heap:
        return ReminderManagerHeap(server_socket_ref)
    else:
        return ReminderManagerSimple(server_socket_ref) 