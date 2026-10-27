"""Exercise preserved services on temporary data, never the real tasks.json."""
import json
import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from main import DesktopShell, load_backend

app = QApplication(sys.argv)
legacy_root = Path(sys.argv[1])
output = Path(sys.argv[2])
output.mkdir(parents=True, exist_ok=True)
legacy = load_backend(legacy_root)
actual_data = legacy.DATA_FILE
original_bytes = actual_data.read_bytes() if actual_data.exists() else None
results = []
def check(name, condition):
    results.append({'name': name, 'pass': bool(condition)})
    print(json.dumps(results[-1], ensure_ascii=False), flush=True)
    assert condition, name

with tempfile.TemporaryDirectory(prefix='maid-test-') as tmp:
    legacy.DATA_FILE = Path(tmp) / 'data' / 'tasks.json'
    shell = DesktopShell(app, legacy)
    shell.show()
    QTest.qWait(150)
    check('default role only', shell.character.isVisible() and not shell.bubble.isVisible() and not shell.backend.isVisible())
    check('old stage timer stopped', not shell.original_stage.timer.isActive())
    shell.character.grab().save(str(output / 'character-half.png'))
    # Direct Qt-dispatched click, not an injected physical Windows click.
    points = [QPoint(x,y) for y in range(20, shell.character.height(),20) for x in range(20,shell.character.width(),20) if shell.character.mask().contains(QPoint(x,y))]
    QTest.mouseClick(shell.character, Qt.LeftButton, pos=points[len(points)//2])
    QTest.qWait(100)
    check('click opens migrated bubble', shell.bubble.isVisible())
    shell.backend.prompt.setText('透明桌面测试')
    shell.backend.send_message()
    check('test chat preserved', '透明桌面测试' in shell.backend.dialogue.toPlainText() and '测试对话' in shell.character.line)
    shell.backend.show_panel('tasks')
    shell.backend.task_entry.setText('isolated test task')
    shell.backend.add_task()
    task_id = shell.backend.tasks[0]['id']
    check('task add persisted', legacy.load_tasks()[0]['title'] == 'isolated test task')
    shell.backend.set_task_done(task_id, True)
    check('task complete persisted', legacy.load_tasks()[0]['done'] is True)
    shell.backend.set_task_done(task_id, False)
    check('task reopen persisted', legacy.load_tasks()[0]['done'] is False)
    shell.bubble.grab().save(str(output / 'tasks-bubble.png'))
    shell.backend.remove_task(task_id)
    check('task removal persisted', legacy.load_tasks() == [])
    for key, index in [('chat',0),('tasks',1),('files',2),('live',2)]:
        shell.backend.show_panel(key)
        check(key + ' navigation preserved', shell.backend.stack.currentIndex() == index)
    shell.change_view('full')
    check('full view and controls synced', shell.character.view_mode == 'full' and shell.bubble.full.isChecked() and not shell.bubble.half.isChecked())
    shell.character.grab().save(str(output / 'character-full.png'))
    shell.change_view('half')
    check('half view synced', shell.character.view_mode == 'half' and shell.bubble.half.isChecked())
    shell.backend.show_panel('chat')
    shell.bubble.grab().save(str(output / 'chat-bubble.png'))
    QTest.keyClick(shell.bubble, Qt.Key_Escape)
    check('Esc dismisses bubble', not shell.bubble.isVisible() and shell.character.isVisible())
    check('tray available on this Windows session', shell.has_tray and shell.tray.isVisible())
    actions = shell.tray_menu.actions()
    actions[1].trigger()
    check('tray hide', not shell.character.isVisible() and not shell.bubble.isVisible())
    actions[0].trigger()
    check('tray show', shell.character.isVisible() and not shell.bubble.isVisible())
    shell.character.close()
    check('close role preserves tray recovery', not shell.character.isVisible() and shell.tray.isVisible())
    actions[0].trigger()
    shell.toggle_bubble()
    app.processEvents()
    # Activate a controlled unrelated window: popup yields to other software.
    from PySide6.QtWidgets import QWidget
    other = QWidget()
    other.setWindowTitle('MaidAssistant · focus test')
    other.show()
    other.activateWindow()
    QTest.qWait(200)
    check('bubble dismisses when another window activates', not shell.bubble.isVisible())
    other.close()
    check('real user data unchanged', (actual_data.read_bytes() if actual_data.exists() else None) == original_bytes)
    QTimer.singleShot(50, actions[-1].trigger)
    check('tray exit terminates event loop', app.exec() == 0)
    check('tray exit hides surfaces and tray', not shell.character.isVisible() and not shell.bubble.isVisible() and not shell.tray.isVisible())
    (output / 'migration-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print('ALL MIGRATION CHECKS PASSED', flush=True)
