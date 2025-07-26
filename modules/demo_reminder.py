#!/usr/bin/env python3
"""
Demo script for reminder functionality
Shows how the reminder system works with UI components
"""

import sys
import time
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QTextEdit
from PySide6.QtCore import QTimer, Signal, QObject
from PySide6.QtUiTools import QUiLoader
from rrd_widgets import TipsWidget, TipsStatus

class ReminderDemo(QWidget):
    """
    Demo widget for testing reminder functionality.
    
    This class provides a simple interface to demonstrate how the reminder system works,
    including setting reminders and displaying notifications when they trigger.
    """
    
    def __init__(self):
        """Initialize the reminder demo widget with UI components and timer setup."""
        super().__init__()
        self.setWindowTitle("Reminder Demo")
        self.setGeometry(100, 100, 500, 400)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Reminder Function Demo")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Event input
        self.event_label = QLabel("Event Name:")
        layout.addWidget(self.event_label)
        
        self.event_input = QLineEdit()
        self.event_input.setPlaceholderText("Enter event, e.g., meeting")
        layout.addWidget(self.event_input)
        
        # Time input
        self.time_label = QLabel("Reminder Time (seconds):")
        layout.addWidget(self.time_label)
        
        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("Enter seconds, e.g., 5")
        layout.addWidget(self.time_input)
        
        # Set button
        self.set_button = QPushButton("Set Reminder")
        self.set_button.clicked.connect(self.set_reminder)
        layout.addWidget(self.set_button)
        
        # Status display
        self.status_label = QLabel("Status: Waiting for reminder")
        layout.addWidget(self.status_label)
        
        # Log display
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)
        
        self.setLayout(layout)
        
        # Timer for simulating reminder trigger
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self.trigger_reminder)
        
        self.current_event = ""
        
    def set_reminder(self):
        """Set a reminder based on user input for event name and time."""
        event = self.event_input.text().strip()
        time_str = self.time_input.text().strip()
        
        if not event or not time_str:
            self.log_text.append("❌ Please enter event name and time")
            return
        
        try:
            seconds = int(time_str)
            if seconds <= 0:
                self.log_text.append("❌ Time must be greater than 0 seconds")
                return
        except ValueError:
            self.log_text.append("❌ Time must be a number")
            return
        
        self.current_event = event
        self.reminder_timer.start(seconds * 1000)  # convert to ms
        
        self.status_label.setText(f"Status: Reminder set for '{event}', triggers in {seconds}s")
        self.log_text.append(f"✅ Reminder set successfully: {event} ({seconds}s)")
        
        # clear inputs
        self.event_input.clear()
        self.time_input.clear()
        
    def trigger_reminder(self):
        """Trigger the reminder notification when the timer expires."""
        self.reminder_timer.stop()
        
        # show reminder popup
        tip = TipsWidget(self)
        tip.setText(f"Reminder|Time for your event: '{self.current_event}'!")
        tip.status = TipsStatus.Succeed
        tip.move(50, 50)
        tip.resize(420, 35)
        tip.show()
        
        self.status_label.setText("Status: Reminder triggered")
        self.log_text.append(f"🔔 Reminder triggered: {self.current_event}")
        
        # reset status after 3s
        QTimer.singleShot(3000, self.reset_status)
        
    def reset_status(self):
        """Reset the status label to waiting state."""
        self.status_label.setText("Status: Waiting for reminder")

def test_reminder_ui():
    """Run the reminder demo application."""
    print("Starting reminder UI demo...")
    
    app = QApplication(sys.argv)
    
    # create demo window
    demo = ReminderDemo()
    demo.show()
    
    print("Demo window is open, you can:")
    print("1. Enter an event name (e.g., meeting)")
    print("2. Enter reminder time in seconds (e.g., 5)")
    print("3. Click 'Set Reminder' button")
    print("4. Wait for the popup")
    
    return app.exec()

if __name__ == '__main__':
    try:
        test_reminder_ui()
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please make sure you have the required dependencies installed")
        
        # if rrd_widgets is not available, create a simplified version
        print("Creating simplified demo version...")
        
        app = QApplication(sys.argv)
        
        widget = QWidget()
        widget.setWindowTitle("Reminder Demo (Simplified)")
        widget.setGeometry(100, 100, 400, 200)
        
        layout = QVBoxLayout()
        
        label = QLabel("Reminder functionality is integrated into the system")
        label.setStyleSheet("font-size: 16px; margin: 20px;")
        layout.addWidget(label)
        
        info = QLabel("Features include:\n• Set reminder events\n• Countdown function\n• Popup notifications\n• Min-Heap optimization")
        layout.addWidget(info)
        
        widget.setLayout(layout)
        widget.show()
        
        app.exec() 