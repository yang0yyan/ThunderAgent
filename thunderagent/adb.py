from __future__ import annotations

import logging
import subprocess
from typing import Optional

import cv2
import numpy as np


class AdbError(RuntimeError):
    pass


class AdbClient:
    def __init__(self, adb_path: str = "adb", serial: str = "", ports=None):
        self.adb_path = adb_path
        self.serial = serial.strip()
        self.ports = ports or [16384, 16416, 16448, 16480, 16512, 16544, 16576]

    def _run(self, args: list[str], timeout: int = 12) -> subprocess.CompletedProcess:
        cmd = [self.adb_path]
        if self.serial:
            cmd += ["-s", self.serial]
        cmd += args
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=False, timeout=timeout, check=False
            )
        except FileNotFoundError as exc:
            raise AdbError(
                "找不到 adb。请安装 Android Platform Tools，或在 config.yaml 填写 adb_path。"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise AdbError(f"ADB 命令超时：{' '.join(cmd)}") from exc
        if result.returncode != 0:
            err = result.stderr.decode("utf-8", errors="replace").strip()
            raise AdbError(err or f"ADB 命令失败：{' '.join(cmd)}")
        return result

    def connect(self) -> str:
        if not self.serial:
            # MuMu 版本和实例不同，端口并非固定；尝试常见端口后再枚举设备。
            for port in self.ports:
                candidate = f"127.0.0.1:{port}"
                try:
                    subprocess.run(
                        [self.adb_path, "connect", candidate],
                        capture_output=True, text=True, timeout=5, check=False
                    )
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    pass
            devices = subprocess.run(
                [self.adb_path, "devices"], capture_output=True, text=True,
                timeout=8, check=False
            )
            if devices.returncode != 0:
                raise AdbError("无法运行 adb devices。请检查 adb_path。")
            available = []
            for line in devices.stdout.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "device":
                    available.append(parts[0])
            # Prefer MuMu localhost TCP devices; if only one device exists, use it.
            mumu = [d for d in available if d.startswith("127.0.0.1:")]
            if len(mumu) == 1:
                self.serial = mumu[0]
            elif len(available) == 1:
                self.serial = available[0]
            elif len(available) > 1:
                raise AdbError(
                    "检测到多个设备：" + ", ".join(available) +
                    "。请在 config.yaml 的 device_serial 中指定设备。"
                )
            else:
                raise AdbError(
                    "没有发现在线设备。请启动 MuMu、开启 ADB 调试，并确认端口。"
                )
        state = self._run(["get-state"]).stdout.decode().strip()
        if state != "device":
            raise AdbError(f"设备状态不是 device：{state}")
        logging.info("ADB 已连接：%s", self.serial)
        return self.serial

    def devices(self) -> str:
        result = subprocess.run(
            [self.adb_path, "devices", "-l"],
            capture_output=True, text=True, timeout=8, check=False
        )
        if result.returncode != 0:
            raise AdbError(result.stderr.strip() or "adb devices 执行失败")
        return result.stdout.strip()

    def screenshot(self) -> np.ndarray:
        raw = self._run(["exec-out", "screencap", "-p"], timeout=15).stdout
        image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise AdbError("截图解码失败。请检查设备连接和 ADB 版本。")
        return image

    def tap(self, x: int, y: int, width: int, height: int) -> None:
        if not (0 <= x < width and 0 <= y < height):
            raise AdbError(f"坐标超出画面范围：({x}, {y}) / {width}x{height}")
        self._run(["shell", "input", "tap", str(x), str(y)])

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int,
              width: int, height: int) -> None:
        for x, y in ((x1, y1), (x2, y2)):
            if not (0 <= x < width and 0 <= y < height):
                raise AdbError("滑动坐标超出画面范围")
        self._run([
            "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2),
            str(max(1, duration_ms))
        ])

    def screen_size(self) -> Optional[str]:
        try:
            return self._run(["shell", "wm", "size"]).stdout.decode(
                "utf-8", errors="replace"
            ).strip()
        except AdbError:
            return None
