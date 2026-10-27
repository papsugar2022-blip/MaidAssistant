"""Windows integration probe. No user data, dependencies or desktop settings modified."""
import ctypes
import json
import sys
from ctypes import wintypes
from pathlib import Path

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QWidget

from character_layer import CharacterLayer

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
under = QWidget()
under.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
under.setWindowTitle('MaidAssistant · 透明交互验证')
under.setStyleSheet('background: #457c65;')
under.setGeometry(80, 80, 820, 650)
under.show()
layer = CharacterLayer(Path(sys.argv[1]))
layer.move(under.pos() + QPoint(420, 60))
layer.show()
bubble = QLabel('点击成功 · 透明角色与交互可以共存')
bubble.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
bubble.setStyleSheet('background: #fff4e6; color: #302638; padding: 20px;')
bubble.resize(350, 85)
bubble.move(under.pos() + QPoint(30, 80))
clicks = []
def clicked():
    clicks.append(True)
    bubble.setVisible(not bubble.isVisible())
    print('CHARACTER_CLICK bubble=' + str(bubble.isVisible()), flush=True)
layer.characterClicked.connect(clicked)

user = ctypes.WinDLL('user32', use_last_error=True)
user.WindowFromPoint.argtypes = [wintypes.POINT]
user.WindowFromPoint.restype = wintypes.HWND
user.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
user.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
user.GetWindowLongW.restype = wintypes.LONG
results = []
def record(name, ok, detail=''):
    results.append({'name': name, 'pass': bool(ok), 'detail': detail})
    print(json.dumps(results[-1], ensure_ascii=False), flush=True)
    if not ok:
        raise AssertionError(name + ': ' + detail)

def native_hit(point):
    rect = wintypes.RECT()
    user.GetClientRect(int(layer.winId()), ctypes.byref(rect))
    p = wintypes.POINT(round(point.x() * rect.right / layer.width()), round(point.y() * rect.bottom / layer.height()))
    user.ClientToScreen(int(layer.winId()), ctypes.byref(p))
    return user.WindowFromPoint(p)

def run_mode(mode):
    layer.set_view_mode(mode)
    layer.raise_()
    QTest.qWait(150)
    holes, body = [], []
    for y in range(5, layer.height(), 15):
        for x in range(5, layer.width(), 15):
            p = QPoint(x, y)
            if layer.image.pixelColor(p).alpha() == 0:
                holes.append(p)
            elif layer.image.pixelColor(p).alpha() > 240:
                body.append(p)
    # Avoid shape boundaries when testing native DPI rounding.
    holes = [p for p in holes if all(not layer.mask().contains(p + d) for d in (QPoint(-2,0),QPoint(2,0),QPoint(0,-2),QPoint(0,2)))]
    body = [p for p in body if all(layer.mask().contains(p + d) for d in (QPoint(-2,0),QPoint(2,0),QPoint(0,-2),QPoint(0,2)))]
    record(mode + ': native holes hit lower window', bool(holes) and all(native_hit(p) == int(under.winId()) for p in holes), str(len(holes)) + ' sample points')
    record(mode + ': native character hit layer', bool(body) and all(native_hit(p) == int(layer.winId()) for p in body), str(len(body)) + ' sample points')
    # Read actual Windows composition from our controlled lower-window area.
    screenshot = under.screen().grabWindow(0, under.x(), under.y(), under.width(), under.height()).toImage()
    dpr = screenshot.devicePixelRatio()
    p = layer.pos() - under.pos() + holes[len(holes)//2]
    color = screenshot.pixelColor(round(p.x()*dpr), round(p.y()*dpr))
    record(mode + ': transparent composition', abs(color.red()-69)<3 and abs(color.green()-124)<3 and abs(color.blue()-101)<3, color.name())
    QTest.mouseClick(layer, Qt.LeftButton, pos=body[len(body)//2])
    QTest.qWait(50)
    record(mode + ': Qt click opens bubble', bubble.isVisible())
    bubble.hide()
    layer.raise_()

def run():
    try:
        record('translucent + frameless', layer.testAttribute(Qt.WA_TranslucentBackground) and bool(layer.windowFlags() & Qt.FramelessWindowHint))
        record('native not topmost', not user.GetWindowLongW(int(layer.winId()), -20) & 0x8)
        run_mode('half')
        run_mode('full')
        record('two clicks delivered', len(clicks) == 2)
        if '--output' in sys.argv:
            output = Path(sys.argv[sys.argv.index('--output') + 1])
            output.mkdir(parents=True, exist_ok=True)
            (output / 'native-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
        if '--interactive' in sys.argv:
            print('READY_FOR_MANUAL_CLICK', flush=True)
        else:
            app.exit(0)
    except Exception as exc:
        print('FAILED: ' + repr(exc), flush=True)
        app.exit(1)
QTimer.singleShot(400, run)
raise SystemExit(app.exec())
