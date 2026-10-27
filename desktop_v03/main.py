"""Desktop shell for the preserved V0.2 services and panels."""
import importlib.util
import sys
from pathlib import Path

from PySide6.QtCore import QEvent, QPoint, Qt, QTimer
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QMenu, QPushButton,
    QSystemTrayIcon, QVBoxLayout, QWidget,
)

from character_layer import CharacterLayer

ROOT = Path(__file__).resolve().parent.parent
LEGACY_ROOT = ROOT / 'MaidAssistant_V02_preview' / 'MaidAssistant_V02'


def load_backend(legacy_root=LEGACY_ROOT):
    spec = importlib.util.spec_from_file_location('maid_v02', legacy_root / 'main.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FunctionBubble(QWidget):
    def __init__(self, shell):
        super().__init__()
        self.shell = shell
        self.setWindowTitle('MaidAssistant · 聊天气泡与功能')
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setStyleSheet(shell.legacy.STYLE + '''
            FunctionBubble { background: #1e2435; border: 1px solid #aa8192; }
        ''')
        self.resize(390, min(560, QApplication.primaryScreen().availableGeometry().height()-40))
        layout = QVBoxLayout(self)
        head = QHBoxLayout()
        head.addWidget(QLabel('女仆 · 测试对话'))
        head.addStretch()
        close = QPushButton('收起 ×')
        close.clicked.connect(self.hide)
        head.addWidget(close)
        layout.addLayout(head)
        self.line = QLabel(shell.character.line)
        self.line.setWordWrap(True)
        self.line.setStyleSheet('color: #f3d3d6; padding: 6px;')
        layout.addWidget(self.line)
        nav = QHBoxLayout()
        for key, title in [('chat', '聊天'), ('tasks', '待办'), ('files', '文件'), ('live', '解说')]:
            button = QPushButton(title)
            button.clicked.connect(lambda checked=False, k=key: shell.backend.show_panel(k))
            nav.addWidget(button)
        layout.addLayout(nav)
        # Reparent the actual V0.2 widgets. Business methods remain unchanged.
        layout.addWidget(shell.backend.panel_header)
        layout.addWidget(shell.backend.stack, 1)
        views = QHBoxLayout()
        self.half = QPushButton('半身')
        self.full = QPushButton('全身')
        for button, mode in [(self.half, 'half'), (self.full, 'full')]:
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, m=mode: shell.change_view(m))
            views.addWidget(button)
        future = QPushButton('3D 待接入')
        future.clicked.connect(lambda: shell.say('3D 尚未接入；未来复用此独立显示层，支持完整模型及半身/全身镜头。'))
        views.addWidget(future)
        layout.addLayout(views)
        footer = QHBoxLayout()
        hide = QPushButton('隐藏角色')
        hide.setEnabled(shell.has_tray)
        hide.clicked.connect(shell.hide)
        quit_button = QPushButton('退出')
        quit_button.clicked.connect(shell.quit)
        footer.addWidget(hide)
        footer.addWidget(quit_button)
        layout.addLayout(footer)
        self.half.setChecked(True)

    def event(self, event):
        if event.type() == QEvent.WindowDeactivate:
            QTimer.singleShot(0, self.hide_if_inactive)
        return super().event(event)

    def hide_if_inactive(self):
        if not self.isActiveWindow() and QApplication.activePopupWidget() is None:
            self.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.hide()
        event.ignore()


class DesktopShell:
    def __init__(self, app, legacy=None):
        self.app = app
        self.legacy = legacy or load_backend()
        self.has_tray = QSystemTrayIcon.isSystemTrayAvailable()
        self.character = CharacterLayer(self.legacy.ASSET)
        # Preserve tested V0.2 callbacks and data location; never show its main window.
        self.backend = self.legacy.MaidWindow()
        self.backend.stage.timer.stop()
        self.original_stage = self.backend.stage
        self.backend.stage = self.character
        self.bubble = FunctionBubble(self)
        self.character.set_line = self.say
        self.character.characterClicked.connect(self.toggle_bubble)
        self.character.closeRequested.connect(self.close_character)
        self.character.viewChanged.connect(self.sync_view)
        self.tray = QSystemTrayIcon(QIcon(self.character.pixmap), app)
        self.tray.setToolTip('MaidAssistant · 点击显示，右键退出')
        self.tray_menu = QMenu()
        self.tray_menu.addAction('显示角色', self.show)
        self.tray_menu.addAction('隐藏角色', self.hide)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction('退出', self.quit)
        self.tray.setContextMenu(self.tray_menu)
        self.tray.activated.connect(self.tray_activated)
        if self.has_tray:
            self.tray.show()
        app.setQuitOnLastWindowClosed(not self.has_tray)

    def say(self, text):
        self.character.line = text
        self.bubble.line.setText(text)

    def sync_view(self, mode):
        self.bubble.half.setChecked(mode == 'half')
        self.bubble.full.setChecked(mode == 'full')
        if self.bubble.isVisible():
            self.position_bubble()

    def change_view(self, mode):
        self.character.set_view_mode(mode)
        self.say('已切换为完整全身展示。' if mode == 'full' else '现在是半身镜头，人物资源仍然是完整全身。')

    def position_bubble(self):
        area = self.character.screen().availableGeometry()
        x = self.character.x() - self.bubble.width() - 12
        if x < area.left():
            x = self.character.geometry().right() + 12
        x = max(area.left(), min(x, area.right() - self.bubble.width() + 1))
        y = max(area.top(), min(self.character.y(), area.bottom() - self.bubble.height() + 1))
        self.bubble.move(QPoint(x, y))

    def toggle_bubble(self):
        if self.bubble.isVisible():
            self.bubble.hide()
            return
        self.backend.click_character()
        self.backend.show_panel('chat')
        self.position_bubble()
        self.bubble.show()
        self.bubble.raise_()
        self.bubble.activateWindow()
        self.backend.prompt.setFocus()

    def show(self):
        self.character.keep_on_screen()
        self.character.show()
        self.character.raise_()  # Only on explicit tray request, never on a timer.

    def hide(self):
        if self.has_tray:
            self.bubble.hide()
            self.character.hide()

    def tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show()

    def close_character(self):
        if self.has_tray:
            self.hide()
        else:
            self.quit()

    def quit(self):
        self.bubble.hide()
        self.character.hide()
        self.tray.hide()
        self.backend.close()
        self.app.quit()


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont('Microsoft YaHei UI', 10))
    try:
        shell = DesktopShell(app)
    except (OSError, ValueError) as exc:
        print(f'MaidAssistant 启动失败：{exc}', file=sys.stderr)
        return 1
    shell.show()
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
