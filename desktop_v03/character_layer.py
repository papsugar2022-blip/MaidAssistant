"""Independent alpha-shaped desktop surface; no application services here."""
from pathlib import Path

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QImage, QPainter, QPixmap, QRegion
from PySide6.QtWidgets import QApplication, QWidget


class CharacterLayer(QWidget):
    characterClicked = Signal()
    viewChanged = Signal(str)
    closeRequested = Signal()

    def __init__(self, asset: Path):
        super().__init__()
        self.setWindowTitle('MaidAssistant · 桌面角色')
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.source = QImage(str(asset))
        if self.source.isNull():
            raise ValueError(f'角色素材无法加载：{asset}')
        self.view_mode = 'half'
        self.line = '欢迎回来，主人。今天需要我做什么？'
        self._press = None
        self._dragging = False
        self.set_view_mode('half')
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 32, screen.bottom() - self.height() - 24)

    def set_view_mode(self, mode):
        if mode not in ('half', 'full'):
            return
        self.view_mode = mode
        screen = self.screen().availableGeometry()
        height = min(520, max(180, screen.height() - 64))
        width = min(350 if mode == 'half' else 300, screen.width())
        self.setFixedSize(width, height)
        canvas = QImage(self.size(), QImage.Format_ARGB32)
        canvas.fill(Qt.transparent)
        if mode == 'half':
            scaled = self.source.scaledToHeight(int(height * 1.92), Qt.SmoothTransformation)
        else:
            scaled = self.source.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter = QPainter(canvas)
        painter.drawImage((width - scaled.width()) // 2, 0, scaled)
        painter.end()
        self.image = canvas
        self.pixmap = QPixmap.fromImage(canvas)
        # Native window region, not merely event.ignore(): holes belong to the
        # underlying Windows window, including icons in another process.
        region = QRegion()
        raw = canvas.constBits()
        stride = canvas.bytesPerLine()
        for y in range(height):
            start = None
            for x in range(width + 1):
                opaque = x < width and raw[y * stride + x * 4 + 3] > 8
                if opaque and start is None:
                    start = x
                elif not opaque and start is not None:
                    region |= QRegion(QRect(start, y, x - start, 1))
                    start = None
        if region.isEmpty():
            raise ValueError('角色素材没有可显示像素')
        self.setMask(region)
        self.update()
        if self.isVisible():
            self.keep_on_screen()
        self.viewChanged.emit(mode)

    def keep_on_screen(self):
        available = self.screen().availableGeometry()
        self.move(min(max(self.x(), available.left()), available.right() - self.width() + 1),
                  min(max(self.y(), available.top()), available.bottom() - self.height() + 1))

    def set_line(self, line):
        self.line = line

    def paintEvent(self, event):
        p = QPainter(self)
        p.drawPixmap(0, 0, self.pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press = event.globalPosition().toPoint()
            self._origin = self.pos()
            self._dragging = False
            event.accept()

    def mouseMoveEvent(self, event):
        if self._press is not None and event.buttons() & Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._press
            if delta.manhattanLength() >= QApplication.startDragDistance():
                self._dragging = True
            if self._dragging:
                self.move(self._origin + delta)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._press is not None:
            clicked = not self._dragging and (event.globalPosition().toPoint() - self._press).manhattanLength() < QApplication.startDragDistance()
            self._press = None
            self.keep_on_screen()
            if clicked:
                self.characterClicked.emit()

    def contextMenuEvent(self, event):
        self.characterClicked.emit()

    def closeEvent(self, event):
        self.closeRequested.emit()
        event.ignore()

