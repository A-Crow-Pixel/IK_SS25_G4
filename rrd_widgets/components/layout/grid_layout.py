"""
Qt-RoastedDuck-Widgets
======================
Qt widgets-based implementation of the Material Design specification.

Repository at https://github.com/Rev-RoastedDuck/Qt-RoastedDuck-Widgets.

Demo are available at https://github.com/Rev-RoastedDuck/Qt-RoastedDuck-Widgets/tree/main/Demo.

Examples are available at https://github.com/Rev-RoastedDuck/Qt-RoastedDuck-Widgets/tree/main/examples.

Information:
    WeChat: Roast_71.
    csdnBlog: https://blog.csdn.net/m0_72760466?type=blog.

:copyright: (c) 2023 by Rev-RoastedDuck.
:license: GPLv3, see LICENSE for more details.
"""
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QRect, QSize, QPoint

class RGridLayout(QWidget):
    def __init__(self,parent,size:QSize):
        super().__init__(parent=parent)
        self.sizeBox = size
        self._uiConfig()
        self._ui()

    def _ui(self):
        self.setObjectName("RButtonBox")
        self.frameIn = QFrame(self)
        self.frameIn.setObjectName("frameIn")
        self.frameIn.setStyleSheet("#frameIn{"
                                    "	background-color: rgba(0,255,0,0);"
                                    "}"
                                )

    def _uiConfig(self):
        # Number of buttons in one row/column
        self.countButtonRow = 3
        self.countButtonCol = 3

        # Grid size
        self.grid_width = None
        self.grid_height = None

        # Button spacing
        self.spacing = None

        # Top/bottom and left/right margins
        self.paddingV = None
        self.paddingH = None

    def _getButtonRect(self, row, col):
        """
        Grid layout
        :param row:
        :param col:
        :return: Returns the Rect of each button
        """
        return QRect(self.grid_width * col + (col + 1) * self.spacing, self.grid_height * row + (row + 1) * self.spacing, self.grid_width, self.grid_height)

    def _getInteriorFrameSize(self):
        """Calculate internal frame size"""
        total_width = self.grid_width * self.countButtonRow + self.spacing * (self.countButtonRow - 1)
        total_height = self.grid_height * self.countButtonCol + self.spacing * (self.countButtonCol - 1)

        total_width += 2 * self.spacing
        total_height += 2 * self.spacing
        return QSize(total_width, total_height)

    def _getInteriorFrameRect(self):
        """Set internal frame position and size"""
        self.paddingH = (self.sizeBox.height() - self._getInteriorFrameSize().height()) // 2
        self.paddingV = (self.sizeBox.width() - self._getInteriorFrameSize().width()) // 2

        return QRect(QPoint(self.paddingH, self.paddingV), self._getInteriorFrameSize())

    def addWidget(self, w, row, column):
        """
        Used to add components
        :param w: Component
        :param row: Row
        :param column: Column
        """
        w.setParent(self.frameIn)
        w.setGeometry(self._getButtonRect(row, column))

        self.frameIn.setGeometry(self._getInteriorFrameRect())
        self.setFixedSize(self.sizeBox)
