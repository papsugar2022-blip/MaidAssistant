# MaidAssistant

**面向 Windows 桌面的虚拟女仆助手：从可运行的 2D 原型逐步探索 3D 角色、AI 秘书与游戏解说。**

当前是 Python / PySide6 桌面原型。默认启动独立的透明角色层，点击人物后展开聊天与功能面板。聊天目前使用固定测试回复，尚未连接大模型；3D、AI 秘书和游戏解说属于后续计划。

## 已实现

- 透明、无边框的 2D 角色显示层，默认仅展示人物，不强制置顶。
- 根据角色 alpha 建立窗口区域，让透明部分避开鼠标命中；已完成受控下层窗口的 Windows 原生命中验证，真实桌面图标操作仍需人工验收。
- 点击角色展开聊天气泡与功能菜单，支持收起、拖动，以及切换其他窗口后自动收起气泡。
- 使用同一张 V1.2 蓝瞳全身立绘切换半身 / 全身视角。
- 测试聊天输入和固定台词反馈。
- 本地待办新增、完成、恢复、删除及 JSON 持久化。
- 系统托盘显示、隐藏和退出；关闭角色后可从托盘恢复。
- 保留可独立运行的 V0.2 主窗口预览。

文件整理、游戏解说和 3D 的界面入口是占位入口，不代表功能已经实现。

## 技术栈与实现

| 部分 | 当前实现 |
| --- | --- |
| 语言 / 环境 | Python 3.11；本地验证平台为 Windows |
| 桌面 UI | PySide6 / Qt Widgets、信号与槽、系统托盘 |
| 2D 显示 | PNG alpha、QPainter、QImage / QPixmap、平滑缩放 |
| 鼠标区域 | 根据 alpha 生成 QRegion，并设置窗口 mask |
| 数据 | 本地 JSON 待办文件，无数据库和云同步 |
| 验证 | QtTest、Windows 原生命中检查、受控透明合成检查 |

角色显示层与功能面板分离，透明桌面外壳复用 V0.2 的业务方法。当前仍通过动态导入复用旧模块；后续计划将业务逻辑提取为独立服务，以便接入其他角色渲染器。

V0.2 的角色绘制从原图按显示尺寸和 DPI 平滑缩放并缓存，避免反复缩放。透明角色层使用平滑缩放；其高 DPI 显示质量仍需进一步优化和验收。

## 运行

在 Windows 上使用 Python 3.11。已有可用虚拟环境时，直接运行：

```powershell
.\.venv\Scripts\python.exe .\main.py
```

新克隆的仓库不包含虚拟环境。首次配置可执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe .\main.py
```

当前原型运行不需要 API Key，也不调用大模型服务。依赖固定版本见 [requirements.txt](requirements.txt)。尚未提供 exe 安装包。

### 操作

- 点击人物展开面板，点“收起”或在气泡内按 Esc 收起。
- 按住人物拖动，在面板中切换半身 / 全身。
- 托盘右键提供显示、隐藏、退出；托盘图标可能位于 Windows 的隐藏图标区域。
- 其他软件可以遮挡角色，托盘“显示角色”可以将其恢复到前方。

原 V0.2 主窗口可单独启动：

```powershell
.\.venv\Scripts\python.exe .\MaidAssistant_V02_preview\MaidAssistant_V02\main.py
```

两个入口共用 `MaidAssistant_V02_preview/MaidAssistant_V02/data/tasks.json`。不存在时首次保存待办会创建该文件。此目录不纳入 Git；两个版本没有并发写入保护，请勿同时编辑待办。

## 仓库结构

```text
main.py                         # 默认透明桌面入口
requirements.txt                # 固定运行依赖
desktop_v03/
  main.py                       # 聊天气泡、功能面板与托盘
  character_layer.py            # 透明角色显示和交互
  verify_layer.py               # Windows 原生显示层验证
  verify_migration.py           # 临时数据上的功能迁移检查
MaidAssistant_V02_preview/
  MaidAssistant_V02/
    main.py                     # V0.2 主窗口和复用业务逻辑
    assets/
      MaidAssistant_V12_BlueEyes.png
TEST_RESULTS.md                 # 历史测试记录与验证边界
```

本地虚拟环境、备份、私人数据、密钥、缓存、生成的测试产物和旧发布压缩包由 `.gitignore` 排除。运行所需的正式立绘随源代码保留。

## 验证

本项目以 Windows 桌面环境为目标，验证脚本需要可用的交互式桌面和系统托盘：

```powershell
.\.venv\Scripts\python.exe .\desktop_v03\verify_layer.py .\MaidAssistant_V02_preview\MaidAssistant_V02\assets\MaidAssistant_V12_BlueEyes.png --output .\desktop_v03\test_artifacts
.\.venv\Scripts\python.exe .\desktop_v03\verify_migration.py .\MaidAssistant_V02_preview\MaidAssistant_V02 .\desktop_v03\test_artifacts
```

迁移验证使用临时待办文件，生成的测试产物不提交。原生命中采样和 Qt 合成点击不等同于人工桌面验收；测试记录与未解决问题见 [TEST_RESULTS.md](TEST_RESULTS.md)。当前没有 CI 流水线。

## 后续计划（尚未实现）

1. **整理架构和显示质量**：分离业务服务与 UI，完善多屏 / 混合 DPI、边缘显示及人工桌面交互验证。
2. **AI 秘书**：接入大模型 API、对话上下文和可控的工具调用；逐步探索任务提醒、文件整理与授权后的外部服务集成。
3. **完整 3D 角色**：探索 Godot 等渲染方案、完整全身模型及半身 / 全身镜头，与现有助手服务对接。当前没有 3D 模型、绑定、动画或渲染实现。
4. **游戏解说**：以《战争雷霆》为探索场景，先研究手动事件输入，再评估事件驱动解说与语音输出。当前没有游戏事件采集或解说实现。

这些是开发方向，不是已交付能力或确定的交付时间表。

## 项目说明

这是持续迭代的个人求职展示项目，用于呈现桌面 UI、透明窗口交互、本地数据管理及逐步拆分架构的实践。当前未添加开源许可证；公开展示不表示已授予代码或角色素材的复用许可。素材使用范围需单独确认。
