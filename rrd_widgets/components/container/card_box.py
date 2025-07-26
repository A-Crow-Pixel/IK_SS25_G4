from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup, QRect, QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget, QScrollArea, QWidgetItem, QBoxLayout


class CardBoxBase(QWidget):
    def __init__(self, parent=None,orientation:Qt.Orientation=Qt.Horizontal):
        super().__init__(parent=parent)
        self.orientation = orientation
        self.__uiInit()

    def __uiInit(self):
        self.resize(550, 300)

        # Scroll area
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Function area
        self.functionArea = QWidget()
        self.functionArea.setStyleSheet("background-color: transparent;")

        # Overall layout
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        """
        Add button to toolbar
        :param button: Button
        :param pos: Position
        """
        # Need to bind this method with a button


class CardBoxDeletable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.trigger = None
        self.del_card:list = []
        self.is_anim_group_connected = False
        self.animationGroup = QParallelAnimationGroup()
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.__uiInit()

    def __uiInit(self):
        self.resize(550, 300)

        # Scroll area
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Function area
        self.functionArea = QWidget()
        self.functionArea.setStyleSheet("background-color: transparent;")

        # Overall layout
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.addWidget(self.functionArea)
        self.mainLayout.addWidget(self.scrollArea)

    def getCardWidget(self) -> (QWidget, QPushButton):
        """
        Inherited window, need to override this function
        QWidget:        Card component
        QPushButton:    Button to delete card
        :return:
        """
        pass

    def addWidget(self, card_widget=None, *args):
        """
        Need to bind this method with a button
        :param card_widget:
        :param button_del:
        :return:
        """
        button_del = QPushButton("×")
        button_del.setFixedSize(20, 20)
        button_del.setStyleSheet("""
            QPushButton {
                background-color: #ff4757;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff3742;
            }
        """)

        button_del.clicked.connect(self.onDelCard)
        self.scrollArea.widget().layout().addWidget(card_widget)
        QTimer.singleShot(0, lambda: self.scrollArea.widget().adjustSize())  # Adjust scroll area size
        QTimer.singleShot(0, lambda: self.scrollArea.horizontalScrollBar().setValue(
            self.scrollArea.horizontalScrollBar().maximum()))  # Move scroll bar

    def onDelCard(self):
        """
        Provide external button binding, cannot be set as private method
        :return:
        """
        self.animationGroup = QParallelAnimationGroup()  # Initialize

        # Card move down
        for i in range(0, self.scrollArea.widget().layout().count()):
            item = self.scrollArea.widget().layout().itemAt(i)
            if isinstance(item, QWidgetItem):
                widget = item.widget()
                if isinstance(widget, QWidget):
                    animation = QPropertyAnimation(widget, b"geometry")
                    animation.setDuration(300)
                    animation.setStartValue(widget.geometry())
                    animation.setEndValue(QRect(widget.x(), widget.y() + 50, widget.width(), widget.height()))
                    self.animationGroup.addAnimation(animation)

        # Card move left
        start_index = self.scrollArea.widget().layout().indexOf(self.trigger) + 1
        end_index = int(self.width() / self.trigger.width()) + 2

        for i in range(start_index, end_index):
            item = self.scrollArea.widget().layout().itemAt(i)
            if isinstance(item, QWidgetItem):
                widget = item.widget()
                if isinstance(widget, QWidget):
                    animation = QPropertyAnimation(widget, b"geometry")
                    animation.setDuration(300)
                    animation.setStartValue(widget.geometry())
                    animation.setEndValue(QRect(widget.x() - self.trigger.width(), widget.y(), widget.width(), widget.height()))
                    self.animationGroup.addAnimation(animation)

        self.animationGroup.finished.connect(self.__onAnimFinished)
        self.animationGroup.start()

    def clearAllCard(self):
        self.animationGroup = QParallelAnimationGroup()  # Initialize
        for i in range(0, self.scrollArea.widget().layout().count()):
            item = self.scrollArea.widget().layout().itemAt(i)
            if isinstance(item, QWidgetItem):
                widget = item.widget()
                if isinstance(widget, QWidget):
                    animation = QPropertyAnimation(widget, b"geometry")
                    animation.setDuration(300)
                    animation.setStartValue(widget.geometry())
                    animation.setEndValue(QRect(widget.x(), widget.y() + 50, widget.width(), widget.height()))
                    self.animationGroup.addAnimation(animation)

        self.animationGroup.finished.connect(self.__onClearAllFinish)
        self.animationGroup.start()

    def __onAnimFinished(self):
        self.trigger.deleteLater()
        QTimer.singleShot(0, lambda: self.scrollArea.widget().adjustSize())

    def __onClearAllFinish(self):
        for i in range(0,self.scrollArea.widget().layout().count()):
            item = self.scrollArea.widget().layout().itemAt(i)
            if isinstance(item, QWidgetItem):
                widget = item.widget()
                if isinstance(widget, QWidget):
                    widget.deleteLater()
        QTimer.singleShot(0, lambda: self.scrollArea.widget().adjustSize())

    def addWidget2ToolBox(self, button: QPushButton, pos: int = 1):
        """
        Add button to toolbar
        :param button: Button
        :param pos: Position
        :return:
        """
        self.functionArea.layout().insertWidget(pos, button)

