# ThunderAgent V0.1

面向 MuMu Android 模拟器的游戏画面采集与人工授权测试工具。V0.1 只提供连接、截图、监控、保存截图和可选的单次手动触控，不包含自动刷关、自动战斗、自动消耗资源或绕过游戏限制的功能。

## 1. 环境

- Windows 10/11
- Python 3.11（建议）
- MuMu 模拟器已启动
- 游戏已由用户手动打开
- MuMu ADB 调试已开启

## 2. 安装

在项目目录打开 PowerShell：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

如果 PowerShell 不允许激活脚本，可直接运行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

## 3. 配置 ADB

MuMu 不同版本、实例和网络模式的 ADB 端口可能不同。先在 MuMu 的设置中心/多开器中查看当前实例的 ADB 端口。

常见端口包括 16384、16416、16448 等，但请以你本机显示的端口为准。项目会尝试 config.yaml 中的候选端口。

如果电脑已安装 Android Platform Tools，通常 `adb` 可直接使用。否则在 config.yaml 中填写 adb.exe 完整路径，例如：

```yaml
adb_path: "C:/Android/platform-tools/adb.exe"
```

如果有多个模拟器或手机连接，请将 `device_serial` 设置为实际设备序列号，例如：

```yaml
device_serial: "127.0.0.1:16384"
```

## 4. 启动

```powershell
python main.py
```

操作顺序：

1. 启动 MuMu，并手动打开游戏。
2. 在 ThunderAgent 点击「连接设备」。
3. 点击「单次截图」确认画面。
4. 点击「开始实时监控」。
5. 使用「保存当前截图」保存大厅、每日任务、战斗、结算等截图。
6. 关闭窗口会停止截图线程。

## 5. 手动点击测试

默认关闭。只有在确认游戏规则允许相应自动化操作后，才勾选「我已确认游戏规则允许，并启用手动测试点击」。点击操作只发送一次，不会自动循环。

坐标以设备实际截图像素为准；如果截图不是 720x1280，控件仍会按实际画面范围校验。

## 6. 常见问题

### 找不到设备
- 确认 MuMu 正在运行。
- 确认 ADB 调试已开启。
- 查看 MuMu 当前实例的 ADB 端口。
- 在终端运行 `adb devices -l`。
- 多设备时填写 `device_serial`。

### 截图失败
- 先重新连接设备。
- 检查 ADB 路径和版本。
- 关闭并重新启动模拟器后再试。

### 画面不是 720x1280
程序会显示设备真实截图尺寸。请检查 MuMu 的分辨率设置；不要仅根据模拟器窗口大小判断 Android 内部画面分辨率。

## 7. 下一阶段

V0.2 可在获得真实截图样本后，建立经过人工标注的界面状态识别集（大厅、任务、战斗、结算、加载、未知）。识别不确定时应停止并请求人工确认。
