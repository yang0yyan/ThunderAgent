from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import cv2
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPushButton, QSpinBox, QVBoxLayout, QWidget
)

from .adb import AdbClient, AdbError


class CaptureWorker(QThread):
    frame_ready = Signal(object)
    error = Signal(str)

    def __init__(self, client: AdbClient, interval_ms: int):
        super().__init__()
        self.client = client
        self.interval_ms = max(150, interval_ms)
        self._running = True
        self._paused = False

    def stop(self):
        self._running = False

    def set_paused(self, paused: bool):
        self._paused = paused

    def run(self):
        while self._running:
            if self._paused:
                self.msleep(150)
                continue
            try:
                frame = self.client.screenshot()
                self.frame_ready.emit(frame)
            except Exception as exc:
                self.error.emit(str(exc))
                self.msleep(1200)
            self.msleep(self.interval_ms)


class MainWindow(QMainWindow):
    def __init__(self, client: AdbClient, config: dict):
        super().__init__()
        self.client = client
        self.config = config
        self.worker = None
        self.last_frame = None
        self.setWindowTitle("ThunderAgent V0.1 - MuMu 连接与画面监控")
        self.resize(1050, 850)

        self.preview = QLabel("请先启动 MuMu，然后点击「连接设备」")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(360, 600)
        self.preview.setStyleSheet("background:#17191d;color:#d7dbe0;border:1px solid #444;")
        self.status = QLabel("状态：未连接")
        self.device = QLabel("设备：未选择")

        self.connect_btn = QPushButton("连接设备")
        self.capture_btn = QPushButton("单次截图")
        self.start_btn = QPushButton("开始实时监控")
        self.pause_btn = QPushButton("暂停监控")
        self.stop_btn = QPushButton("停止监控")
        self.save_btn = QPushButton("保存当前截图")

        self.x_input = QSpinBox()
        self.x_input.setRange(0, 719)
        self.x_input.setPrefix("X ")
        self.y_input = QSpinBox()
        self.y_input.setRange(0, 1279)
        self.y_input.setPrefix("Y ")
        self.manual_enable = QCheckBox("我已确认游戏规则允许，并启用手动测试点击")
        self.tap_btn = QPushButton("发送一次测试点击")
        self.tap_btn.setEnabled(False)

        self.connect_btn.clicked.connect(self.connect_device)
        self.capture_btn.clicked.connect(self.capture_once)
        self.start_btn.clicked.connect(self.start_monitor)
        self.pause_btn.clicked.connect(self.pause_monitor)
        self.stop_btn.clicked.connect(self.stop_monitor)
        self.save_btn.clicked.connect(self.save_frame)
        self.manual_enable.toggled.connect(self.tap_btn.setEnabled)
        self.tap_btn.clicked.connect(self.manual_tap)

        controls = QHBoxLayout()
        for widget in (self.connect_btn, self.capture_btn, self.start_btn,
                       self.pause_btn, self.stop_btn, self.save_btn):
            controls.addWidget(widget)

        tap_row = QHBoxLayout()
        tap_row.addWidget(QLabel("手动触控测试（像素坐标）："))
        tap_row.addWidget(self.x_input)
        tap_row.addWidget(self.y_input)
        tap_row.addWidget(self.tap_btn)

        layout = QVBoxLayout()
        layout.addWidget(self.status)
        layout.addWidget(self.device)
        layout.addLayout(controls)
        layout.addWidget(self.preview, 1)
        layout.addWidget(self.manual_enable)
        layout.addLayout(tap_row)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def connect_device(self):
        try:
            serial = self.client.connect()
            size = self.client.screen_size() or "分辨率读取失败"
            self.device.setText(f"设备：{serial} | {size}")
            self.status.setText("状态：已连接")
            logging.info("设备信息：%s | %s", serial, size)
            QMessageBox.information(self, "连接成功", f"已连接：{serial}\n{size}")
        except Exception as exc:
            self.status.setText("状态：连接失败")
            logging.exception("连接失败")
            QMessageBox.critical(self, "ADB 连接失败", str(exc))

    def show_frame(self, frame):
        self.last_frame = frame
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888).copy()
        pixmap = QPixmap.fromImage(qimg).scaled(
            self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.preview.setPixmap(pixmap)
        self.status.setText(f"状态：监控中 | 画面：{w} × {h}")

    def capture_once(self):
        try:
            self.show_frame(self.client.screenshot())
        except Exception as exc:
            QMessageBox.warning(self, "截图失败", str(exc))

    def start_monitor(self):
        if not self.client.serial:
            QMessageBox.warning(self, "尚未连接", "请先连接模拟器。")
            return
        if self.worker and self.worker.isRunning():
            return
        self.worker = CaptureWorker(
            self.client, int(self.config.get("capture_interval_ms", 500))
        )
        self.worker.frame_ready.connect(self.show_frame)
        self.worker.error.connect(self.on_worker_error)
        self.worker.start()
        self.status.setText("状态：正在启动实时监控")

    def pause_monitor(self):
        if self.worker and self.worker.isRunning():
            self.worker.set_paused(True)
            self.status.setText("状态：监控已暂停")

    def stop_monitor(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait(2500)
            self.worker = None
        self.status.setText("状态：监控已停止")

    def on_worker_error(self, message: str):
        logging.error("监控错误：%s", message)
        self.status.setText("状态：截图失败，请检查设备连接")

    def save_frame(self):
        if self.last_frame is None:
            QMessageBox.information(self, "没有截图", "请先截图或开始监控。")
            return
        folder = Path(self.config.get("screenshot_dir", "data/screenshots"))
        folder.mkdir(parents=True, exist_ok=True)
        name = datetime.now().strftime("screen_%Y%m%d_%H%M%S.png")
        path = folder / name
        if cv2.imwrite(str(path), self.last_frame):
            QMessageBox.information(self, "保存成功", str(path.resolve()))
        else:
            QMessageBox.warning(self, "保存失败", "无法写入截图文件。")

    def manual_tap(self):
        if not self.manual_enable.isChecked():
            return
        if self.last_frame is None:
            QMessageBox.warning(self, "没有画面", "请先获取截图。")
            return
        h, w = self.last_frame.shape[:2]
        x, y = self.x_input.value(), self.y_input.value()
        try:
            self.client.tap(x, y, w, h)
            logging.info("手动测试点击：(%s, %s)", x, y)
        except AdbError as exc:
            QMessageBox.warning(self, "点击失败", str(exc))

    def closeEvent(self, event):
        self.stop_monitor()
        event.accept()
