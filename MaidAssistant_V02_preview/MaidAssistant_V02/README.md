# V0.2 主窗口预览

本目录保留可运行的 2D 主窗口及聊天 / 待办逻辑，也供透明桌面入口复用。

在仓库根目录运行：

```powershell
.\.venv\Scripts\python.exe .\MaidAssistant_V02_preview\MaidAssistant_V02\main.py
```

使用 `assets/MaidAssistant_V12_BlueEyes.png`，保留半身 / 全身视角及按 DPI 平滑缩放缓存。聊天是固定台词测试；待办保存在本目录运行时生成的 `data/tasks.json`，不纳入 Git。

文件整理、游戏解说、3D 模式是未实现的占位入口。默认透明桌面入口、依赖安装和后续规划见[项目 README](../../README.md)。不要同时用两个入口编辑同一份待办。
