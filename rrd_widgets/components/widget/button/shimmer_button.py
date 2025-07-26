from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QFrame, QGraphicsBlurEffect
from PySide6.QtGui import QColor, QPainter, QPainterPath, QLinearGradient, QImage

from rrd_widgets.common.get_style_property import get_property, transfer_type
from rrd_widgets.common.set_blur_to_image import set_blur_to_image


class ShimmerButton(QFrame):
    def __init__(self, parent=None):
        super(ShimmerButton, self).__init__(parent)
        self.is_hover = False
        self.index = 0

    def setParams(self,
                  shimmer_color_1: QColor = None,
                  shimmer_color_2: QColor = None,
                  shimmer_blur_radius: int = None,
                  timer_interval: int = 5
                  ):
        """
        :param shimmer_color_1: Gradient color 1
        :param shimmer_color_2: Gradient color 2
        :param shimmer_blur_radius: Shimmer blur radius
        :param timer_interval: Interval between shimmer animation frames, smaller value means faster animation
        """
        self.blur_radius = shimmer_blur_radius
        self.shimmer_color_1 = shimmer_color_1
        self.shimmer_color_2 = shimmer_color_2
        self.timer_interval = timer_interval

    def setAnimParams(self):
        """ Configure animation parameters """
        self.timer = QTimer()
        self.timer.setInterval(self.timer_interval)
        self.timer.timeout.connect(self.offsetUpdate)

        self.rect_1_offset = self.width()  # Rectangle 1 position
        self.rect_2_offset = self.width()  # Rectangle 2 position
        self.rect_1_start = -self.width()  # Rectangle 1 initial position
        self.rect_2_start = -self.width() * 2  # Rectangle 2 initial position
        self.flag = 0  # Rectangle 1 initial position flag, 0 -> at initial, 1 -> at default initial

    def compSizeParams(self):
        """ Calculate position parameters """
        blur_radius_offset = 10
        self.foreground_width = self.width() - self.blur_radius - blur_radius_offset
        self.foreground_height = self.height() - self.blur_radius - blur_radius_offset

        self.background_width = self.width() - self.blur_radius - blur_radius_offset
        self.background_height = self.height() - self.blur_radius - blur_radius_offset

    def getStyleSheetParams(self):
        """ Extract style """
        ShimmerButtonBox_property: dict = get_property(self)["ShimmerButton"]
        self.font_color = transfer_type(ShimmerButtonBox_property["color"], "color")
        self.border_radius = transfer_type(ShimmerButtonBox_property["border-radius"], "pixel")

    def setGeometry(self, g):
        super(ShimmerButton, self).setGeometry(g)
        self.compSizeParams()

    def setStyleSheet(self, styleSheet: str) -> None:
        super(ShimmerButton, self).setStyleSheet(styleSheet)
        self.getStyleSheetParams()

    def paintEvent(self, event):
        super(ShimmerButton, self).paintEvent(event)

        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), self.border_radius, self.border_radius)

        painter_widget = QPainter(self)
        painter_widget.setPen(Qt.NoPen)
        painter_widget.setClipPath(path)
        painter_widget.setRenderHint(QPainter.Antialiasing)

        # Draw background
        if self.is_hover:
            background = self.paintBackground()
            painter_widget.drawImage(self.background_x, self.background_y, background)

        foreground = self.paintForeground()
        painter_widget.drawImage(self.foreground_x, self.foreground_y, foreground)

        # Draw text
        self.paintText()

    def paintText(self):
        """ Draw text """
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), self.border_radius, self.border_radius)

        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setClipPath(path)
        painter.setFont(self.font())
        painter.setPen(QColor(self.font_color))
        painter.setRenderHint(QPainter.Antialiasing)

        painter.drawText(self.rect(), Qt.AlignCenter, self.text)

    def paintBackground(self):
        """Generate background image"""
        self.background_x = 0
        self.background_y = 0

        image_1_x = (self.width() - self.background_width) // 2
        image_1_y = (self.height() - self.background_height) // 2

        path_1 = QPainterPath()
        path_1.addRoundedRect(image_1_x, image_1_y, self.background_width, self.background_height, self.border_radius,
                              self.border_radius)

        image = QImage(self.width(), self.height(), QImage.Format_ARGB32)
        image.fill(Qt.transparent)

        painter = QPainter(image)
        painter.setPen(Qt.NoPen)
        painter.setClipPath(path_1)
        painter.setRenderHint(QPainter.Antialiasing)

        gradient_1 = self.createGradient(self.rect_1_start + self.rect_1_offset)
        painter.setBrush(gradient_1)
        painter.drawRoundedRect(self.rect_1_start + self.rect_1_offset, 0, self.width() + 1, self.height(),self.border_radius*2,self.border_radius*2)

        gradient_2 = self.createGradient(self.rect_2_start + self.rect_2_offset)
        painter.setBrush(gradient_2)
        painter.drawRoundedRect(self.rect_2_start + self.rect_2_offset, 0, self.width() + 1, self.height(),self.border_radius*2,self.border_radius*2)

        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(self.blur_radius)
        image_blur = set_blur_to_image(image, blur)

        painter.end()

        return image_blur

    def paintForeground(self):
        """Generate foreground image"""
        self.foreground_x = (self.width() - self.foreground_width) // 2
        self.foreground_y = (self.height() - self.foreground_height) // 2

        path = QPainterPath()
        path.addRoundedRect(0, 0, self.foreground_width, self.foreground_height, self.border_radius, self.border_radius)

        image = QImage(self.foreground_width, self.foreground_height, QImage.Format_ARGB32)
        image.fill(Qt.transparent)

        painter = QPainter(image)
        painter.setPen(Qt.NoPen)
        painter.setClipPath(path)
        painter.setRenderHint(QPainter.Antialiasing)

        gradient_1 = self.createGradient(self.rect_1_start + self.rect_1_offset)
        painter.setBrush(gradient_1)
        painter.drawRect(self.rect_1_start + self.rect_1_offset, 0, self.width() + 1, self.height())

        gradient_2 = self.createGradient(self.rect_2_start + self.rect_2_offset)
        painter.setBrush(gradient_2)
        painter.drawRect(self.rect_2_start + self.rect_2_offset, 0, self.width() + 1, self.height())

        painter.end()
        return image

    def createGradient(self, x):
        '''
        Set gradient color
        :param x: Rectangle x coordinate
        :return:
        '''
        gradient = QLinearGradient(x, 0, x + self.width(), 0)
        gradient.setColorAt(0, QColor(self.shimmer_color_1))
        gradient.setColorAt(0.5, QColor(self.shimmer_color_2))
        gradient.setColorAt(1, QColor(self.shimmer_color_1))

        return gradient

    def enterEvent(self, event):
        self.timer.start()
        self.is_hover = True

    def leaveEvent(self, event):
        self.timer.stop()
        self.is_hover = False
        self.update()

    def showEvent(self, event):
        super(ShimmerButton, self).showEvent(event)
        self.setAnimParams()

    def offsetUpdate(self):
        '''
        Determine if rectangle has left the button and trigger update event
        :return:
        '''
        if self.rect_1_offset >= self.width() * 2:
            self.rect_1_offset = 0
        if self.rect_2_offset >= self.width() * 3:
            self.rect_2_offset = 0
            self.rect_2_start = -self.width()
            self.flag = 1
        if self.rect_2_offset >= self.width() * 2 and self.flag == 1:
            self.rect_2_offset = 0

        self.rect_1_offset += 1
        self.rect_2_offset += 1

        self.update()

    def setText(self, text):
        self.text = text

    def mousePressEvent(self, event):
        """Used to switch gradient colors, this method can be deleted"""
        self.color = [["#784ea9", "#6f469f"], ["#fbe74a", "#92d692"], ["#5bc9b9", "#92d692"], ["#4FFBDF", "#845EC2"],
                      ["#95d9ea", "#e5aae9"], ["#004d65", "#008d89"], ["#bb00ff", "#00b3ff"]]
        super(ShimmerButton, self).mousePressEvent(event)
        self.shimmer_color_1 = self.color[self.index][0]
        self.shimmer_color_2 = self.color[self.index][1]
        self.index += 1
        if self.index % len(self.color) == 0:
            self.index = 0
        self.update()



