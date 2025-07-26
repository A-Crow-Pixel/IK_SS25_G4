from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QTreeWidget, QTreeWidgetItem, QTextBrowser,
                               QStackedWidget, QTableWidget, QTableWidgetItem,
                               QFrame, QSplitter)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont, QColor, QPalette

from rrd_widgets import (SimpleButton_1, SimpleButton_2, SimpleButton_3,
                         ExpandLineEdit, ComboBoxWidget, TipsWidget, TipsStatus)


class ModernReminderDialog(QWidget):
    """Modern Reminder Setting Dialog"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Set Reminder")
        self.resize(400, 250)
        self.setup_ui()

    def setup_ui(self):
        """Setup UI Layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title
        title_label = QLabel("Set Reminder")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title_label.setStyleSheet("color: #333; text-align: center;")
        layout.addWidget(title_label)

        # Event name
        event_layout = QHBoxLayout()
        event_label = QLabel("Event Name:")
        event_label.setFont(QFont("Microsoft YaHei", 10))
        event_layout.addWidget(event_label)

        self.Eventname = ExpandLineEdit()
        self.Eventname.setParams(editer_height=35)
        self.Eventname.setPlaceholderText("Enter reminder event name")
        self.Eventname.setStyleSheet("""
            ExpInput {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 5px;
                color: #333;
                padding: 5px;
            }
        """)
        self.Eventname.setFont(QFont("Microsoft YaHei", 10))
        event_layout.addWidget(self.Eventname)
        layout.addLayout(event_layout)

        # Time setting
        time_layout = QHBoxLayout()
        time_label = QLabel("Countdown (seconds):")
        time_label.setFont(QFont("Microsoft YaHei", 10))
        time_layout.addWidget(time_label)

        self.Time = ExpandLineEdit()
        self.Time.setParams(editer_height=35)
        self.Time.setPlaceholderText("Enter countdown seconds")
        self.Time.setStyleSheet("""
            ExpInput {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 5px;
                color: #333;
                padding: 5px;
            }
        """)
        self.Time.setFont(QFont("Microsoft YaHei", 10))
        time_layout.addWidget(self.Time)
        layout.addLayout(time_layout)

        # Set button
        self.setButton = SimpleButton_1()
        self.setButton.setParams(
            text="Set Reminder",
            border_radius=5,
            full_color=QColor(156, 39, 176),
            font_anim_start_color=QColor(156, 39, 176),
            font_anim_finish_color=QColor(255, 255, 255)
        )
        self.setButton.setFont(QFont("Microsoft YaHei", 10))
        self.setButton.setFixedHeight(35)
        layout.addWidget(self.setButton)