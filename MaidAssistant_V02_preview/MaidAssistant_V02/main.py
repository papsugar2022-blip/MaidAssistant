"""Maid Assistant V0.2: 2D full-body character, startup scene and local tasks.

Built as an isolated preview. Does not modify an existing MaidAssistant project.
Python 3.10+ and PySide6 required. This is intentionally NOT a 3D renderer.
"""

import json
import math
import sys
import uuid
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal, QRectF
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QScrollArea, QStackedWidget,
    QTextEdit, QVBoxLayout, QWidget,
)

ROOT = Path(__file__).resolve().parent
ASSET = ROOT / 'assets' / 'MaidAssistant_V12_BlueEyes.png'
DATA_FILE = ROOT / 'data' / 'tasks.json'

STYLE = """
QMainWindow, QWidget#root { background: #171c2a; color: #f8f5ef; }
QLabel { color: #f0eee9; background: transparent; }
QLabel#muted { color: #a6aec1; }
QLabel#title { font-size: 19px; font-weight: 800; }
QLabel#section { font-size: 15px; font-weight: 700; }
QFrame#side { background: #111626; border-right: 1px solid #374055; }
QFrame#right { background: #1e2435; border-left: 1px solid #374055; }
QFrame#top { background: #161b2a; border-bottom: 1px solid #374055; }
QFrame#taskrow { background: #2a3144; border-radius: 11px; }
QPushButton { border: 0; border-radius: 10px; padding: 10px 14px; background: #2b3347; color: #e9eaf0; font-size: 13px; }
QPushButton:hover { background: #39455f; }
QPushButton:pressed { background: #52607b; }
QPushButton#primary { background: #97465c; color: #fff5f6; font-weight: 700; }
QPushButton#primary:hover { background: #ae5870; }
QPushButton#nav { text-align: left; padding: 14px 18px; background: transparent; }
QPushButton#nav:hover { background: #283248; }
QPushButton#nav:checked { background: #36405a; border-left: 3px solid #d5a3ae; }
QPushButton#mode:checked { background: #805068; }
QPushButton#ghost { background: transparent; color: #b8bed0; }
QLineEdit, QTextEdit { background: #272e40; border: 1px solid #4d566b; border-radius: 10px; padding: 10px; color: white; selection-background-color: #805068; }
QLineEdit:focus, QTextEdit:focus { border-color: #c587a0; }
QCheckBox { font-size: 13px; color: #f0eee9; }
QScrollArea { border: 0; background: transparent; }
"""


def make_label(text, object_name='', size=None, strong=False):
    label = QLabel(text)
    if object_name:
        label.setObjectName(object_name)
    if size:
        font = QFont('Microsoft YaHei UI', size)
        font.setBold(strong)
        label.setFont(font)
    label.setWordWrap(True)
    return label


