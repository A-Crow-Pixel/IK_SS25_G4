from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QIcon
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QBoxLayout

from ..base import WidgetAnimationGroupBase
from ..widget.button.base_button import BaseButton, BaseClickedHoveringButton
from ..layout.v_layout import VBoxLayoutManager


class FlexibleSidebarButton(BaseClickedHoveringButton):
    def __init__(self, parent, text=None, icon=None):
        super().__init__(parent=parent)
        self.setFixedHeight(30)
        self.setText(text)
        self.setIcon(icon)


class FlexibleSidebarBase(WidgetAnimationGroupBase):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.min_v = 0
        self.max_v = 0
        self.is_focus = False

        self.border_radius = 0
        self.background_color = QColor()
        self.both_sides_stretching = True

        self.componentInit()
        self.setMaximumWidth(300)

    def setParams(self,
                  min_of_range: int,
                  max_of_range: int,
                  background_color: QColor,
                  border_radius: int = 0,
                  both_sides_stretching: bool = True
                  ):
        self.min_v = min_of_range
        self.max_v = max_of_range
        self.border_radius = border_radius
        self.background_color = background_color
        self.both_sides_stretching = both_sides_stretching
        # self.animConfig()

    def componentInit(self):
        self.vbox = QVBoxLayout(self)
        self.vbox.setSpacing(8)
        self.vbox.setContentsMargins(5, 15, 5, 10)
        self.vbox.setDirection(QBoxLayout.BottomToTop)
        self.vbox.addStretch()
        self.setLayout(self.vbox)

    def animConfig(self):
        self.addAnimParams(min_v=self.min_v, max_v=self.max_v, time=100)
        if self.both_sides_stretching:
            start_show_x = self.x()
            start_hide_x = self.x() + (self.max_v - self.min_v) // 2
            self.addAnimParams(min_v=start_hide_x, max_v=start_show_x, time=100)

    def paintEvent(self, event) -> None:
        path = QPainterPath()
        path.addRoundedRect(self.rect(), self.border_radius, self.border_radius)

        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setClipPath(path)

        self.drawBackground(painter)

    def drawBackground(self, painter: QPainter):
        painter.save()
        painter.setBrush(self.background_color)
        painter.drawRect(self.rect())
        painter.restore()

    def onAnimParamChangeSignal(self, v: list) -> None:
        width = v[0]
        self.setGeometry(self.x(), self.y(), width, self.height())
        if self.both_sides_stretching:
            x = v[1]
            self.setGeometry(x, self.y(), width, self.height())

    def addWidget(self, widget: QPushButton, pos: int):
        """
        :param widget:
        :param pos:     1 at top : 0 at bottom
        :return:
        """
        self.vbox.insertWidget(pos, widget)
        widget.clicked.connect(self.onItemClicked)

    def onItemClicked(self):
        for item in self.findChildren(FlexibleSidebarButton):
            if isinstance(item, FlexibleSidebarButton):
                item.is_clicked = False
                item.update()

        trigger = self.sender()
        trigger.is_clicked = True

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.animConfig()


class FlexibleSidebar_Hover(FlexibleSidebarBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_focus = True

    def enterEvent(self, event):
        super().enterEvent(event)
        if not self.is_focus and not self.is_running():
            self.animForwardRun()
            self.is_focus = True

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if self.is_focus and not self.is_running():
            self.is_focus = False
            self.animBackwardRun()


class FlexibleSidebar_Click(FlexibleSidebarBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_focus = True
        self.close_icon = QIcon()

    def setButtonIcon(self, close_icon: QIcon = QIcon(), open_icon: QIcon = QIcon()):
        self.open_icon = open_icon
        self.close_icon = close_icon

        self.btn.setIcon(self.open_icon)

    def componentInit(self):
        super().componentInit()

        icon = QIcon()
        icon.addFile(":/icon_svg/icon_svg/more-2.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.btn = BaseButton(parent=self)
        self.btn.setFixedHeight(30)
        self.btn.setIcon(icon)
        self.btn.setText("More")
        self.btn.setParams(font_color=QColor(255, 255, 255), background_color=QColor(0, 0, 0, 0))
        self.btn.clicked.connect(self.onAnimRun)
        self.vbox.addWidget(self.btn)

    def addWidget(self, widget: QPushButton, pos: int):
        super().addWidget(widget, pos)
        self.btn.setFont(widget.font())

    def onAnimRun(self):
        if not self.is_running():
            if not self.is_focus:
                if self.close_icon:
                    self.btn.setIcon(self.close_icon)
                self.animForwardRun()
                self.is_focus = True
            else:
                if self.close_icon:
                    self.btn.setIcon(self.open_icon)
                self.is_focus = False
                self.animBackwardRun()