class CharacterStage(QWidget):
    characterClicked = Signal()

    def __init__(self):
        super().__init__()
        self.image = QPixmap(str(ASSET))
        self._display_cache_key = None
        self._display_image = QPixmap()
        self.view_mode = 'half'
        self.line = '欢迎回来，主人。今天需要我做什么？'
        self.tick = 0
        self.person_rect = QRectF()
        self.setMinimumSize(420, 440)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip('单击人物：触发一句测试台词')
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)

    def animate(self):
        self.tick += 1
        self.update()

    def set_view_mode(self, mode):
        if mode in ('half', 'full'):
            self.view_mode = mode
            self.update()

    def set_line(self, line):
        self.line = line
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)
        w, h = self.width(), self.height()
        bg = QLinearGradient(0, 0, w, h)
        bg.setColorAt(0, QColor('#3b4054'))
        bg.setColorAt(.47, QColor('#2d3449'))
        bg.setColorAt(1, QColor('#1b2336'))
        p.fillRect(self.rect(), bg)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(239, 190, 161, 23))
        p.drawEllipse(QRectF(w*.04, h*.04, w*.72, h*.92))
        p.setBrush(QColor(178, 149, 174, 20))
        p.drawEllipse(QRectF(w*.4, h*.14, w*.5, h*.8))

        p.setPen(QColor('#c8c5cd'))
        p.setFont(QFont('Georgia', 10, QFont.Bold))
        p.drawText(24, 33, 'MAID ASSISTANT  /  2D')
        p.setFont(QFont('Microsoft YaHei UI', 10))
        p.setPen(QColor('#a9b1c5'))
        p.drawText(24, 57, '半身视角' if self.view_mode == 'half' else '完整全身视角')

        if not self.image.isNull():
            bob = math.sin(self.tick / 14) * 2.5
            iw, ih = self.image.width(), self.image.height()
            if self.view_mode == 'full':
                scaled_h = min(h * .83, max(1, w - 48) * ih / iw)
                y = h - scaled_h - 30 + bob
            else:
                # Camera-like crop: uses THE SAME full-body image, enlarged.
                scaled_h = h * 1.92
                y = h * .05 + bob
            scaled_w = scaled_h * iw / ih
            x = (w-scaled_w)/2
            self.person_rect = QRectF(x, y, scaled_w, scaled_h)
            # Always resample the original at native display pixel density.
            # Cache by size/DPI; never resize a previously scaled image.
            dpr = self.devicePixelRatioF()
            pixel_w = max(1, math.ceil(scaled_w * dpr))
            pixel_h = max(1, math.ceil(scaled_h * dpr))
            cache_key = (pixel_w, pixel_h, dpr)
            if cache_key != self._display_cache_key:
                self._display_image = self.image.scaled(
                    pixel_w, pixel_h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation,
                )
                self._display_image.setDevicePixelRatio(dpr)
                self._display_cache_key = cache_key
            p.drawPixmap(self.person_rect, self._display_image,
                         QRectF(self._display_image.rect()))
        else:
            p.setPen(Qt.white)
            p.drawText(self.rect(), Qt.AlignCenter, '角色素材缺失: assets/MaidAssistant_V12_BlueEyes.png')

        # Chat bubble anchored near bottom, not painted over as a system dialog.
        bubble_h = 78
        bubble = QRectF(22, h-bubble_h-22, w-44, bubble_h)
        p.setPen(QPen(QColor(218, 221, 235, 65), 1))
        p.setBrush(QColor(17, 22, 34, 225))
        p.drawRoundedRect(bubble, 14, 14)
        p.setPen(QColor('#f3d3d6'))
        p.setFont(QFont('Microsoft YaHei UI', 11, QFont.Bold))
        p.drawText(QRectF(bubble.left()+16, bubble.top()+8, bubble.width()-30, 22), '女仆')
        p.setPen(QColor('#f5f4ef'))
        p.setFont(QFont('Microsoft YaHei UI', 11))
        p.drawText(QRectF(bubble.left()+16, bubble.top()+33, bubble.width()-32, 38), Qt.TextWordWrap, self.line)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.person_rect.contains(event.position()):
            self.characterClicked.emit()
        super().mousePressEvent(event)


def load_tasks():
    try:
        tasks = json.loads(DATA_FILE.read_text(encoding='utf-8'))
        if isinstance(tasks, list):
            return [x for x in tasks if isinstance(x, dict) and 'title' in x]
    except (OSError, ValueError):
        pass
    return []


def save_tasks(tasks):
    DATA_FILE.parent.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding='utf-8')


class MaidWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Maid Assistant · V0.2 视觉原型')
        self.resize(1280, 780)
        self.setMinimumSize(1040, 610)
        self.tasks = load_tasks()
        self.setStyleSheet(STYLE)
        self.build_ui()
        self.show_panel('chat')

    def build_ui(self):
        root = QWidget()
        root.setObjectName('root')
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QFrame()
        header.setObjectName('top')
        header.setFixedHeight(64)
        hb = QHBoxLayout(header)
        hb.setContentsMargins(23, 9, 22, 9)
        title = make_label('✦  Maid Assistant', 'title')
        hb.addWidget(title)
        hb.addStretch(1)
        hb.addWidget(make_label('全身角色 · 游戏式启动主界面', 'muted'))
        hb.addSpacing(20)
        self.mode_2d = QPushButton('2D 模式')
        self.mode_2d.setObjectName('mode')
        self.mode_2d.setCheckable(True)
        self.mode_2d.setChecked(True)
        self.mode_3d = QPushButton('3D 模式（待接入）')
        self.mode_3d.clicked.connect(self.about_3d)
        hb.addWidget(self.mode_2d)
        hb.addWidget(self.mode_3d)
        outer.addWidget(header)

        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)
        outer.addLayout(content, 1)

        side = QFrame()
        side.setObjectName('side')
        side.setFixedWidth(196)
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(10, 25, 10, 17)
        side_layout.setSpacing(9)
        for key, text in [('chat', '✦  对话'), ('tasks', '☑  任务管理'), ('files', '▤  文件整理'), ('live', '◉  游戏解说')]:
            b = QPushButton(text)
            b.setObjectName('nav')
            b.setCheckable(True)
            b.clicked.connect(lambda _, k=key: self.show_panel(k))
            side_layout.addWidget(b)
            setattr(self, 'nav_'+key, b)
        side_layout.addStretch(1)
        side_layout.addWidget(make_label('V0.2 · 本地预览', 'muted'))
        side_layout.addWidget(make_label('3D 保留全身模型；默认镜头只展示上半身。', 'muted'))
        content.addWidget(side)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(14, 14, 14, 16)
        center_layout.setSpacing(10)
        self.stage = CharacterStage()
        self.stage.characterClicked.connect(self.click_character)
        center_layout.addWidget(self.stage, 1)
        controls = QHBoxLayout()
        controls.addWidget(make_label('角色视角', 'muted'))
        controls.addStretch(1)
        self.half_btn = QPushButton('半身')
        self.half_btn.setCheckable(True)
        self.half_btn.setChecked(True)
        self.full_btn = QPushButton('全身')
        self.full_btn.setCheckable(True)
        self.half_btn.clicked.connect(lambda: self.change_view('half'))
        self.full_btn.clicked.connect(lambda: self.change_view('full'))
        controls.addWidget(self.half_btn)
        controls.addWidget(self.full_btn)
        center_layout.addLayout(controls)
        content.addWidget(center, 1)

        right = QFrame()
        right.setObjectName('right')
        right.setFixedWidth(335)
        rp = QVBoxLayout(right)
        rp.setContentsMargins(19, 24, 19, 20)
        rp.setSpacing(13)
        self.panel_header = make_label('', 'section')
        rp.addWidget(self.panel_header)
        self.stack = QStackedWidget()
        rp.addWidget(self.stack, 1)
        content.addWidget(right)

        chat = QWidget()
        chat_layout = QVBoxLayout(chat)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(11)
        chat_layout.addWidget(make_label('当前为固定台词测试版，尚未连接大模型 API。', 'muted'))
        self.dialogue = QTextEdit()
        self.dialogue.setReadOnly(True)
        self.dialogue.setText('女仆：欢迎回来，主人。\n')
        chat_layout.addWidget(self.dialogue, 1)
        self.prompt = QLineEdit()
        self.prompt.setPlaceholderText('输入测试消息…')
        self.prompt.returnPressed.connect(self.send_message)
        chat_layout.addWidget(self.prompt)
        send_btn = QPushButton('发送测试消息')
        send_btn.setObjectName('primary')
        send_btn.clicked.connect(self.send_message)
        chat_layout.addWidget(send_btn)
        self.stack.addWidget(chat)

        tasks = QWidget()
        tl = QVBoxLayout(tasks)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(12)
        tl.addWidget(make_label('待办会保存在本项目 data/tasks.json 中。', 'muted'))
        self.task_entry = QLineEdit()
        self.task_entry.setPlaceholderText('例如：完成 Python 练习')
        self.task_entry.returnPressed.connect(self.add_task)
        tl.addWidget(self.task_entry)
        add_btn = QPushButton('添加任务')
        add_btn.setObjectName('primary')
        add_btn.clicked.connect(self.add_task)
        tl.addWidget(add_btn)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.task_list_root = QWidget()
        self.task_list_layout = QVBoxLayout(self.task_list_root)
        self.task_list_layout.setContentsMargins(0, 0, 0, 0)
        self.task_list_layout.setSpacing(9)
        scroll.setWidget(self.task_list_root)
        tl.addWidget(scroll, 1)
        self.stack.addWidget(tasks)

        placeholder = QWidget()
        pl = QVBoxLayout(placeholder)
        pl.setContentsMargins(0, 0, 0, 0)
        self.todo_text = make_label('功能还未接入。\n先完成可用的主界面，后续再接入真实功能。', 'muted')
        pl.addWidget(self.todo_text)
        pl.addStretch(1)
        self.stack.addWidget(placeholder)
        self.refresh_tasks()

    def change_view(self, mode):
        self.stage.set_view_mode(mode)
        self.half_btn.setChecked(mode == 'half')
        self.full_btn.setChecked(mode == 'full')
        self.stage.set_line('已切换为完整全身展示。' if mode == 'full' else '现在是半身镜头，人物资源仍然是完整全身。')

    def about_3d(self):
        QMessageBox.information(self, '3D 模式', '这是 2D 可运行预览，尚未制作或导入正式 3D 全身模型。\n\n目标：全身 3D 资源 + 默认半身镜头 + 可切换全身视角。')

    def show_panel(self, key):
        for k in ('chat', 'tasks', 'files', 'live'):
            getattr(self, 'nav_'+k).setChecked(k == key)
        if key == 'chat':
            self.stack.setCurrentIndex(0)
            self.panel_header.setText('聊天 · 测试')
        elif key == 'tasks':
            self.stack.setCurrentIndex(1)
            self.panel_header.setText('我的任务')
        else:
            self.stack.setCurrentIndex(2)
            self.panel_header.setText('文件整理 · 后续版本' if key == 'files' else '游戏解说 · 后续版本')
            self.todo_text.setText('文件导入及钉钉授权要等后续版本。' if key == 'files' else '《战争雷霆》的手动播报与事件解说将另行开发。')

    def click_character(self):
        line = '哎呀，被主人发现啦。今天也请多多指教～'
        self.stage.set_line(line)
        self.dialogue.append('女仆：' + line)

    def send_message(self):
        message = self.prompt.text().strip()
        if not message:
            return
        self.dialogue.append('你：' + message)
        response = ('主人，我已经收到你的消息。这里还是测试对话，下一版才接入真正的 AI。')
        self.dialogue.append('女仆：' + response)
        self.stage.set_line(response)
        self.prompt.clear()

    def refresh_tasks(self):
        layout = self.task_list_layout
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        if not self.tasks:
            layout.addWidget(make_label('暂无任务。\n先为女仆安排一件工作吧～', 'muted'))
        for task in self.tasks:
            row = QFrame()
            row.setObjectName('taskrow')
            box = QHBoxLayout(row)
            box.setContentsMargins(8, 8, 5, 8)
            check = QCheckBox(task['title'])
            check.setChecked(bool(task.get('done', False)))
            check.stateChanged.connect(lambda state, id_=task['id']: self.set_task_done(id_, state != 0))
            box.addWidget(check, 1)
            remove = QPushButton('×')
            remove.setObjectName('ghost')
            remove.setFixedWidth(31)
            remove.setToolTip('删除任务')
            remove.clicked.connect(lambda _, id_=task['id']: self.remove_task(id_))
            box.addWidget(remove)
            layout.addWidget(row)
        layout.addStretch(1)

    def add_task(self):
        title = self.task_entry.text().strip()
        if not title:
            return
        self.tasks.append({'id':uuid.uuid4().hex[:12], 'title':title, 'done':False})
        save_tasks(self.tasks)
        self.task_entry.clear()
        self.refresh_tasks()
        self.stage.set_line('收到！这项任务已经替主人记下了。')

    def set_task_done(self, id_, done):
        for task in self.tasks:
            if task['id'] == id_:
                task['done'] = done
                break
        save_tasks(self.tasks)
        self.stage.set_line('完成任务啦！辛苦了，主人。' if done else '任务已恢复为待办。')

    def remove_task(self, id_):
        self.tasks = [task for task in self.tasks if task['id'] != id_]
        save_tasks(self.tasks)
        self.refresh_tasks()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont('Microsoft YaHei UI', 10))
    window = MaidWindow()
    window.show()
    raise SystemExit(app.exec())
